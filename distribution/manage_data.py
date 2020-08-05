"""
processed data is stored as zip archived
script extracts of specific folders
"""

from os import path, makedirs, listdir
import zipfile


def read_zip(path2file, file):
        return zipfile.ZipFile(path.join(path2file,file), 'r')


def zip_file_content(zip_f):
        return zip_f.namelist()


def xtrct_dirs(zip_f, _ls_content, path_2_extract, pattern=""):
    for val in _ls_content:
        if pattern in val:
            try:
                zip_f.extract(val, path=path_2_extract)
            except Exception as e:     
                print(e)                                                                     
                pass                                                                 

def extract_archive(src_dir, folders_2_extract, path_2_extract):
    archive_type = '.zip'
    for zip in listdir(src_dir):
        print("extracting: "+ zip)
        zip_file = read_zip(src_dir, zip)
        for folder in [path.join(zip.strip(archive_type), i) for i in folders_2_extract]:
            xtrct_dirs(zip_file,
                       zip_file_content(zip_file),
                       path_2_extract,
                       pattern = folder)
