import tkinter as tk
from tkinter import ttk

import json
import os
from tkinter.messagebox import showwarning

from resources import constants


class GlobalSettings:
    _instance = None
    _settings = {}
    _settings_file = 'settings.json'

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalSettings, cls).__new__(cls)
            cls._load_settings()
        return cls._instance

    @classmethod
    def _load_settings(cls):
        if os.path.isfile(cls._settings_file):
            with open(cls._settings_file, 'r') as f:
                cls._settings = json.load(f)
        else:
            cls._settings = {}

    @classmethod
    def _save_settings(cls):
        with open(cls._settings_file, 'w') as f:
            json.dump(cls._settings, f, ensure_ascii=False, indent=4)

    @classmethod
    def get_settings(cls):
        return cls._settings

    @classmethod
    def set_setting(cls, key, value):
        if key in cls._settings:
            cls._settings[key] = value
        else:
            cls.add_setting(key, value)

        cls._save_settings()

        return cls._settings[key]

    @classmethod
    def get_setting(cls, key):
        if key in cls._settings:
            return cls._settings[key]
        return None

    @classmethod
    def add_setting(cls, key, value):
        cls._settings[key] = value
        cls._save_settings()
        return cls._settings[key]


class SettingsModal:
    def __init__(self, master, refresh):
        self.master = master
        self.refresh = refresh

        self.window = tk.Toplevel(master, padx=20, pady=10)
        self.window.title("Настройки")
        self.window.resizable(False, False)

        window_width = 300
        window_height = 200

        main_modal_width = self.master.winfo_width()
        main_modal_height = self.master.winfo_height()
        main_modal_x = self.master.winfo_x()
        main_modal_y = self.master.winfo_y()

        position_right = main_modal_x + (main_modal_width // 2) - (window_width // 2)
        position_down = main_modal_y + (main_modal_height // 2) - (window_height // 2)

        self.window.geometry(f'{window_width}x{window_height}+{position_right}+{position_down}')

        self.settings = GlobalSettings()

        self.user_name = self.settings.get_setting('user_name')
        self.depot = self.settings.get_setting('depot')

        self.version = ttk.Label(self.window, text=f'Версия: {constants.CURRENT_VERSION}')

        self.user_name_label = ttk.Label(self.window, text='Никнейм:')
        self.user_name_entry = ttk.Entry(self.window)
        self.user_name_entry.insert(0, self.user_name)

        self.depot_label = ttk.Label(self.window, text='Депот:')
        self.depot_combobox = ttk.Combobox(self.window, values=['paf_test', 'paf'])
        self.depot_combobox.set(self.depot)
        self.depot_combobox.configure(state="readonly")

        self.user_name_label.pack(fill=tk.X, pady=(0, 5))
        self.user_name_entry.pack(fill=tk.X, ipady=3, ipadx=5, pady=(0, 8))

        self.depot_label.pack(fill=tk.X, pady=(0, 5))
        self.depot_combobox.pack(fill=tk.X, ipady=3, ipadx=5, pady=(0, 10))

        self.version.pack(fill=tk.X, pady=(0, 5))

        save_button = ttk.Button(self.window, text="Сохранить", command=self.save_settings)
        save_button.pack(ipady=3, ipadx=5, side=tk.BOTTOM)

    def save_settings(self):
        user_name = self.user_name_entry.get()
        depot = self.depot_combobox.get()

        if not user_name:
            showwarning(title='Nick')
            return

        if user_name == self.user_name and depot == self.depot:
            return

        self.user_name = self.settings.set_setting('user_name', user_name)
        self.depot = self.settings.set_setting('depot', depot)

        self.refresh()
        self.window.destroy()