from os import listdir
from os.path import isfile, join
from typing import TextIO, Tuple


class Log:
    def __init__(self, raw_data: str):
        self.raw = raw_data


class LogFile:
    def __init__(self, file_attributes: Tuple[str, str], log_file: TextIO):
        self.name = file_attributes[0]
        self.suffix = file_attributes[1]
        self.log_file = log_file

    def to_dict(self):
        return {'Test': 'Test'}


class LogFolder:
    def __init__(self, directory_path: str, log_file_suffix: str):
        self._path = directory_path
        self._log_file_suffix = log_file_suffix
        self._files = []
        self.logs = {}
        self._find_available_files()
        self._open_then_create_log_file()

    def __repr__(self):
        return f'<LogFolder Path: "{self._path}" Suffix: "{self._log_file_suffix}" >'

    def _find_available_files(self):
        """
        Find all files in the provided directory with the provided suffix.
        """
        for file in listdir(self._path):
            if isfile(join(self._path, file)):
                if self._log_file_suffix in file:
                    self._files.append(file)

    def _open_then_create_log_file(self):
        """
        Opens each file in the _files list and creates a log file
        :return:
        """
        for file in self._files:
            with open(join(self._path, file), 'r') as log_file:
                self._create_log_files(file_name=file, log_file=log_file)

    def _create_log_files(self, file_name: str, log_file: TextIO):
        file_attributes = (file_name[:file_name.index(self._log_file_suffix)],
                           file_name[file_name.index(self._log_file_suffix):])
        self.logs |= LogFile(file_attributes=file_attributes, log_file=log_file).to_dict()



folder = LogFolder(r'C:\Users\e261712\Desktop\1383001', 'rec')
print(folder)
print(folder.logs)


# Every log folder has a log file
# Every log file has a log
# every log has a raw data line
