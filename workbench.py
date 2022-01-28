import threading
import tkinter as tk
from time import sleep
from tkinter import ttk



def task_to_be_ran(callback):
    processing = True
    processing_progress = 5
    print('task running', threading.current_thread())
    while processing:
        sleep(1)
        processing_progress -= 1
        callback(processing)
        if processing_progress == 0:
            processing = False
    print('task finished')


class ProgressBar(tk.Toplevel):
    """
    Usage
    ProgressBar(parent: parent window to create the widget from,
                command: command to be ran in thread,
                min_value: default 0, set minimum value of progress bar,
                max_value: default 100, set maximum value of progress bar,

    """
    def __init__(self, parent, command=None, min_value=0, max_value=100, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.wm_overrideredirect(True)
        self.wm_attributes('-topmost', True)
        w = '500'
        h = '20'
        x = parent.winfo_screenwidth() // 2 - round(int(w)/2)
        y = parent.winfo_screenheight() // 2 - round(int(h)/2)
        self.geometry(f'{w}x{h}+{x}+{y}')

        self.task = command
        self.max = max_value
        self.min = min_value

        self.current_value = tk.IntVar()
        self.current_value = self.min
        self.bar = ttk.Progressbar(self)

        self.thread = threading.Thread(target=self.task)
        self.thread.daemon = True

        # run the task
        # update the progressbar
        self.start_task()

    def _progress(self):
        if self.thread.is_alive():
            print('progress')
            self.after(100, self._progress)
        else:
            self.cleanup()

    def start_task(self):
        self.thread.start()
        self._progress()

    def cleanup(self):
        self.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    root.geometry('800x600')
    button = tk.Button(root, text='Test')
    button.pack()
    task = ProgressBar(root, command=task_to_be_ran)
    root.mainloop()

