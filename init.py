from settings import GlobalSettings
import tkinter as tk
from tkinter import ttk

from tiler import TileSelector
from tkinter.messagebox import showerror, showwarning, showinfo


class InitModal:
    def __init__(self, master):
        self.master = master

        self.settings = GlobalSettings
        self.settings.add_setting('user_name', '');

        label = ttk.Label(self.master, text='Ник:')
        label.pack()
        self.entry = ttk.Entry(self.master)
        self.entry.pack()

        save_button = ttk.Button(self.master, text="Сохранить", command=self.init)
        save_button.pack()

    def init(self):
        nick = self.entry.get()

        if not nick:
            showwarning(title='Nick')
            return

        self.settings.set_setting('user_name', nick)
        self.master.destroy()
        root = tk.Tk()
        TileSelector(root, 'stitched_tiles.png')
        root.mainloop()
