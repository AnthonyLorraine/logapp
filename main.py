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
from os.path import join
from os import getcwd
from sys import platform
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


class OptionsFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.pack_propagate(False)
        self.configure(background='black', width=300)
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

    def read_logs(self):
        result_grid: ttk.Treeview = self.parent.result_display_frame
        self.parent.result_display_frame.column_names.append('Fish')
        result_grid.update_idletasks()

    def export_logs_to_csv(self):
        pass


class ResultDisplayFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.pack_propagate(False)
        self.configure(background='yellow')
        self.column_names = ['cats', 'dogs', 'elbows']

        self.results = ttk.Treeview(self, columns=self.column_names, show='headings')
        for column in self.column_names:
            self.results.heading(f'{column}', text=f'{column}')

        for contact in range(1, 100):
            self.results.insert('', tk.END, text='',
                                values=(f'first {contact}', f'last {contact}', f'email{contact}@example.com'))
        self.results.pack(side='left', fill='both', expand=True)

        self.results_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.results.yview)
        self.results.configure(yscroll=self.results_scrollbar.set)
        self.results_scrollbar.pack(side='right', fill='y', expand=False)

        self.results.bind('<<TreeviewSelect>>', self.select_result)

    def select_result(self, event):
        for selected_item in self.results.selection():
            print(self.results.item(selected_item))
        print(event)


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

    # icon_path = join(getcwd(), 'icon.jpg')
    # root.iconphoto(True, tk.PhotoImage(file=icon_path))
    ClientApp(root).pack(side='top', fill='both', expand=True)
    root.mainloop()
