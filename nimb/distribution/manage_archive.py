"""
This module handles the archiving and extraction of processed data using zip files.
It is intended for managing storage and distribution of processed subjects.
"""

import os
import zipfile
import shutil
import logging

log = logging.getLogger(__name__)

archives_supported = ('.zip', '.gz', '.tar.gz')


def is_archive(file):
    """
    Checks if a given file has a supported archive extension.
    """
    archived = False
    archive_type = 'none'
    for ending in archives_supported:
        if file.endswith(ending):
            archived = True
            archive_type = ending
            break
    return archived, archive_type


class ZipArchiveManagement:
    """
    A class to manage the extraction of specific folders or files from a zip archive.
    """

    def __init__(self, zip_file_path, path2xtrct=None, dirs2xtrct=None, files2xtrct=None):
        self.zip_f_path = zip_file_path
        self.path2xtrct = path2xtrct
        self.dirs2xtrct = dirs2xtrct or []
        self.files2xtrct = files2xtrct or []
        self.zip_file_open = None

        if not zipfile.is_zipfile(self.zip_f_path):
            log.error(f"File is not a valid zip archive: {self.zip_f_path}")
            return

        if self.path2xtrct:
            self.extract_archive()
        else:
            log.info(f"Reading archive content without extraction: {self.zip_f_path}")

    def __enter__(self):
        """Context manager entry."""
        self.zip_file_open = zipfile.ZipFile(self.zip_f_path, 'r')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.zip_file_open:
            self.zip_file_open.close()

    def get_content_list(self):
        """Returns a list of all file paths within the zip archive."""
        if not self.zip_file_open:
            with zipfile.ZipFile(self.zip_f_path, 'r') as zf:
                return zf.namelist()
        return self.zip_file_open.namelist()

    def extract_archive(self):
        """Initiates the archive extraction process."""
        log.info(f"Extracting file: {self.zip_f_path} to folder: {self.path2xtrct}")
        
        with self as archive:
            if self.dirs2xtrct or self.files2xtrct:
                self._extract_patterns(archive)
            else:
                archive.zip_file_open.extractall(self.path2xtrct)
        log.info("Extraction complete.")

    def _extract_patterns(self, archive):
        """Finds and extracts specific folders or files based on defined patterns."""
        ls_patterns = self.dirs2xtrct[:]
        # Ensure directory patterns match correctly
        for i, pattern in enumerate(ls_patterns):
            ls_patterns[i] = pattern.strip('/') + '/'
        
        ls_patterns.extend(self.files2xtrct)
        
        content_paths_to_extract = []
        for content in archive.get_content_list():
            for pattern in ls_patterns:
                if pattern in content:
                    content_paths_to_extract.append(content)

        if content_paths_to_extract:
            log.info(f"Extracting patterns: {self.dirs2xtrct} & {self.files2xtrct}")
            for content_path in set(content_paths_to_extract): # Use set to avoid duplicates
                try:
                    archive.zip_file_open.extract(content_path, path=self.path2xtrct)
                except Exception as e:
                    log.error(f"Error during extraction of {content_path}: {e}")
        else:
            log.warning(f"Patterns not found in the archive: {ls_patterns}")
