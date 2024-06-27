import tkinter as tk
from init import InitModal
from settings import GlobalSettings
from tiler import TileSelector

if __name__ == "__main__":
    output_image_path = "stitched_tiles.png"
    root = tk.Tk()
    settings = GlobalSettings()
    user_name = GlobalSettings.get_setting('user_name')

    if not user_name:
        InitModal(root)
    else:
        TileSelector(root, output_image_path)

    root.mainloop()
