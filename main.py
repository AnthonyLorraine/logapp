import csv
import tkinter as tk
import gzip
import os
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


# Log Classes


class Log:
    """
    Base log class to hold common functionality across logfiles
    """

    def __init__(self, raw_data: str):
        self.raw = raw_data

    def header(self):
        pass

    def values(self):
        pass


class BRDLog(Log):
    """
    Broadcaster Log class has common HL7 Attributes
    """

    def __init__(self, raw_data: str):
        """
        Converts the raw string data to the BRDLog object
        :param raw_data: str data to be converted to class object
        """
        super().__init__(raw_data)
        if len(self.raw) != 0:
            self.msh = str(self.raw)[53:].split('|')[0:19]
            try:
                self.message_date_time = datetime.strptime(self.msh[6], '%Y%m%d%H%M%S')
            except AttributeError:
                print(self.raw)
            except IndexError:
                print(self.raw)
            self.message_date = self.message_date_time.date()
            self.message_time = self.message_date_time.time()
            self.message_type = self.msh[8][12:]
            self.message_id = int(self.msh[9])
            self.pid = ''
            self.ur_number = ''
            self.first_name = ''
            self.middle_name = ''
            self.last_name = ''
            self.date_of_birth = None
            try:
                self.pid = str(self.raw)[str(self.raw).find('PID|'):].split('|')[:31]
                self.ur_number = self.pid[3].split('^')[0]
                self.first_name = self.pid[5].split('^')[1]
                self.middle_name = self.pid[5].split('^')[2]
                self.last_name = self.pid[5].split('^')[0]
                self.date_of_birth = datetime.strptime(self.pid[7], '%Y%m%d').date()
            except IndexError:
                pass
            try:
                self.pv1 = str(self.raw)[str(self.raw).find('PV1|'):].split('|')[:45]
                self.admission_type = self.pv1[2]
                self.ward = ''
                self.bed = ''
                self.visit_number = 0
                if self.admission_type.lower() == 'e':
                    self.ward = 'Emergency'
                    self.bed = self.pv1[10].split('^')[1]
                else:
                    self.ward = self.pv1[3].split('^')[0]
                    self.bed = self.pv1[3].split('^')[3]
                    self.visit_number = int(self.pv1[5])
            except IndexError:
                self.ward = ''
                self.bed = ''
                self.visit_number = 0
                self.admission_type = ''

    def __repr__(self):
        return f'<BRDLog MsgID:{self.message_id} MsgType:{self.message_type} MRN:{self.ur_number}>'


class RECLog(Log):
    """
    Receiver Log class has common HL7 Attributes
    """

    def __init__(self, raw_data: str):
        """
        Converts the raw string data to the RECLog object
        :param raw_data: str data to be converted to class object
        """
        super().__init__(raw_data)
        if len(self.raw) != 0:
            self.msh = str(self.raw)[53:].split('|')[0:19]
            try:
                self.message_date_time = datetime.strptime(self.msh[5][:14], '%Y%m%d%H%M%S')
            except AttributeError:
                print(self.raw)
            except IndexError:
                print(self.raw)
            self.message_date = self.message_date_time.date()
            self.message_time = self.message_date_time.time()
            self.message_type = self.msh[7][12:]
            self.message_id = 0
            try:
                self.message_id = int(self.msh[8])
            except ValueError:
                self.message_id = self.msh[8]
            self.pid = ''
            self.ur_number = ''
            self.first_name = ''
            self.middle_name = ''
            self.last_name = ''
            self.date_of_birth = None
            try:
                self.pid = str(self.raw)[str(self.raw).find('PID|'):].split('|')[:31]
                self.ur_number = self.pid[3].split('^')[0]
                self.first_name = self.pid[5].split('^')[1]
                self.middle_name = self.pid[5].split('^')[2]
                self.last_name = self.pid[5].split('^')[0]
                self.date_of_birth = datetime.strptime(self.pid[7], '%Y%m%d').date()
            except IndexError:
                pass
            try:
                self.pv1 = str(self.raw)[str(self.raw).find('PV1|'):].split('|')[:45]
                self.admission_type = self.pv1[2]
                self.ward = ''
                self.bed = ''
                self.visit_number = 0
                if self.admission_type.lower() == 'e':
                    self.ward = 'Emergency'
                    self.bed = self.pv1[10].split('^')[1]
                else:
                    self.ward = self.pv1[3].split('^')[0]
                    self.bed = self.pv1[3].split('^')[3]
                    self.visit_number = int(self.pv1[5])
            except ValueError:
                try:
                    self.visit_number = int(self.pv1[17].split('^')[0])
                except ValueError:
                    self.visit_number = 0
            except IndexError:
                self.ward = ''
                self.bed = ''
                self.visit_number = 0
                self.admission_type = ''

    def __repr__(self):
        return f'<RECLog MsgID:{self.message_id} MsgType:{self.message_type} MRN:{self.ur_number}>'


class PASAccessLog(Log):
    """
    Webpas Web Server Access Log
    """

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
    BRD = BRDLog
    REC = RECLog
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
        self.header = self._logs[0].header()

    def _create_log_files(self):
        for log in self._raw_logs:
            self._logs.append(LogType[self.log_type].value(log))

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
    PASAccessLog = 'txt'
    MEXAccessLog = '0'
    BRDTransactionLog = 'brd'
    RECTransactionLog = 'rec'


class LogFolder:
    """
    Folder level class that contains a list of log files, each logfile contains logs.
    """

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
        self.header = None
        self._find_available_files()
        self._create_log_files()
        self._remove_decompressed_files()

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

    def _decompress_files(self) -> None:
        """
        Decompress files
        """
        for file in listdir(self._path):
            if isfile(join(self._path, file)):
                if '.gz' in file:
                    self._gz_extract(file)

    def _remove_decompressed_files(self) -> None:
        """
        Removed decompressed *.gz files
        """
        if self._extracted_files:
            for file in self._extracted_files:
                os.remove(join(self._path, file))

    def _find_available_files(self) -> None:
        """
        Find all files in the provided directory with the provided suffix.
        """
        self._decompress_files()
        for file in listdir(self._path):
            if isfile(join(self._path, file)):
                if self._log_file_suffix in file:
                    self._files.append(file)

    def _create_log_files(self) -> None:
        """
        Opens each file in the LogFolder._files list and creates a log file
        """
        for file in self._files:
            with open(join(self._path, file), 'r') as log_file:
                file_attributes = (file[:file.index(self._log_file_suffix) - 1], self._log_file_type)
                log_file = LogFileType[self._log_file_type].value(file_attributes, log_file)
                if self.header is None:
                    self.header = log_file.header
                self.logs |= log_file.to_dict()

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


# GUI Classes

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
                    log: PASAccessLog
                    for ur_number in list(ur_numbers):
                        if int(ur_number) == log.ur_number:
                            filtered_logs.append(log)
                    else:
                        pass
                self.log_folder.filtered_logs[name] = filtered_logs
        else:
            self.log_folder.filtered_logs = {}
        print(self.log_folder.filtered_logs)

    def filter_by_visit_number(self, visit_number: int):
        pass

    def filter_all(self, search_query: str):
        pass


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

    def get_keywords(self) -> tuple[str,]:
        """
        Get the list of keywords added to the Searchbox Listbox widget.
        :return: Tuple[str]
        """
        if isinstance(self.search_list.get(), str):
            return tuple(self.search_list.get())
        else:
            return self.search_list.get()


class OptionsFrame(tk.Frame):
    """
    Options Frame for setting up the parameters for the parser that reads the logs used by the application.
    """

    def __init__(self, parent, *args, **kwargs):
        """
        :param parent: Parent window or frame to place this widget on
        """
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent: ClientApp = parent
        self.pack_propagate(False)
        self.configure(background='black', width=300)

        # Widgets
        self.log_list_var = tk.StringVar()
        self.log_list_var.set('Select a log type to read')
        self.log_list = tk.OptionMenu(self, self.log_list_var, *[suffix.name for suffix in Suffix])
        self.working_directory_button = tk.Button(self, text='Select Directory', command=self.select_working_folder)
        self.working_directory_var = tk.StringVar()
        self.working_directory_var.set(os.getcwd())
        self.working_directory_path_display = tk.Entry(self, textvariable=self.working_directory_var, width=100)
        self.read_logs_button = tk.Button(self, text='Read Logs', command=self.read_logs)
        self.filter_button = tk.Button(self, text='Filter', command=self.filter)
        self.export_button = tk.Button(self, text='Export to CSV', command=self.export_logs_to_csv)
        self.ur_number_search = SearchBox(self, label='UR Number search', background='black', foreground='white')
        self.visit_number_search = SearchBox(self, label='visit number search', background='black', foreground='white')
        self.wildcard_search = SearchBox(self, label='Anywhere search', background='black', foreground='white')

        # Packing
        self.log_list.pack(side='top', padx=(20, 0))
        self.working_directory_button.pack(side='top', pady=(20, 0))
        self.working_directory_path_display.pack(side='top', pady=(20, 0))
        self.read_logs_button.pack(side='top', pady=(20, 0))
        self.filter_button.pack(side='top', pady=(20, 0))
        self.export_button.pack(side='top', pady=(20, 0))
        self.ur_number_search.pack(side='top', pady=(20, 0), fill='x')
        self.visit_number_search.pack(side='top', pady=(20, 0), fill='x')
        self.wildcard_search.pack(side='top', pady=(20, 0), fill='x')

        self.tree_view_data = None

    def select_working_folder(self) -> None:
        """
        Renders the filedialog.askdirectory dialog box requesting user input.
        Sets the self.working_directory_var to the users chosen folder path.
        """
        directory = filedialog.askdirectory(initialdir=os.getcwd())
        self.working_directory_var.set(directory)

    def log_file_suffix(self):
        try:
            return Suffix[self.log_list_var.get()]
        except KeyError:
            messagebox.showerror(title='No log type selected',
                                 message='Invalid log file type to read. Please select a valid log file type')
            self.log_list.configure(bg='red')
            # todo revert the color after new selection made

    def read_logs(self):
        # todo check if the log type has changed
        if self.tree_view_data is None:
            self.tree_view_data = TreeViewData(log_folder=LogFolder(directory_path=self.working_directory_var.get(),
                                                                    log_file_suffix=self.log_file_suffix()))
        else:
            pass
        self.filter()

    def filter(self):
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
            with filedialog.asksaveasfile(mode='w', initialdir=os.getcwd(), defaultextension=".csv", filetypes=(('*.csv', 'CSV File'),)) as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(list(self.tree_view_data.header))
                for log in self.tree_view_data.log_folder.log_list:
                    csv_writer.writerow(list(log.values()))
        else:
            messagebox.showwarning(title='No data to export',
                                   message='You haven\'t loaded any data to export.')


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

    def select_result(self, event):
        for selected_item in self.results.selection():
            print(self.results.item(selected_item))

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
            self.results.heading(f'{heading}', text=f'{heading}', command=lambda _col=heading: self.sort_column(self.results, _col, False))
        self.delete_results()
        for log in tvd.log_folder.log_list:
            self.results.insert('',
                                tk.END,
                                text='',
                                values=log.values()
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
    root.title('Log Reader')
    root.state('zoomed')
    DARK_THEME = ttk.Style(root)
    DARK_THEME.theme_use("clam")
    DARK_THEME.configure("Treeview",
                         background="black",
                         fieldbackground="black",
                         foreground="white",
                         bd=0,
                         relief='flat',
                         highlightcolor='grey',
                         selectbackground='grey',
                         highlightthickness=0)
    ClientApp(root).pack(side='top', fill='both', expand=True)
    root.mainloop()
