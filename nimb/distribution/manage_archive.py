"""
if processed data is stored as zip archived
script extracts of specific folders
"""
archive_types = ('.zip', '.gz', '.tar.gz')

import os
import zipfile
import shutil


def is_archive(file):
    archived = False
    archive_type = 'none'
    for ending in archive_types:
        if file.endswith(ending):
            archived = True
            archive_type = ending
            break
    return archived, archive_type



class ZipArchiveManagement():

    def __init__(self,
                zip_file_path,
                path2xtrct = False,
                path_err = False,
                dirs2xtrct = list(),
                log=True):
        self.zip_f_path = zip_file_path
        self.zip_file   = os.path.split(self.zip_f_path)[-1]
        self.path2xtrct = path2xtrct
        self.dirs2xtrct = dirs2xtrct
        self.path_err   = path_err
        self.log        = log
        if self.chk_if_zipfile():
            self.zip_file_open = self.read_zip()
            if self.path2xtrct:
                self.extract_archive()
            else:
                self.content = self.zip_file_content()


    def chk_if_zipfile(self):
        if not zipfile.is_zipfile(self.zip_f_path):
            print(f'{" " * 12}{self.zip_f_path} not a zip file')
            if self.path_err:
                self.move_error()
            return False
        else:
            return True


    def read_zip(self):
        return zipfile.ZipFile(self.zip_f_path, 'r')


    def zip_file_content(self):
        return self.zip_file_open.namelist()


    def xtrct_all(self):
        print(f'{" " * 12}extracting all content')
        extracted = False
        try:
            self.zip_file_open.extractall(self.path2xtrct)
            extracted = False
        except Exception as e:
            print(f'{" " * 16}{e}')
        if not extracted:
            try:
                print(f'{" " * 12}trying to use system unzip:')
                os.system(f'unzip -o {self.zip_f_path} -d {self.path2xtrct}')
            except Exception as e:
                print(f'{" " * 16}{e}')


    def pattern_exists(self):
        ls_patterns = [os.path.join(self.zip_file.replace('.zip',''), i).replace(os.sep,'/') for i in self.dirs2xtrct]
        content_paths = list()
        for abs_path in self.zip_file_content():
            for pattern in ls_patterns:
                if pattern in abs_path:
                    content_paths.append(abs_path)
        if content_paths:
            print(f'{" " * 12}extracting patterns: {self.dirs2xtrct}')
            self.extract_pattern(content_paths)

    def extract_pattern(self, content_paths):
        for content_path in content_paths:
            try:
                self.zip_file_open.extract(content_path, path=self.path2xtrct)
            except Exception as e:
                print(f'{" " * 16}{e}')
                pass


    def extract_archive(self):
        if self.log:
            print(f'{" " * 12}extracting: file {self.zip_f_path}')
            print(f'{" " * 16}to folder {self.path2xtrct}')
        if self.dirs2xtrct:
                self.pattern_exists()
        else:
            self.xtrct_all()


    def move_error(self):
        shutil.move(self.zip_f_path, self.path_err)
        shutil.move(os.path.join(self.path_err, self.zip_file), os.path.join(self.path_err, 'errzip_'+self.zip_file))
