"""
if processed data is stored as zip archived
script extracts of specific folders
"""
archives_supported = ('.zip', '.gz', '.tar.gz')

import os
import zipfile
import shutil


def is_archive(file):
    archived = False
    archive_type = 'none'
    for ending in archives_supported:
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
                files2xtrct = list(),
                log=True):
        self.zip_f_path = zip_file_path
        self.zip_file   = os.path.split(self.zip_f_path)[-1]
        self.path2xtrct = path2xtrct
        self.dirs2xtrct = dirs2xtrct
        self.files2xtrct= files2xtrct
        self.path_err   = path_err
        self.log        = log
        if self.chk_if_zipfile():
            self.zip_file_open = self.read_zip()
            if self.path2xtrct:
                self.extract_archive()
            else:
                print(f'{" " * 12}reading: {self.zip_f_path}')
                print(f'{" " * 15}extraction is not requested. returning only content')
                self.zip_file_content()


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
        """
        sometimes the patterns has a WIN-OS os.sep
        it has to be changed to UNIX version
        sometimes the os.sep is missing and has to be added
        script also extracts only the files that correspond to the requested pattern
        """
        # add os.sep
        ls_patterns = [i.replace(os.sep,'/') for i in self.dirs2xtrct]
        for pattern in ls_patterns[::-1]:
            if "/" not in pattern:
                ix_pattern = ls_patterns.index(pattern)
                ls_patterns[ix_pattern] = f"/{pattern}/"
        if self.files2xtrct:
            for i in self.files2xtrct:
                ls_patterns.append(i)


        # search for the corresponding patterns in the whole content
        content_paths = list()
        for content in self.zip_file_content():
            for pattern in ls_patterns:
                if pattern in content:
                    content_paths.append(content)
        if content_paths:
            print(f'{" " * 16}extracting patterns: {self.dirs2xtrct}')
            self.extract_patterns(content_paths)
        else:
            print(f'{" " * 16}ERR: patterns are missing from archive: {self.dirs2xtrct}')

    def extract_patterns(self, content_paths):
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
        if self.dirs2xtrct or self.files2xtrct:
                self.pattern_exists()
        else:
            self.xtrct_all()


    def move_error(self):
        shutil.move(self.zip_f_path, self.path_err)
        shutil.move(os.path.join(self.path_err, self.zip_file), os.path.join(self.path_err, 'errzip_'+self.zip_file))
