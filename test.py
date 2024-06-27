import os
import sys
import tkinter as tk
from init import InitModal
from settings import GlobalSettings
from tiler import TileSelector

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    output_image_path = "resources\map.png"
    output_image_path = resource_path(output_image_path)
    root = tk.Tk()
    settings = GlobalSettings()
    user_name = GlobalSettings.get_setting('user_name')

    if not user_name:
        InitModal(root, output_image_path)
    else:
        TileSelector(root, resource_path(output_image_path))

    root.mainloop()
