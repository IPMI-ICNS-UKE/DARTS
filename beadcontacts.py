import pandas as pd
import os

#%%
def list_files(directory, extension):
    filenames = []
    for filename in os.listdir(directory):
        if filename.endswith(extension):
            filenames.append(os.path.splitext(filename)[0])
    return filenames

#%%
ko_file = "/Users/lwoelk/ICNScloud/PythonPipeline_Testfiles/Bead Kontakte/161209_HN1L-KO.xlsx"
wt_file = "/Users/lwoelk/ICNScloud/PythonPipeline_Testfiles/Bead Kontakte/161209_WT.xlsx"
KO_excel = pd.read_excel(ko_file, header=3)
WT_excel = pd.read_excel(wt_file, header=3)

#%%

ko_data_path = "/Users/lwoelk/ICNScloud/PythonPipeline_Testfiles/HN1L/K2 OKT3"
wt_data_path = "/Users/lwoelk/ICNScloud/PythonPipeline_Testfiles/HN1L/WT OKT3"

ko_files = list_files(ko_data_path, '.tif')
wt_files = list_files(wt_data_path, '.tif')


#%%
KO_excel['fname'] = KO_excel['Name'].str.split('_', n=1).str[0]
KO_excel['fname'] = KO_excel['fname'].str.split('-', n=1).str[0]
WT_excel['fname'] = WT_excel['Name'].str.split('_', n=1).str[0]
WT_excel['fname'] = WT_excel['fname'].str.split('-', n=1).str[0]

#%%
KO_info = KO_excel[KO_excel['fname'].isin(ko_files)]
WT_info = WT_excel[WT_excel['fname'].isin(wt_files)]

#%%
aggregated_KO = KO_info.groupby('fname').agg({'von': ['min', 'max']})
aggregated_KO.columns = ['_'.join(col).strip() for col in aggregated_KO.columns.values]
aggregated_KO = aggregated_KO.reset_index()
aggregated_KO['end'] = aggregated_KO['von_max']+600

aggregated_WT = WT_info.groupby('fname').agg({'von': ['min', 'max']})
aggregated_WT.columns = ['_'.join(col).strip() for col in aggregated_WT.columns.values]
aggregated_WT = aggregated_WT.reset_index()
aggregated_WT['end'] = aggregated_WT['von_max']+600

aggregated_KO.to_csv('bead_contact_times_KO.csv', index=False)
aggregated_WT.to_csv('bead_contact_times_WT.csv', index=False)
