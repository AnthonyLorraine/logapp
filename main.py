# choose log type
# - BRD REC
# - PAS ACCESS
# - MEX LOGS

# select folder path that contains the brd files
# display results in datagrid (Full screenable)
# export to csv
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from os.path import join, isfile
from os import getcwd, listdir
from sys import platform
from typing import List

from PIL import Image, ImageTk

if platform == "win32":
    import ctypes

    # Set the Taskbar Icon on windows
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('rishu.chatapp.client.v0.001')


class SearchBox(tk.Frame):
    def __init__(self, parent, label, background, foreground, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.configure(
            background=background)

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
        self.search = tk.Listbox(self,
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

        self.label.pack(side='top')

        self.search.pack(side='top',
                         fill='x',
                         anchor='n',
                         expand=False,
                         pady=(0, 10),
                         padx=(70, 70))

        self.scrollbar.pack(side='right',
                            fill='y',
                            expand=False)
        self.entry.pack(side='top',
                        anchor='n',
                        pady=(0, 10),
                        padx=(10, 10)
                        )
        self.add_button.pack(side='left', padx=(70, 5), ipadx=20)
        self.remove_button.pack(side='right', padx=(5, 70), ipadx=10)

    def remove_item(self):
        try:
            selected_item = self.search.curselection()[0]
            self.search.delete(selected_item)
        except IndexError:
            self.search.delete(self.search.size() - 1)

    def add_item(self):
        item = self.search_var.get()
        if len(item) == 0:
            pass
        else:
            self.search.insert('end', item)
            self.search_var.set('')

    def get(self):
        return self.search_var.get()


class OptionsFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.pack_propagate(False)
        self.configure(background='black', width=300)
        self.log_headers = []
        self.log_data = []
        self.log_data_column_width = 0
        self.log_list_var = tk.StringVar()
        self.log_list_var.set('Select a log type to read')
        self.log_list_options = ['HL7 BRD/REC Files', 'WebPAS Access Logs', 'Mex Application Logs']
        self.log_list = tk.OptionMenu(self, self.log_list_var, *self.log_list_options)
        self.log_list.pack(side='top', padx=(20, 0))

        self.working_directory_button = tk.Button(self, text='Select Directory', command=self.select_working_folder)
        self.working_directory_var = tk.StringVar()
        self.working_directory_button.pack(side='top', pady=(20, 0))
        self.working_directory_path_display = tk.Entry(self, textvariable=self.working_directory_var, width=100)
        self.working_directory_path_display.pack(side='top', pady=(20, 0))

        self.read_logs_button = tk.Button(self, text='Read Logs', command=self.read_logs)
        self.read_logs_button.pack(side='top', pady=(20, 0))

        self.export_button = tk.Button(self, text='Export to CSV', command=self.export_logs_to_csv)
        self.export_button.pack(side='top', pady=(20, 0))

        self.ur_number_search = SearchBox(self,
                                          label='UR Number search',
                                          background='black',
                                          foreground='white')
        self.ur_number_search.pack(side='top', pady=(20, 0), fill='x')

        self.visit_number_search = SearchBox(self,
                                             label='visit number search',
                                             background='black',
                                             foreground='white')
        self.visit_number_search.pack(side='top', pady=(20, 0), fill='x')

        self.wildcard_search = SearchBox(self,
                                         label='Anywhere search',
                                         background='black',
                                         foreground='white')
        self.wildcard_search.pack(side='top', pady=(20, 0), fill='x')

    def select_working_folder(self):
        directory = filedialog.askdirectory(initialdir=os.getcwd())
        self.working_directory_var.set(directory)

    def render_logs(self):
        self.parent.result_display_frame.display_results(
            headers=tuple(self.log_headers),
            results=self.log_data
        )

    def calculate_column_width(self, column_data_length: int):
        if column_data_length > self.log_data_column_width:
            self.log_data_column_width = column_data_length


    def read_logs(self):
        directory = self.working_directory_var.get()
        files = [join(directory, file) for file in listdir(directory)
                 if isfile(join(directory, file))
                 and ('.rec' in file or '.brd' in file)]
        patient_id = '189442'
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
                            if len(data[0]) > 1 and f'|{patient_id}^' in data[0]:
                                self.calculate_column_width(len(data))
                                self.log_data.append(data)
                            data = []
                            header.append(log)
                        else:
                            header.append(log[:80])
                    except NameError:
                        msg_body = str(log).strip()
                        if 'Timeout waiting for incoming message' not in msg_body:
                            body.append(str(log).strip())
        self.log_headers.clear()
        self.log_headers.append(('Data', 1500))
        self.render_logs()


    def export_logs_to_csv(self):
        pass


class ResultDisplayFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent: tk.Tk = parent
        self.pack_propagate(False)

        self.results = ttk.Treeview(self, show='headings')

        self.results.pack(side='left', fill='both', expand=True)

        self.results_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.results.yview)
        self.results.configure(yscroll=self.results_scrollbar.set)
        self.results_scrollbar.pack(side='right', fill='y', expand=False)

        self.results.bind('<<TreeviewSelect>>', self.select_result)

    def select_result(self, event):
        for selected_item in self.results.selection():
            print(self.results.item(selected_item))

    def display_results(self, headers: tuple[str, int], results: List[tuple]):
        self.set_headers(headers)
        self.set_results(results)

    def set_headers(self, headers: List[tuple[str, int]]):
        # cols requires (name, name, name)
        # widths requires (20, 20, 20)
        self.results['columns'] = ()
        self.results['columns'] = headers
        for idx, header_data in enumerate(headers):
            self.results.heading(f'{header_data[0]}', text=f'{header_data[0]}')
            self.results.column(idx+1, width=header_data[1])

    def set_results(self, result_list: List[tuple]):
        for item in self.results.get_children():
            self.results.delete(item)
        for result in result_list:
            self.results.insert('',
                                tk.END,
                                text='',
                                values=result)


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
