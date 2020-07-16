#!/bin/python
#Alexandru Hanganu, 2020 06 13


import time
date = str(time.strftime('%Y%m%d', time.localtime()))


#Names of the final files with statistical data:
file_with_all_sheets = 'data_FreeSurfer_'+date+'.xlsx'
file_with_only_subcortical_volumes = 'data_FreeSurfer_subcortical_volumes_'+date+'.xlsx'
file_with_all_data_one_sheet = 'data_FreeSurfer_one_sheet_'+date+'.xlsx'



from os import path, listdir
try:
        import pandas as pd
except ImportError:
        print('Install pandas module. Type in the terminal: pip3 install pandas')
try:
        import numpy as np
except ImportError:
        print('Install numpy module. Type in the terminal: pip3 install numpy')
try:
        import xlsxwriter, xlrd
except ImportError:
        print('Install xlsxwriter and xlrd modules (pip3 install xlsxwriter, xlrd)')


