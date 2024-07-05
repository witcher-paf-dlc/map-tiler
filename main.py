import tkinter as tk
from components.init import InitModal
from components.settings import GlobalSettings
from components.main import MainModal

if __name__ == "__main__":
    root = tk.Tk()
    settings = GlobalSettings()
    user_name = GlobalSettings.get_setting('user_name')
    depot = GlobalSettings.get_setting('depot')

    if not user_name or not depot:
        InitModal(root)
    else:
        MainModal(root)

    root.mainloop()
