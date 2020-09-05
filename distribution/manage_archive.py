"""
if processed data is stored as zip archived
script extracts of specific folders
"""

from os import path, makedirs, listdir
import zipfile
import shutil

class ZipArchiveManagement():

    def __init__(self, zip_file, path2xtrct, path_err, dirs2xtrct = list()):
        self.zip_file   = zip_file
        self.path2xtrct = path2xtrct
        self.dirs2xtrct = dirs2xtrct
        self.path_err   = path_err
        if self.chk_if_zipfile():
            self.extract_archive()

    def chk_if_zipfile(self):
        if not zipfile.is_zipfile(self.zip_file):
            print(self.zip_file,' not a zip file')
            self.move_error()
            return False
        else:
            return True

    def read_zip(self):
        return zipfile.ZipFile(self.zip_file, 'r')

    def zip_file_content(self, zip_f):
        return zip_f.namelist()

    def xtrct_all(self, zip_f):
        try:
            zip_f.extractall(self.path2xtrct)
        except Exception as e:
            print(e)

    def xtrct_dirs(self, zip_f, _ls_content, pattern):
        for val in _ls_content:
            if pattern in val:
                try:
                    zip_f.extract(val, path=self.path2xtrct)
                except Exception as e:
                    print(e)
                    pass

    def extract_archive(self):
        print("extracting: {} to {}".format(self.zip_file, self.path2xtrct))
        zip_file_open = self.read_zip()
        if self.dirs2xtrct:
            for folder in [path.join(self.zip_file.strip('.zip'), i) for i in self.dirs2xtrct]:
                self.xtrct_dirs(zip_file_open,
                            self.zip_file_content(zip_file_open),
                            self.path2xtrct,
                            pattern = folder)
        else:
            self.xtrct_all(zip_file_open)

    def move_error(self):
        shutil.move(self.zip_file, self.path_err)
        shutil.rename(path.join(self.path_err, self.zip_file), path.join(self.path_err, 'errzip_'+self.zip_file))
