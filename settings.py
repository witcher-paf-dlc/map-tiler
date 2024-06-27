# settings_modal.py
import tkinter as tk
from tkinter import ttk

import json
import os

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
            cls._settings = {
                'tile_size': 256,
                'tile_border_size': 3,
            }

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
    def __init__(self, master):
        self.master = master

        self.window = tk.Toplevel(master)
        self.window.title("Settings")

        self.settings = GlobalSettings()

        self.entries = {}
        row = 0
        for key, value in self.settings.get_settings().items():
            label = ttk.Label(self.window, text=key)
            label.grid(row=row, column=0, padx=10, pady=10)
            entry = ttk.Entry(self.window)
            entry.insert(0, value)
            entry.grid(row=row, column=1, padx=10, pady=10)
            self.entries[key] = entry
            row += 1

        save_button = ttk.Button(self.window, text="Сохранить", command=self.save_settings)
        save_button.grid(row=row, column=0, columnspan=2, pady=10)

    def save_settings(self):
        for key, var in self.entries.items():
            value = var.get()
            self.settings.set_setting(key, value)
        self.window.destroy()
