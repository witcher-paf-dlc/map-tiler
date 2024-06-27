from components.settings import GlobalSettings
import tkinter as tk
from tkinter import ttk

from components.tiler import TileSelector
from tkinter.messagebox import showwarning


class InitModal:
    def __init__(self, master, image):
        self.master = master
        self.image = image

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
        TileSelector(root, self.image)
        root.mainloop()
