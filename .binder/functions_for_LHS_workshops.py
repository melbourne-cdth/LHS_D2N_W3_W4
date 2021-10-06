import pandas as pd 
import ipywidgets as widgets
import qgrid
import sweetviz as sv
from ipywidgets import interact, interact_manual

patients_df = pd.read_csv('patients.csv', sep=',')
diagnosis_df = pd.read_csv('diagnosis.csv', sep=',')
encounters_df = pd.read_csv('encounters.csv', sep=',')
medication_df = pd.read_csv('medication.csv', sep=',')

def dataframe_2_qgrid(x):

    col_opts = {'editable': False}

    grid_options={'forceFitColumns': False, 
              'defaultColumnWidth': 220,'highlightSelectedCell': True }

    if x=='patients':
        df = patients_df
        column_definitions={ 'index': { 'maxWidth': 0, 'minWidth': 0, 'width': 0 }, 
                            'STUDYID': { 'toolTip': "Patient identifier"} ,
                            'INDEX_YEAR': { 'toolTip': "Year of Diabetes Diagnosis"} , 
                            'INDEX_AGE': {'toolTip': "Age at Diagnosis"},
                            'GENDER': {'_tablestoolTip': "Gender"} , 
                            'RACE': {'toolTip': "Race"} , 
                            'T2D_STATUS': {'toolTip': "Describes how the patient was identified as a T2D patient.\n 1. ICD diagnosis alone\n 2. HbA1C alone\n 3. Meds alone\n 4. Combination of any of the above."},
                            'COMBINATION': {'toolTip': " of any of the above."} , 
                            'CARDIOVASCULAR': {'toolTip': "Cardiovascular disease status: Yes/No"} , 
                            'NEPHROPATHY': {'toolTip': "Nephropathy status: Yes/No"} , 
                            'LIVER': {'toolTip': "Liver disease status: Yes/No"} , 
                            'ENC_12M_BF': {'toolTip': "Encounters in 12 month period before index event"} , 
                            'ENC_12M_AF': {'toolTip': "Encounters in 12 month period after index event"} , 
                            'ENC_YRS_BF': {'toolTip': "Number of years of encounter data before the index event"} , 
                            'ENC_YRS_AF': {'toolTip': "Number of years of encounter data after the index event"} , 
                            'BIOBANK': {'toolTip': "Availability of biobank data for patient: Yes/No"} , 
                                   }
    elif x=='medication':
        df = medication_df            
        column_definitions={ 'index': { 'maxWidth': 0, 'minWidth': 0, 'width': 0 }, 
                            'STUDYID': { 'toolTip': "Patient identifier"} ,
                            'DRUG_NAME': { 'toolTip': "Name of the drug"} , 
                            'STRENGTH': {'toolTip': "Strength (e.g. 20mg, 500 mg etc)"},     
                            'NUMBER_OF_DAYS_SUPPLY': {'toolTip': "Total number of days supplied"},
                            'DAYS_MED_INDEX': {'toolTip': "Day medication was prescribed in terms of days from/to the index event a given medication was prescribed"},
                            'NDC_CODE': {'toolTip': "11-digit national drug code"},
                            'DISPENSE_AMOUNT': {'toolTip': "Number of pills/units dispensed"}
                        
                                    }
    elif x=='encounters':
        df = encounters_df            
        column_definitions={ 'index': { 'maxWidth': 0, 'minWidth': 0, 'width': 0 }, 
                            'STUDYID': { 'toolTip': "Patient identifier"} ,
                            'DAYS_ENC_INDEX': { 'toolTip': "Encounter day in terms of days from/to index event"} ,
                            'CARE_SETTING_NAME': { 'toolTip': "Care setting\n(e.g. Outpatient, Inpatient etc.)"} ,
                            'LOCATION_POINT_OF_CARE': { 'toolTip': "Actual location\n( e.g. X hospital, Y Pharmacy etc.)"} ,
                                           }
        
    elif x=='diagnosis':
        df = diagnosis_df            
        column_definitions={ 'index': { 'maxWidth': 0, 'minWidth': 0, 'width': 0 }, 
                            'STUDYID': { 'toolTip': "Patient identifier"} ,
                            'DAYS_DX_INDEX': { 'toolTip': "Number of days from/to index event"} ,
                            'DX_CODE': { 'toolTip': "ICD9 diagnosis code"} ,
                                           }
        
    gri=qgrid.show_grid(df,column_options=col_opts, grid_options=grid_options, column_definitions=column_definitions)
    return gri


def df_2_visualized_EDA(x):
    if x=='patients':
        df = patients_df
    elif x=='medication':
        df = medication_df 
    elif x=='encounters':
        df = encounters_df 
    elif x=='diagnosis':
        df = diagnosis_df
    analysis = sv.analyze(df)  
    #analysis.show_html('mtcars.html')
    return analysis.show_notebook()
    
def cohort_creation():
    # Filtering table 'Encounters' by type of care setting name and time offset between hospitalisation and a day
    # when a patient was diagnosed with diabetes:
    encounters_inp_df=encounters_df[(encounters_df['CARE_SETTING_NAME'].str.contains('INPATIENT')) & (encounters_df['DAYS_ENC_INDEX']>0)]
    
    # Filtering table 'Diagnosis' by ICD-9 code (250.00) and time offset between a day when a patient was diagnosed 
    # with diabetes and a date when diagnosis diabetes was mentioned for the second time:
    diagnosis_diab_df=diagnosis_df[diagnosis_df['DX_CODE'].str.contains('250\.0') & (diagnosis_df['DAYS_DX_INDEX']>0)]
    
    # Joining filtered 'Encounters' and 'Diagnosis' tables:
    inp_diab = pd.merge(encounters_inp_df, diagnosis_diab_df, on='STUDYID', how='inner')

    # Add additional condition that the time between admission and diabetes diagnosis should be less than 30 days:
    #inp_diab=inp_diab[(inp_diab['DAYS_DX_INDEX'] <= (inp_diab['DAYS_ENC_INDEX']+30)) & (inp_diab['DAYS_DX_INDEX']>=inp_diab['DAYS_ENC_INDEX'])]
    inp_diab=inp_diab[(inp_diab['DAYS_DX_INDEX'] == inp_diab['DAYS_ENC_INDEX']) & (inp_diab['DAYS_DX_INDEX']>=inp_diab['DAYS_ENC_INDEX'])]

    # Selection of unique records only:
    inp_diab=inp_diab[['STUDYID','CARE_SETTING_NAME']].drop_duplicates()
    
    # Creation of binary features: 
    # MED_PRESCR - identifies if data about medication is available
    # METFORMIN_HYDROCHLORIDE - identifies a fact that a patient was prescribed with Metformin Hydrochloride
    # INSULIN_GLARGINE - binary feature, identifies a fact that a patient was prescribed with Insulin Glargine
    medication_df['MED_PRESCR']=medication_df['NDC_CODE'].apply(lambda x: 1 if x is not None else 0)
    medication_df['METFORMIN_HYDROCHLORIDE']=medication_df['NDC_CODE'].apply(lambda x: 1 if x in (68382002810,68382003010,93726701) else 0)
    medication_df['INSULIN_GLARGINE']=medication_df['NDC_CODE'].apply(lambda x: 1 if x  in(88222033, 88221905) else 0)

    # creation of pivoted table with information about mediction for each patient
    medication_per_pat = medication_df.groupby(['STUDYID'], as_index=False).agg(MED_PRESCR = ('MED_PRESCR', pd.Series.max), COUNT_NDC_CODES=('NDC_CODE', pd.Series.count), UNIQUE_NDC_CODES=('NDC_CODE', pd.Series.nunique)
                                                                         , METFORMIN_HYDROCHLORIDE =('METFORMIN_HYDROCHLORIDE', pd.Series.max),  INSULIN_GLARGINE =('INSULIN_GLARGINE', pd.Series.max))
    #Joining 'Patients' table abd the table obtained on the previous step:
    cohort = pd.merge(patients_df, inp_diab, on='STUDYID', how='left')
    #Joining 'Medication' table abd the table obtained on the previous step:
    cohort = pd.merge(cohort, medication_per_pat, on='STUDYID', how='left')
    #Changing name of the column from 'CARE_SETTING_NAME' to 'LABEL':
    cohort.rename(columns={'CARE_SETTING_NAME':'LABEL'}, inplace=True)

    #For all rows containing 'INPATIENT' value, set value in 'lABEL' column to 1:
    cohort.loc[(cohort['LABEL'] == 'INPATIENT') , 'LABEL'] = 1

    #For other patients set label to 0:
    cohort['LABEL'].fillna(0, inplace=True)
    cohort['MED_PRESCR'].fillna(0, inplace=True)
    #Removing irrelevant or label-related columns:
    cohort.drop(columns=['STUDYID','ENC_12M_AF', 'ENC_YRS_BF', 'ENC_YRS_AF', 'BIOBANK'], inplace=True)

    #Show number of rows and columns in the final cohort:
    cohort.shape
    print("Obtained dataset has {} rows and {} columns.".format(cohort.shape[0], cohort.shape[1]))
    return cohort
    
    
def cohort_2_qgrid(x):
    col_opts = {'editable': False}

    grid_options={'forceFitColumns': False, 
              'defaultColumnWidth': 220,'highlightSelectedCell': True }

    df = x #cohort_creation()
    column_definitions={ 'index': { 'maxWidth': 0, 'minWidth': 0, 'width': 0 }, 
                        'STUDYID': { 'toolTip': "Patient identifier"} ,
                        'INDEX_YEAR': { 'toolTip': "Year of Diabetes Diagnosis"} , 
                        'INDEX_AGE': {'toolTip': "Age at Diagnosis"},
                        'GENDER': {'toolTip': "Gender"} , 
                        'RACE': {'toolTip': "Race"} , 
                        'T2D_STATUS': {'toolTip': "Describes how the patient was identified as a T2D patient.\n 1. ICD diagnosis alone\n 2. HbA1C alone\n 3. Meds alone\n 4. Combination of any of the above."},
                        'COMBINATION': {'toolTip': " of any of the above."} , 
                        'CARDIOVASCULAR': {'toolTip': "Cardiovascular disease status: Yes/No"} , 
                        'NEPHROPATHY': {'toolTip': "Nephropathy status: Yes/No"} , 
                        'LIVER': {'toolTip': "Liver disease status: Yes/No"} , 
                        'ENC_12M_BF': {'toolTip': "Encounters in 12 month period before index event"} , 
                        'LABEL': {'toolTip': "Label. \n 1 - patient has information about admission to hospital due to diabetes.\n 0 - patient was not admitted to a hospital. "} , 
                        'MED_PRESCR': {'toolTip': "Identifies if data about medication is available"} , 
                        'COUNT_NDC_CODES': {'toolTip': "Total number of prescribed medication types based on NDC code"} , 
                        'UNOQ_NDC_CODES': {'toolTip': "Number of unique prescribed medication types based on NDC code"} , 
                        'METFORMIN_HYDROCHLORIDE': {'toolTip': "Identifies a fact that a patient was prescribed with Metformin Hydrochloride"} , 
                        'INSULIN_GLARGINE': {'toolTip': "Identifies a fact that a patient was prescribed with Insulin Glargine."} , 
                        
                               }
   
        
    gri=qgrid.show_grid(df,column_options=col_opts, grid_options=grid_options, column_definitions=column_definitions)
    return gri