from components.settings import GlobalSettings
import tkinter as tk
from tkinter import ttk

from components.main import MainModal
from tkinter.messagebox import showwarning


class InitModal:
    def __init__(self, master):
        self.master = master
        self.master.geometry('300x200')
        self.master.configure(padx=20, pady=10)
        self.master.resizable(False, False)
        self.master.title('Инициализация')

        self.settings = GlobalSettings

        self.user_name_label = ttk.Label(self.master, text='Никнейм:')
        self.user_name_entry = ttk.Entry(self.master)

        self.depot_label = ttk.Label(self.master, text='Депот:')
        self.depot_combobox = ttk.Combobox(self.master, values=['paf_test', 'paf'])
        self.depot_combobox.current(0)
        self.depot_combobox.configure(state="readonly")

        self.user_name_label.pack(fill=tk.X, pady=(0, 5))
        self.user_name_entry.pack(fill=tk.X, ipady=3, ipadx=5, pady=(0, 8))

        self.depot_label.pack(fill=tk.X, pady=(0, 5))
        self.depot_combobox.pack(fill=tk.X, ipady=3, ipadx=5, pady=(0, 10))

        save_button = ttk.Button(self.master, text="Сохранить", command=self.init)
        save_button.pack(ipady=3, ipadx=5, side=tk.BOTTOM)

    def init(self):
        nick = self.user_name_entry.get()
        depot = self.depot_combobox.get()

        if not nick:
            showwarning(title='Введите никнейм', message='Введите никнейм')
            return

        self.settings.set_setting('user_name', nick)
        self.settings.set_setting('depot', depot)

        self.master.destroy()

        root = tk.Tk()
        MainModal(root)
        root.mainloop()
