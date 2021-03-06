import csv
import sys
import threading
import tkinter as tk
import gzip
import os
import ipaddress
import shutil
import enum
from tkinter import ttk
from tkinter import filedialog, messagebox
from dataclasses import dataclass
from datetime import datetime
from os import listdir
from os.path import isfile, join
from typing import TextIO, Tuple, List
from urllib import parse

# Colours
BACKGROUND = '#121212'
BACKGROUND_2 = '#242424'
BACKGROUND_3 = '#363636'
BACKGROUND_4 = '#484848'
FOREGROUND = '#7b7b7b'
HIGHLIGHT = '#8bc6fe'
HIGHLIGHT_TEXT = '#000'
HIGHLIGHT_2 = '#65a2db'
HIGHLIGHT_TEXT_2 = '#000'
BORDERS = '#008ffd'
ERROR = '#eb6773'
ERROR_TEXT = '#000'
WHITE_TEXT = '#fff'

# HL7 Message Definitions

HL7_MESSAGE = {
    'I': {
        'ADT': {
            'A01': 'Admission',
            'A02': 'Transfer',
            'A03': 'Discharge',
            'A05': 'Pre-admission',
            'A08': 'Visit Update',
            'A11': 'Cancel Admission',
            'A12': 'Cancel Transfer',
            'A13': 'Cancel I/P Discharge',
            'A14': 'Pre-admission',
            'A21': 'On-Leave',
            'A22': 'Return from leave',
            'A27': 'Cancel Pre-admission',
            'A28': 'PMI Registration',
            'A31': 'PMI Update',
            'A34': 'PMI Merge',
            'A44': 'Change U/R for O/P visit',
        },
        'SIU': {
            'S12': 'Notification of New Appointment',
            'S14': 'Notification of Appointment Modification',
            'S15': 'Notification of Appointment Cancellation',
        }
    },
    'E': {
        'ADT': {
            'A03': 'Discharge Emergency Visit',
            'A04': 'Register Emergency Visit',
            'A08': 'Emergency Visit Update',
            'A11': 'Cancel Emergency Visit',
            'A13': 'Cancel Emergency Visit Discharge',
            'A44': 'Change U/R for Emergency Visit',
        }
    },
    'O': {
        'ADT': {
            'A03': 'Discharge',
            'A04': 'Register Event (Attendance)',
            'A05': 'Pre-admit a Patient (Booking)',
            'A08': 'Update Patient Information (Update Booking/Reschedule)',
            'A11': 'Cancel Visit (Unattend)',
            'A13': 'Cancel Discharge',
            'A38': 'Cancel Pre-admit (Booking)',
            'A44': 'Change U/R for O/P visit',
            'A31': 'PMI Update',
        }
    },

}
HL7_MESSAGE['S'] = HL7_MESSAGE['I']


# Log Classes


class Log:
    """
    Base log class to hold common functionality across logfiles
    """

    def __init__(self, raw_data: str):
        self.raw = raw_data
        self._parse()

    def _parse(self):
        pass

    def header(self):
        pass

    def values(self):
        pass


class HL7Log(Log):
    """
    Log class that has common HL7 Attributes
    """

    def __init__(self, raw_data: str):
        """
        Converts the raw string data to the BRDLog object
        :param raw_data: str data to be converted to class object
        """
        super().__init__(raw_data)

    def _parse(self):
        self._parse_headers()
        self._build_msh()
        self._build_pid()
        self._build_pv1()
        self._set_type_descriptions()

    def _parse_headers(self):
        self.pid = ''
        if len(self.raw) != 0:
            self.msh = str(self.raw)[53:].split('|')[0:19]
            try:
                self.pid = str(self.raw)[str(self.raw).find('PID|'):].split('|')[:31]
            except IndexError:
                self.pid = ''
            try:
                self.pv1 = str(self.raw)[str(self.raw).find('PV1|'):].split('|')[:45]
            except IndexError:
                self.pv1 = ''

    def _build_msh(self):
        try:
            self.message_date_time = datetime.strptime(self.msh[6], '%Y%m%d%H%M%S')
            self.message_date = self.message_date_time.date()
            self.message_time = self.message_date_time.time()
            self.message_trans_type = self.msh[8].split('^')[0]
            self.message_type = self.msh[8].split('^')[1]
            self.message_id = int(self.msh[9])
        except AttributeError:
            pass
        except IndexError:
            pass

    def _build_pid(self):
        self.ur_number = ''
        self.first_name = ''
        self.middle_name = ''
        self.last_name = ''
        self.date_of_birth = None
        try:
            self.ur_number = self.pid[3].split('^')[0]
            self.first_name = self.pid[5].split('^')[1]
            self.middle_name = self.pid[5].split('^')[2].replace('"', '')
            self.last_name = self.pid[5].split('^')[0]
            self.date_of_birth = datetime.strptime(self.pid[7], '%Y%m%d').date()
        except IndexError:
            pass

    def _build_pv1(self):
        try:
            self.admission_type = self.pv1[2]
            self.ward = ''
            self.bed = ''
            self.visit_number = 0
            if self.admission_type.lower() == 'e':
                self.ward = 'Emergency'
                self.bed = self.pv1[10].split('^')[1]
            else:
                self.ward = self.pv1[3].split('^')[0]
                self.bed = self.pv1[3].split('^')[2]
                self.visit_number = int(self.pv1[5])
        except IndexError:
            self.ward = ''
            self.bed = ''
            self.visit_number = 0
            self.admission_type = ''

    def _set_type_descriptions(self):
        self.type_description = ''
        if self.admission_type != '':
            self.type_description = HL7_MESSAGE[self.admission_type][self.message_trans_type][self.message_type]

    def __repr__(self):
        return f'<{self.__class__.__name__} MsgID:{self.message_id} MsgType:{self.message_type} MRN:{self.ur_number}>'

    def header(self):
        return 'message_id', 'message_date_time', 'message_type', 'type_description', 'ur_number', 'first_name', \
               'middle_name', 'last_name', 'date_of_birth', 'visit_number', 'admission_type', 'ward', 'bed', 'raw'

    def values(self):
        if self.visit_number == 0:
            visit = ''
        else:
            visit = self.visit_number
        return self.message_id, self.message_date_time, self.message_type, self.type_description, \
               self.ur_number, self.first_name, self.middle_name, self.last_name, self.date_of_birth, \
               visit, self.admission_type, self.ward, self.bed, self.raw


class BRDLog(HL7Log):
    """
    Broadcaster Log class
    """
    pass


class RECLog(HL7Log):
    """
    Receiver Log class
    """

    def _build_msh(self):
        try:
            self.message_date_time = datetime.strptime(self.msh[5][:14], '%Y%m%d%H%M%S')
            self.message_date = self.message_date_time.date()
            self.message_time = self.message_date_time.time()
            self.message_trans_type = self.msh[7].split('^')[0]
            self.message_type = self.msh[7].split('^')[1]
            self.message_id = 0
            try:
                self.message_id = int(self.msh[8])
            except ValueError:
                self.message_id = self.msh[8]
        except AttributeError:
            pass
        except IndexError:
            pass

    def _build_pv1(self):
        try:
            self.admission_type = self.pv1[2]
            self.ward = ''
            self.bed = ''
            self.visit_number = 0
            if self.admission_type.lower() == 'e':
                self.ward = 'Emergency'
                self.bed = self.pv1[10].split('^')[1]
            elif self.admission_type.lower() == 'o':
                self.ward = self.pv1[3].split('^')[0]
                self.bed = ''
                self.visit_number = int(self.pv1[17].split('^')[0])
            elif self.admission_type.lower() == 'i':
                self.ward = self.pv1[3].split('^')[0]
                self.bed = self.pv1[3].split('^')[2]
                if self.pv1[1] == '':
                    self.visit_number = self.pv1[19].split(' ')[0]
                else:
                    self.visit_number = int(self.pv1[17].split('^')[0])
        except IndexError:
            self.ward = ''
            self.bed = ''
            self.visit_number = 0
            self.admission_type = ''
        except ValueError:
            self.visit_number = 0


class PASAccessLog(Log):
    """
    Webpas Web Server Access Log
    """

    def __new__(cls, raw_data: str, *args, **kwargs):
        if ipaddress.ip_address(raw_data.split(' ')[0]):
            return super(PASAccessLog, cls).__new__(cls)

    def __init__(self, raw_data: str):
        """
        Converts the raw string data to the PASAccessLog object
        :param raw_data: str data to be converted to class object
        """
        super().__init__(raw_data)
        self.log = self.raw.split(' ')
        self.ip_address = self.log[0]
        self.user = self.log[1]
        self.datetime = datetime.strptime(' '.join(self.log[2:4]), '%Y-%m-%d %H:%M:%S')
        self.date = self.datetime.date()
        self.time = self.datetime.time()
        self.method = self.log[4].strip('"')
        self.response_code = self.log[7]

        # Parsing visited URL
        self.url = self.log[5].split('?')[0]
        try:
            self.url_params = parse.parse_qs(self.log[5].split('?')[1])
        except IndexError:
            self.url_params = ''
        if '/cgi-bin/' in self.url:
            self.visited_server = self.url[-12:-4].upper()

        # Parse Visited Template Number
        self.visited_template = None
        try:
            self.visited_template = self.url_params['template'][0].zfill(3)
        except KeyError:
            pass
        except TypeError:
            pass

        # Parse Visited Report Number
        self.visited_report = None
        try:
            self.visited_report = self.url_params['reportno'][0].zfill(2)
        except KeyError:
            pass
        except TypeError:
            pass

        # Parsing referred URL
        self.referer_url = self.log[10].split('?')[0].strip('Referer=').replace('"', '')
        try:
            self.referer_params = parse.parse_qs(self.log[10].split('?')[1])
        except IndexError:
            self.referer_params = ''
        self.host = self.referer_url.strip('https://')[:self.referer_url.find('.sjog.org.au') - 8]
        if '/cgi-bin/' in self.referer_url:
            self.referred_server = self.referer_url[-12:-4].upper()

        # Parse Referred Template Number
        self.referred_template = None
        try:
            self.referred_template = self.referer_params['template'][0].zfill(3)
        except KeyError:
            pass
        except TypeError:
            pass

        # Parse Referred Report Number
        self.referred_report = None
        try:
            self.referred_report = self.referer_params['reportno'][0].zfill(2)
        except KeyError:
            pass
        except TypeError:
            pass

        # Parse UR Number
        self.ur_number = None
        try:
            self.ur_number = int(self.url_params['urnumber'][0])
        except KeyError:
            pass
        except TypeError:
            pass
        except ValueError:
            pass
        try:
            referer_ur = int(self.referer_params['urnumber'][0])
            if referer_ur != self.ur_number and self.ur_number is None:
                self.ur_number = referer_ur
        except KeyError:
            pass
        except TypeError:
            pass
        except ValueError:
            pass

        # Parse Visit number
        self.visit_number = None
        try:
            self.visit_number = int(self.url_params['admissno'][0])
        except KeyError:
            pass
        except TypeError:
            pass
        except ValueError:
            pass
        try:
            referer_visit = int(self.referer_params['admissno'][0])
            if referer_visit != self.visit_number and self.visit_number is None:
                self.visit_number = referer_visit
        except KeyError:
            pass
        except TypeError:
            pass
        except ValueError:
            pass

    def __repr__(self):
        return f'<PASAccessLog IP:{self.ip_address} UserID:{self.user} MRN:{self.ur_number}>'

    def header(self):
        return 'ip_address', 'user', 'datetime', 'method', 'response_code', 'host', 'ur_number', 'visit_number', \
               'visited_url', 'referred_url', 'raw '

    def values(self):
        return self.ip_address, self.user, self.datetime, self.method, self.response_code, self.host, self.ur_number, \
               self.visit_number, self.url, self.referer_url, self.raw


class LogType(enum.Enum):
    """
    Enum to call the correct log from the LogFile class.
    """
    BRDTRANSACTIONLOG = BRDLog
    RECTRANSACTIONLOG = RECLog
    PASACCESSLOG = PASAccessLog


class LogFile:
    """
    Base Log file, contains a list of Log's. This class holds common functionality across all log file types
    """

    def __init__(self, file_attributes: Tuple[str, str], log_file: TextIO):
        self.name = file_attributes[0]
        self.header = None
        self.suffix = file_attributes[1]
        self.log_type = self.suffix.upper()
        self.log_file = log_file
        self._raw_logs = []
        self._logs = []
        self._parse()
        self._create_log_files()
        self._get_header()

    def _get_header(self):
        """
        Sets the header name on the log file, based on the first row Log header field.
        Used for setting the headers in the Treeview
        """
        try:
            self.header = self._logs[0].header()
        except IndexError:
            # todo Why does this occur?
            print(self._logs)

    def _create_log_files(self):
        for log in self._raw_logs:
            try:
                self._logs.append(LogType[self.log_type].value(log))
            except ValueError:
                pass

    def to_dict(self):
        return {self.name: self._logs}

    def _parse(self):
        pass


class BRDLogFile(LogFile):
    """
    Webpas Broadcaster Log file, contains a list of BRDLog's.
    """

    def __init__(self, file_attributes: Tuple[str, str], log_file: TextIO):
        super().__init__(file_attributes, log_file)

    def _parse(self):
        header = []
        body = []
        data = []
        for idx, log in enumerate(self.log_file):
            try:
                if not log[:80] == (80 * '-'):
                    raise NameError
                if len(header) != 0:
                    data.append(' '.join(body))
                    header = []
                    body = []
                    if data[0]:
                        self._raw_logs.append(data[0])
                    data = []
                    header.append(log)
                else:
                    header.append(log[:80])
            except NameError:
                msg_body = str(log).strip()
                if 'Timeout waiting for incoming message' not in msg_body:
                    body.append(str(log).strip())


class RECLogFile(BRDLogFile):
    """
    Webpas Receiver Log file, contains a list of RECLog's.
    """

    def __init__(self, file_attributes: Tuple[str, str], log_file: TextIO):
        super().__init__(file_attributes, log_file)


class PASLogFile(LogFile):
    def __init__(self, file_attributes: Tuple[str, str], log_file: TextIO):
        super().__init__(file_attributes, log_file)

    def _parse(self):
        for log in self.log_file:
            self._raw_logs.append(log.strip('\n'))


class LogFileType(enum.Enum):
    """
    Enum to call the correct log file from the LogFolder class.
    """
    BRDTransactionLog = BRDLogFile
    RECTransactionLog = RECLogFile
    PASAccessLog = PASLogFile


class Suffix(enum.Enum):
    # todo rework this as cant have to txt suffixes
    PASAccessLog = 'txt'
    BRDTransactionLog = 'brd'
    RECTransactionLog = 'rec'


class LogFolder:
    """
    Folder level class that contains a list of log files, each logfile contains logs.
    """

    # todo if existing txt files in folder then it crashes ;(
    def __init__(self, directory_path: str, log_file_suffix: Suffix):
        """
        Takes the given directory path and checks it for the file suffix provided, then uses the search word list to
        filter the logs.
        :param directory_path: eg: "C:/Users/user/desktop"
        :param log_file_suffix: log file extension
        """
        self._path = directory_path
        self._log_file_suffix = log_file_suffix.value
        self._log_file_type = log_file_suffix.name
        self._files = []
        self._extracted_files = []
        self.logs = {}
        self.filtered_logs = {}
        self._progress_max = len([file for file in listdir(self._path) if self._log_file_suffix in file]) + 4
        self._progress_min = 0
        self._current_progress = 0
        self.header = None

    def run(self):
        self._find_available_files()
        self._create_log_files()
        self._remove_decompressed_files()

    def _update_progress(self):
        self._current_progress += 1

    def get_progress(self):
        return self._current_progress

    def __repr__(self):
        return f'<LogFolder Path: "{self._path}" Type: "{self._log_file_type}" >'

    def _gz_extract(self, file_to_extract) -> None:
        """
        Function to extract gzip compressed files to the same working directory.
        :param file_to_extract: File_name.gz (must be a gzip file)
        """
        with gzip.open(join(self._path, file_to_extract), 'rb') as f_in:
            with open(join(self._path, f'{file_to_extract[:-2]}txt'), 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
                self._extracted_files.append(f'{file_to_extract[:-2]}txt')
        self._update_progress()

    def _decompress_files(self) -> None:
        """
        Decompress files
        """
        for file in listdir(self._path):
            if isfile(join(self._path, file)):
                if '.gz' in file:
                    self._gz_extract(file)
        self._update_progress()

    def _remove_decompressed_files(self) -> None:
        """
        Removed decompressed *.gz files
        """
        if self._extracted_files:
            for file in self._extracted_files:
                os.remove(join(self._path, file))
        self._update_progress()

    def _find_available_files(self) -> None:
        """
        Find all files in the provided directory with the provided suffix.
        """
        self._decompress_files()
        for file in listdir(self._path):
            if isfile(join(self._path, file)):
                if self._log_file_suffix in file:
                    self._files.append(file)
        self._update_progress()

    def _create_log_files(self) -> None:
        """
        Opens each file in the LogFolder._files list and creates a log file
        """
        for file in self._files:
            with open(join(self._path, file), 'r', encoding='latin-1', errors='surrogateescape') as log_file:
                file_attributes = (file[:file.index(self._log_file_suffix) - 1], self._log_file_type)
                log_file = LogFileType[self._log_file_type].value(file_attributes, log_file)
                # todo raise custom error to remove the wrong long types, if there are multiple logs that use
                # todo the same file suffix
                if self.header is None:
                    self.header = log_file.header
                self.logs |= log_file.to_dict()
            self._update_progress()

    @property
    def log_list(self) -> List[Log]:
        if self.filtered_logs:
            logs = list(self.filtered_logs.values())
            return logs[0]
        else:
            logs = list(self.logs.values())
        return logs[0]

    @property
    def log_file_type(self):
        return self._log_file_type

    @property
    def progress_max(self):
        return self._progress_max


@dataclass
class TreeViewData:
    log_folder: LogFolder

    @property
    def header(self):
        return self.log_folder.header

    def filter_by_ur_number(self, ur_numbers: tuple):
        if ur_numbers:
            filtered_logs = []
            for name, logs in self.log_folder.logs.items():
                for idx, log in enumerate(logs):
                    for ur_number in list(ur_numbers):
                        if int(ur_number) == log.ur_number:
                            filtered_logs.append(log)
                    else:
                        pass
                self.log_folder.filtered_logs[name] = filtered_logs
        else:
            self.log_folder.filtered_logs = {}

    def filter_by_visit_number(self, visit_number: tuple):
        # todo handle if there are already filters, need to append items to the list
        if visit_number:
            filtered_logs = []
            for name, logs in self.log_folder.logs.items():
                for idx, log in enumerate(logs):
                    for visit_num in list(visit_number):
                        if int(visit_num) == log.visit_number:
                            filtered_logs.append(log)
                    else:
                        pass
                self.log_folder.filtered_logs[name] = filtered_logs
        else:
            self.log_folder.filtered_logs = {}

    def filter_all(self, search_query: str):
        pass

    def run(self):
        self.log_folder.run()

    def progress(self):
        return self.log_folder.get_progress()

# GUI Classes
# Widgets


class ContextMenu(tk.Menu):
    def __init__(self, parent, event, *args, **kwargs):
        """
        param parent: Parent window or frame to place this widget on
        """
        tk.Menu.__init__(self, parent, *args, **kwargs)
        self.my_event = event
        self.configure(tearoff=0, takefocus=0)
        self.add_command(label='Copy', command=self.copy)
        self.tk_popup(event.x_root, event.y_root)

    def copy(self):
        self.clipboard_clear()
        clipboard_list = []
        self.clipboard_append(', '.join(self.my_event.widget['columns']))
        self.clipboard_append('\n')
        for log in self.my_event.widget.selection():
            clipboard_list.append(', '.join([str(str_val) for str_val in self.my_event.widget.item(log)['values']]))
        self.clipboard_append('\n'.join(clipboard_list))


class SearchBox(tk.Frame):
    """
    Frame that includes an Entry box with Add/Remove buttons for modifying items in a list.
    Add button: Adds item to the list, based on the text located in the entry box
    Remove button: removes item to the list, based on selected item or if there are no selected
    items, then the last added item.
    """

    def __init__(self, parent, label, background, foreground, *args, **kwargs):
        """
        Construct a SearchBox (Frame subclass) with the parent MASTER
        :param parent: Parent window or frame to place this widget on
        :param label: Title of the widget (Displayed in the Label widget) inside the Searchbox.
        :param background: Sets the background of the frame and all child widgets inside the Searchbox.
        :param foreground: Sets the foreground of the frame and all child widgets inside the Searchbox.
        """
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.configure(background=background)

        # Widgets
        self.label = tk.Label(self,
                              text=f'{str(label).lower().capitalize()}',
                              bg=background,
                              fg=foreground,
                              highlightcolor='grey',
                              bd=0,
                              highlightthickness=0,
                              justify="center")
        self.search_var = tk.StringVar()
        self.entry = tk.Entry(self,
                              textvariable=self.search_var,
                              bg=background,
                              fg=foreground,
                              highlightcolor='grey',
                              bd=0,
                              highlightthickness=1,
                              justify="center",
                              width=26,
                              )
        self.search_list = tk.Variable()
        self.search = tk.Listbox(self,
                                 listvariable=self.search_list,
                                 height=4,
                                 bg=background,
                                 fg=foreground,
                                 highlightcolor='grey',
                                 bd=0,
                                 highlightthickness=1,
                                 selectbackground='grey',
                                 justify="center"
                                 )
        self.scrollbar = ttk.Scrollbar(self.search,
                                       orient=tk.VERTICAL,
                                       command=self.search.yview)
        self.search.configure(yscroll=self.scrollbar.set)
        self.add_button = tk.Button(self,
                                    text='Add',
                                    command=self.add_item,
                                    bg=background,
                                    fg=foreground)
        self.remove_button = tk.Button(self,
                                       text='Remove',
                                       command=self.remove_item,
                                       bg=background,
                                       fg=foreground)

        # Packing
        self.label.pack(side='top')
        self.search.pack(side='top', fill='x', anchor='n', expand=False, pady=(0, 10), padx=(70, 70))
        self.scrollbar.pack(side='right', fill='y', expand=False)
        self.entry.pack(side='top', anchor='n', pady=(0, 10), padx=(10, 10))
        self.add_button.pack(side='left', padx=(70, 5), ipadx=20)
        self.remove_button.pack(side='right', padx=(5, 70), ipadx=10)

    def remove_item(self) -> None:
        """
        Remove either the selected item or the most recently added item from the Searchbox Listbox widget.
        """
        try:
            selected_item = self.search.curselection()[0]
            self.search.delete(selected_item)
        except IndexError:
            self.search.delete(self.search.size() - 1)

    def add_item(self) -> None:
        """
        Add the item entered in the Searchbox Entry widget to the Searchbox Listbox widget. Cannot be an empty string.
        """
        item = self.search_var.get()
        if len(item) == 0:
            pass
        else:
            self.search.insert('end', item)
            self.search_var.set('')

    def get_keywords(self) -> Tuple[str,]:
        """
        Get the list of keywords added to the Searchbox Listbox widget.
        :return: Tuple[str]
        """
        if isinstance(self.search_list.get(), str):
            return tuple(self.search_list.get())
        else:
            return self.search_list.get()


class Button(tk.Button):
    def __init__(self, parent, *args, **kwargs):
        """
        param parent: Parent window or frame to place this widget on
        """
        tk.Button.__init__(self, parent, *args, **kwargs)
        self.configure(background=BACKGROUND,
                       foreground=FOREGROUND,
                       highlightcolor=BACKGROUND,
                       highlightbackground=BACKGROUND,
                       highlightthickness=0,
                       activebackground=BACKGROUND_2,
                       activeforeground=WHITE_TEXT,
                       borderwidth=0
                       )
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)

    def on_enter(self, event=None):
        self['background'] = BACKGROUND_2
        self['foreground'] = WHITE_TEXT

    def on_leave(self, event=None):
        self['background'] = BACKGROUND
        self['foreground'] = FOREGROUND


class PrimaryButton(Button):
    def __init__(self, parent, *args, **kwargs):
        """
        param parent: Parent window or frame to place this widget on
        """
        Button.__init__(self, parent, *args, **kwargs)
        self.configure(background=HIGHLIGHT,
                       foreground=HIGHLIGHT_TEXT,
                       highlightthickness=0,
                       borderwidth=0
                       )

    def on_enter(self, event=None):
        self['background'] = HIGHLIGHT_2
        self['foreground'] = HIGHLIGHT_TEXT_2

    def on_leave(self, event=None):
        self['background'] = HIGHLIGHT
        self['foreground'] = HIGHLIGHT_TEXT


class RadioButton(tk.Radiobutton):
    def __init__(self, parent, *args, **kwargs):
        """
        :param parent: Parent window or frame to place this widget on
        """
        tk.Radiobutton.__init__(self, parent, *args, **kwargs)
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.configure(background=BACKGROUND,
                       foreground=FOREGROUND,
                       highlightcolor=FOREGROUND,
                       highlightbackground=BACKGROUND,
                       highlightthickness=0,
                       activebackground=BACKGROUND_2,
                       activeforeground=WHITE_TEXT,
                       borderwidth=0,
                       indicatoron=False,
                       selectcolor=BACKGROUND_3, )

    def on_enter(self, event=None):
        self['background'] = BACKGROUND_2
        self['foreground'] = WHITE_TEXT

    def on_leave(self, event=None):
        self['background'] = BACKGROUND
        self['foreground'] = FOREGROUND


class ButtonFrame(tk.Frame):
    def __init__(self, parent, title, subtext, command=None, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.pack_propagate(False)
        self.configure(height=50, background=BACKGROUND)
        self.button_command = command
        self.subtext_var = tk.StringVar()
        self.subtext_var.set(subtext)
        self.title = tk.Label(self, name='btn_label_title', text=title, font=('', 12))
        self.subtext = tk.Label(self, name='btn_label_subtext', textvariable=self.subtext_var, font=('', 10))
        self.subtext.configure(background=BACKGROUND, foreground=FOREGROUND)
        self.title.configure(background=BACKGROUND, foreground=FOREGROUND)

        self.rel_y = 0.36
        self.current_rel_y = self.rel_y
        self.new_rel_y = 0.24
        self.speed = 0.01
        self.transitioning = False
        self.title.place(anchor='n', relheight=0.3, relx=0.5, rely=self.rel_y)

        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<1>', self.run_command)

    def set_subtext(self, text: str):
        self.subtext_var.set(text)

    def run_command(self, event=None):
        self.button_command()

    def on_enter_animate(self, timeout=[]):
        timeout.append('try')
        if len(timeout) > 30:
            self.reset_widget()
            timeout.clear()
        else:
            if self.current_rel_y >= self.new_rel_y:
                self.current_rel_y -= self.speed
                self.title.place_configure(rely=self.current_rel_y)
                if round(self.current_rel_y, 2) != self.new_rel_y:
                    self.after(10, self.on_enter_animate)
                elif round(self.current_rel_y, 2) == self.new_rel_y:
                    self.subtext.place(anchor='n', relheight=0.3, relx=0.5, rely=0.56)
                    timeout.clear()

    def on_leave_animate(self, timeout=[]):
        timeout.append('try')
        if len(timeout) > 30:
            self.reset_widget()
            timeout.clear()
        else:
            if self.current_rel_y <= self.rel_y:
                self.current_rel_y += self.speed
                self.title.place_configure(rely=self.current_rel_y)
                if round(self.current_rel_y, 2) != self.rel_y:
                    self.after(10, self.on_leave_animate)
                else:
                    self.reset_widget()
                    timeout.clear()

    def reset_widget(self):
        self.current_rel_y = self.rel_y
        self.title.place_forget()
        self.subtext.place_forget()
        self.title.place(anchor='n', relheight=0.3, relx=0.5, rely=self.rel_y)

    def on_enter(self, event=None):
        self['background'] = BACKGROUND_2
        self.title['background'] = BACKGROUND_2
        self.title['foreground'] = WHITE_TEXT
        self.subtext['foreground'] = WHITE_TEXT
        self.subtext['background'] = BACKGROUND_2
        self.on_enter_animate()

    def on_leave(self, event=None):
        self.subtext.place_forget()
        self['background'] = BACKGROUND
        self.title['background'] = BACKGROUND
        self.subtext['foreground'] = FOREGROUND
        self.on_leave_animate()


class ProgressBar(tk.Toplevel):
    """
    Usage
    ProgressBar(parent: parent window to create the widget from,
                command: command to be ran in thread,
                min_value: default 0, set minimum value of progress bar,
                max_value: default 100, set maximum value of progress bar,

    The command needs a command.progress() function, this function will be used to get the current
    progress of the task.
    """
    def __init__(self, parent, command=None, callback=None, max_value=100, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.wm_overrideredirect(True)
        self.wm_attributes('-topmost', True)
        w = '500'
        h = '20'
        x = parent.winfo_screenwidth() // 2 - round(int(w)/2)
        y = parent.winfo_screenheight() // 2 - round(int(h)/2)
        self.geometry(f'{w}x{h}+{x}+{y}')

        self.parent = parent
        self.task = command
        self.callback = callback
        self.max = max_value

        self.bar = ttk.Progressbar(self, maximum=self.max)
        self.bar.pack(side='top', fill='x', expand=True)
        self.thread = threading.Thread(target=self.task.run)
        self.thread.daemon = True
        self.start_task()

    def _progress(self):
        if self.thread.is_alive():
            self.bar['value'] = self.task.progress()
            self.after(100, self._progress)
        else:
            self.cleanup()

    def start_task(self):
        self.thread.start()
        self._progress()

    def cleanup(self):
        self.callback()
        self.destroy()

# Frames


class OptionsFrame(tk.Frame):
    """
    Options Frame for setting up the parameters for the parser that reads the logs used by the application.
    """

    def __init__(self, parent, *args, **kwargs):
        """
        :param parent: Parent window or frame to place this widget on
        """
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.selected_data = []
        self.parent: ClientApp = parent
        self.pack_propagate(False)
        self.configure(background=BACKGROUND, width=300)

        # Widgets

        self.title = tk.Label(self,
                              name='lbl_title',
                              text='Logger',
                              background=BACKGROUND,
                              foreground=FOREGROUND,
                              font=('Calibri', 44)
                              )
        self.separator = ttk.Separator(self,
                                       name='sep_title',
                                       orient='horizontal')
        self.step_one = tk.Label(self,
                                 name='lbl_step_one',
                                 text='Step 1',
                                 background=BACKGROUND,
                                 foreground=WHITE_TEXT,
                                 )
        self.separator_step_1 = ttk.Separator(self,
                                              name='sep_step_one',
                                              orient='horizontal')

        self.step_two = tk.Label(self,
                                 name='lbl_step_two',
                                 text='Step 2\n\nSelect a Log type to inspect',
                                 background=BACKGROUND,
                                 foreground=WHITE_TEXT,
                                 )

        self.separator_step_2 = ttk.Separator(self,
                                              name='sep_step_two',
                                              orient='horizontal')
        self.log_list_var = tk.StringVar()
        for suffix in Suffix:
            RadioButton(self,
                        name=f'rb_{suffix.name}',
                        text=suffix.name,
                        value=suffix.name,
                        variable=self.log_list_var,
                        command=self.radio_selected
                        )
        self.working_directory_var = tk.StringVar()
        self.working_directory_var.set('None')
        self.working_directory_button = ButtonFrame(self,
                                                    name='btn_working_directory',
                                                    title='Set Directory',
                                                    subtext=self.working_directory_var.get(),
                                                    command=self.select_working_folder
                                                    )

        self.working_directory_var.set(os.getcwd())

        self.read_logs_button = ButtonFrame(self, title='Read Logs', subtext='', name='btn_read',  command=self.read_logs)
        self.filter_button = ButtonFrame(self, title='Filter', subtext='', name='btn_filter',  command=self.filter)
        self.export_button = ButtonFrame(self, title='Export to CSV', subtext='', name='btn_export',  command=self.export_logs_to_csv)

        self.ur_number_search = SearchBox(self, name='srb_ur_number', label='UR Number search', background=BACKGROUND,
                                          foreground=FOREGROUND)
        self.visit_number_search = SearchBox(self, name='srb_visit_number', label='visit number search',
                                             background=BACKGROUND,
                                             foreground=FOREGROUND)
        self.wildcard_search = SearchBox(self, name='srb_wildcard', label='Anywhere search', background=BACKGROUND,
                                         foreground=FOREGROUND)

        # Packing
        self.title.pack(side='top', padx=(20, 0), pady=(30, 20))
        self.separator.pack(side='top', fill='x', pady=(20, 0))
        self.step_one.pack(side='top', pady=10)
        self.working_directory_button.pack(side='top', pady=(0, 0), fill='x', ipady=10)
        self.separator_step_1.pack(side='top', fill='x', pady=10)

        self.tree_view_data = None

    def select_working_folder(self, event=None) -> None:
        """
        Renders the filedialog.askdirectory dialog box requesting user input.
        Sets the self.working_directory_var to the users chosen folder path.
        """
        directory = filedialog.askdirectory(initialdir=os.getcwd())
        self.working_directory_var.set(directory)
        self.working_directory_button.set_subtext(self.working_directory_var.get())
        self.parent.parent.title(f'Logger [{self.working_directory_var.get()}]')
        self.pack_step_two()

    def pack_step_two(self):
        self.step_two.pack(side='top', fill='x', pady=10)
        for suffix in Suffix:
            self.nametowidget(f'rb_{suffix.name}').pack(side='top',
                                                        fill='x',
                                                        ipady=13)
        self.separator_step_2.pack(side='top', fill='x', pady=10)

    def pack_step_three(self):
        self.read_logs_button.pack(side='top', fill='x', ipady=10)
        self.export_button.pack(side='top', fill='x', ipady=10)

    def log_file_suffix(self):
        try:
            return Suffix[self.log_list_var.get()]
        except KeyError:
            messagebox.showerror(title='No log type selected',
                                 message='Invalid log file type to read. Please select a valid log file type')

    def read_logs(self):
        # todo check if the log type has changed
        if self.tree_view_data is None:
            self.tree_view_data = TreeViewData(log_folder=LogFolder(directory_path=self.working_directory_var.get(),
                                                                    log_file_suffix=self.log_file_suffix()))
            ProgressBar(self, self.tree_view_data,
                        callback=self.filter_data,
                        max_value=self.tree_view_data.log_folder.progress_max)
        else:
            pass

    def filter(self):
        selected_log = self.log_list_var.get()
        if 'PAS' in selected_log or 'BRD' in selected_log or 'REC' in selected_log:
            self.ur_number_search.pack(side='top', pady=(20, 0), fill='x')
            self.visit_number_search.pack(side='top', pady=(20, 0), fill='x')
            self.wildcard_search.pack(side='top', pady=(20, 0), fill='x')
        else:
            self.ur_number_search.forget()
            self.visit_number_search.forget()
            self.wildcard_search.forget()

    def filter_data(self):
        self.tree_view_data.filter_by_ur_number(self.ur_number_search.get_keywords())
        if self.visit_number_search.get_keywords():
            pass
        if self.wildcard_search.get_keywords():
            pass
        self.render()

    def render(self):
        self.tree_view_data: TreeViewData
        try:
            self.parent.result_display_frame.display_results(self.tree_view_data)
        except TypeError:
            messagebox.showerror(title='No log files found',
                                 message=f'There were no {self.tree_view_data.log_folder.log_file_type} files '
                                         f' found in {self.working_directory_var.get()}')

    def export_logs_to_csv(self):
        if self.tree_view_data:
            new_file = filedialog.asksaveasfilename(initialdir=os.getcwd(), defaultextension=".csv",
                                                    filetypes=(('*.csv', 'CSV File'),))
            with open(new_file, 'w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(list(self.tree_view_data.header))
                try:
                    if self.selected_data and len(self.selected_data) > 1:
                        for log in self.selected_data:
                            csv_writer.writerow(log)
                    elif self.selected_data and len(self.selected_data) == 1:
                        answer = messagebox.askyesnocancel('Only export one record?\n\n',
                                                           'You are exporting only one record.\n'
                                                           'Yes: Only one record\n'
                                                           'No: All data.\n'
                                                           'Cancel: Change options',
                                                           )
                        if answer:
                            for log in self.selected_data:
                                csv_writer.writerow(log)
                        elif not answer:
                            for log in self.tree_view_data.log_folder.log_list:
                                csv_writer.writerow(list(log.values()))
                    else:
                        for log in self.tree_view_data.log_folder.log_list:
                            csv_writer.writerow(list(log.values()))
                except TypeError:
                    os.remove(new_file)
        else:
            messagebox.showwarning(title='No data to export',
                                   message='You haven\'t loaded any data to export.')

    def radio_selected(self):
        self.filter_button.pack(side='top', pady=(0, 0), fill='x', ipady=10)
        self.pack_step_three()


class ResultDisplayFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent: ClientApp = parent
        self.pack_propagate(False)

        self.results = ttk.Treeview(self, show='headings')

        self.results.pack(side='left', fill='both', expand=True)
        self.y_scrollbar = ttk.Scrollbar(self.results, orient=tk.VERTICAL, command=self.results.yview)
        self.results.configure(yscroll=self.y_scrollbar.set)
        self.y_scrollbar.pack(side='right', fill='y', expand=False)

        self.x_scrollbar = ttk.Scrollbar(self.results, orient=tk.HORIZONTAL, command=self.results.xview)
        self.results.configure(xscroll=self.x_scrollbar.set)
        self.x_scrollbar.pack(side='bottom', fill='x', expand=False)

        self.results.bind('<<TreeviewSelect>>', self.select_result)
        self.results.bind('<3>', self.show_context_menu)

    def show_context_menu(self, event):
        ContextMenu(self, event)

    def select_result(self, event):
        self.parent.options_frame.selected_data.clear()
        for selected_item in self.results.selection():
            self.parent.options_frame.selected_data.append(self.results.item(selected_item)['values'])

    def sort_column(self, tv, col, reverse):
        # Sourced from https://stackoverflow.com/questions/1966929/tk-treeview-column-sort
        data_list = [(tv.set(k, col), k) for k in tv.get_children('')]
        data_list.sort(reverse=reverse)

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(data_list):
            tv.move(k, '', index)

        # reverse sort next time
        tv.heading(col, text=col, command=lambda _col=col: self.sort_column(tv, _col, not reverse))

    def delete_results(self):
        for log in self.results.get_children():
            self.results.delete(log)

    def display_results(self, tvd: TreeViewData):
        self.results['columns'] = ()
        self.results['columns'] = tvd.header

        for heading in tvd.header:
            self.results.heading(f'{heading}', text=f'{heading}',
                                 command=lambda _col=heading: self.sort_column(self.results, _col, False))
        self.delete_results()
        for log in tvd.log_folder.log_list:
            self.results.insert('',
                                tk.END,
                                text='',
                                values=log.values(),
                                )


class ClientApp(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.pack_propagate(True)
        self.configure(borderwidth=0, height=1080, width=1920)

        self.options_frame = OptionsFrame(self)
        self.options_frame.pack(side='left', fill='both', expand=False)

        self.result_display_frame = ResultDisplayFrame(self)
        self.result_display_frame.pack(side='left', fill='both', expand=True)


if __name__ == '__main__':
    root = tk.Tk()
    root.geometry('1920x1080')
    root.title('Logger')
    if sys.platform == "win32":
        root.state('zoomed')
    DARK_THEME = ttk.Style(root)
    DARK_THEME.theme_use("default")
    DARK_THEME.configure("Treeview",
                         fieldbackground=BACKGROUND,

                         font=('Arial', 11))

    DARK_THEME.configure("Treeview.Heading",
                         rowheight=30,
                         font=('Arial', 16)
                         )

    DARK_THEME.configure('TCombobox',
                         arrowsize=0,
                         fieldbackground=BACKGROUND,
                         foreground=FOREGROUND,
                         highlightcolor=BACKGROUND,
                         )

    ClientApp(root).pack(side='top', fill='both', expand=True)
    root.mainloop()
