import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk
from tkinter import filedialog
from os.path import join, isfile
from os import getcwd, listdir
from sys import platform
from typing import List
from dataclasses import dataclass
import threading
from PIL import Image, ImageTk

if platform == "win32":
    import ctypes
    # Set the Taskbar Icon on windows
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('rishu.logapp.client.v0.001')


@dataclass
class PatientLog:
    msg_id: int
    msg_date: datetime.date
    msg_time: datetime.time
    msg_type: str
    ur_number: str  # str because there are leading zero's at some sites
    visit_number: int
    first_name: str
    middle_name: str
    last_name: str
    date_of_birth: datetime.date

    @property
    def header(self):
        return 'msg_id', 'msg_date', 'msg_time', 'msg_type', 'ur_number', 'visit_number', 'first_name', 'middle_name', 'last_name', 'date_of_birth'

    @property
    def column_width(self):
        return 75, 75, 75, 75, 100, 100, 200, 200, 200, 100

    def to_tuple(self):
        v_no = ''
        if self.visit_number == 0:
            v_no = ''
        else:
            v_no = self.visit_number
        return self.msg_id, self.msg_date, self.msg_time, self.msg_type, self.ur_number, v_no, self.first_name, self.middle_name.strip('"'), self.last_name, self.date_of_birth


class BRDParse:
    def __init__(self, data: str):
        self.raw = data
        if len(self.raw) != 0 and 'HL7RECVR' not in self.raw:
            self.msh = str(self.raw)[53:].split('|')[0:19]
            try:
                self.message_date_time = datetime.strptime(self.msh[6], '%Y%m%d%H%M%S')
            except:
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

    def log(self):
        if len(self.raw) != 0 and 'HL7RECVR' not in self.raw:
            log = PatientLog(msg_id=self.message_id,
                             msg_date=self.message_date,
                             msg_time=self.message_time,
                             msg_type=self.message_type,
                             ur_number=self.ur_number,
                             visit_number=self.visit_number,
                             first_name=self.first_name,
                             middle_name=self.middle_name,
                             last_name=self.last_name,
                             date_of_birth=self.date_of_birth)
            if log:
                return log


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

    def get_keywords(self) -> tuple[str, ]:
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
        self.parent = parent
        self.pack_propagate(False)
        self.configure(background='black', width=300)

        self.keywords = []
        self.log_headers = []
        self.log_data = []
        self.original_log_data = self.log_data
        self.log_data_column_width = 0

        # Widgets
        self.log_list_var = tk.StringVar()
        self.log_list_var.set('Select a log type to read')
        self.log_list_options = ['HL7 BRD/REC Files', 'WebPAS Access Logs', 'Mex Application Logs']
        self.log_list = tk.OptionMenu(self, self.log_list_var, *self.log_list_options)
        self.working_directory_button = tk.Button(self, text='Select Directory', command=self.select_working_folder)
        self.working_directory_var = tk.StringVar()
        self.working_directory_var.set(os.getcwd())
        self.working_directory_path_display = tk.Entry(self, textvariable=self.working_directory_var, width=100)
        self.read_logs_button = tk.Button(self, text='Read Logs', command=threading.Thread(target=self.read_logs).start)
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

    def select_working_folder(self) -> None:
        """
        Renders the filedialog.askdirectory dialog box requesting user input.
        Sets the self.working_directory_var to the users chosen folder path.
        """
        directory = filedialog.askdirectory(initialdir=os.getcwd())
        self.working_directory_var.set(directory)

    def filter(self):
        self.log_data = self.original_log_data
        self.generate_keywords()
        filtered_data = []
        if self.keywords:
            for data in self.log_data:
                if any(keyword in str(data.to_tuple()) for keyword in self.keywords):
                    filtered_data.append(data)
            self.log_data = filtered_data
        self.render_logs()


    def render_logs(self):
        self.parent.result_display_frame.display_results(
            headers=tuple(self.log_headers),
            results=self.log_data
        )

    def calculate_column_width(self, column_data_length: int):
        if column_data_length > self.log_data_column_width:
            self.log_data_column_width = column_data_length

    def read_logs(self):
        print('Reading logs', threading.current_thread())
        self.parse_brd_rec_logfiles()

    def thread_read_logs(self):
        print('Reading logs', threading.current_thread())
        self.read_logs()
        print('Finished parsing logs', threading.current_thread())

    def export_logs_to_csv(self):
        pass

    def generate_keywords(self):
        self.keywords.clear()
        keywords = self.ur_number_search.get_keywords() + self.visit_number_search.get_keywords() + self.wildcard_search.get_keywords()
        for keyword in keywords:
            self.keywords.append(keyword)

    def parse_brd_rec_logfiles(self):
        # get keywords to search
        self.generate_keywords()
        directory = self.working_directory_var.get()
        files = [join(directory, file) for file in listdir(directory)
                 if isfile(join(directory, file))
                 and ('.rec' in file or '.brd' in file)]

        header = []
        body = []
        data = []
        for file in files:
            with open(file) as log_file:
                for idx, log in enumerate(log_file):
                    try:
                        if not log[:80] == (80 * '-'):
                            raise NameError
                        if len(header) != 0:
                            data.append(' '.join(body))
                            header = []
                            body = []
                            if self.keywords:
                                if any(keyword in data for keyword in self.keywords):
                                    log = BRDParse(data[0]).log()
                                    if log:
                                        self.log_data.append(log)
                            else:
                                log = BRDParse(data[0]).log()
                                if log:
                                    self.log_data.append(log)
                            data = []
                            header.append(log)
                        else:
                            header.append(log[:80])
                    except NameError:
                        msg_body = str(log).strip()
                        if 'Timeout waiting for incoming message' not in msg_body:
                            body.append(str(log).strip())
        self.log_headers = ()

        self.log_headers = (self.log_data[0].header,
                            self.log_data[0].column_width)
        self.render_logs()


class ResultDisplayFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent: tk.Tk = parent
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

    def display_results(self, headers: tuple[tuple[str], tuple[int]], results: List[tuple]):
        self.set_headers(headers)
        self.set_results(results)

    def set_headers(self, headers: List[tuple[str, int]]):
        self.results['columns'] = ()
        self.results['columns'] = headers[0]
        for heading in headers[0]:
            self.results.heading(f'{heading}', text=f'{heading}')
        for idx, width in enumerate(headers[1]):
            self.results.column(idx, width=width)

    def set_results(self, result_list: List[tuple]):
        for item in self.results.get_children():
            self.results.delete(item)
        if result_list:
            for result in result_list:
                result: PatientLog
                self.results.insert('',
                                    tk.END,
                                    text='',
                                    values=result.to_tuple()
                                    )
        else:
            self.results.insert('',
                                tk.END,
                                text='',
                                values=('No results',))


class ClientApp(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.pack_propagate(True)
        self.configure(borderwidth=0, height=1080, width=1920, background='blue')

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
    # icon_path = join(getcwd(), 'icon.jpg')
    # root.iconphoto(True, tk.PhotoImage(file=icon_path))
    ClientApp(root).pack(side='top', fill='both', expand=True)
    root.mainloop()