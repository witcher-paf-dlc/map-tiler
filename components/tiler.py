import tkinter as tk
from tkinter import ttk as ttk

import numpy as np
from PIL import Image, ImageTk
from tkinter import filedialog
from tkinter.messagebox import showwarning
from resources import icons, constants
from utils import utils
from p4 import P4Manager
from components.settings import SettingsModal, GlobalSettings
from components.map import PanZoomCanvas
from models.tile import Tile, CheckoutInfo


class TileSelector:
    def __init__(self, master, image_path):
        self.p4 = P4Manager()

        self.tiles_combobox = None
        self.tiles_combobox_label = None
        self.separator = None
        self.workspaces = None
        self.refresh_button = None
        self.clear_button = None
        self.checkout_button = None
        self.settings_button = None
        self.workspace_combobox = None
        self.container = None
        self.canvas = None
        self.canvas_image = None
        self.control_frame = None

        self.master = master
        self.image_path = image_path
        self.tile_size = constants.TILE_SIZE
        self.grid_size = constants.GRID_ROWS
        self.border_size = constants.TILE_BORDER_SIZE
        self.scale_factor = constants.SCALE_FACTOR

        self.selected_tiles = set()
        self.start_selection = None

        self.user_colors = {}

        self.original_image = Image.open(image_path)
        self.image = self.original_image.resize(
            (int(self.original_image.width * self.scale_factor), int(self.original_image.height * self.scale_factor)))
        self.tk_image = ImageTk.PhotoImage(self.image)

        self.setup_ui()

        self.load_tiles()
        self.load_workspaces()

    def setup_ui(self):
        self.master.geometry('1300x700')

        self.plus_icon_tk = tk.PhotoImage(data=icons.add_icon)
        self.refresh_icon_tk = tk.PhotoImage(data=icons.refresh_icon)

        self.control_frame = tk.Frame(self.master, width=700, height=700)
        self.control_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        self.left_panel_frame = tk.Frame(self.control_frame, width=200)
        self.left_panel_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=15, pady=5)

        self.right_panel_frame = tk.Frame(self.control_frame, width=200)
        self.right_panel_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=15, pady=5)

        self.canvas_image = PanZoomCanvas(self.control_frame, 700, 700, self.image_path, self.right_panel_frame)
        self.canvas = self.canvas_image.canvas
        self.selected_tiles = self.canvas_image.selected_tiles

        self.tiles_info_canvas = tk.Canvas(self.right_panel_frame, width=200, bd=0)
        self.tiles_info_canvas.pack(fill=tk.X, expand=True)

        self.refresh_button = ttk.Button(self.left_panel_frame, text="Обновить", command=self.load_tiles)
        self.clear_button = ttk.Button(self.left_panel_frame, text="Очистить выбранные тайлы", command=self.clear_tiles)
        self.checkout_button = ttk.Button(self.left_panel_frame, text="Чекаут", command=self.checkout_tiles)
        self.settings_button = ttk.Button(self.left_panel_frame, text="Настройки", command=self.open_settings_modal)

        self.perforce_status = ttk.Label(self.left_panel_frame, text='Perforce статус: ', foreground='green')

        self.separator = ttk.Separator(self.left_panel_frame, orient='horizontal')

        self.workspace_combobox_label = tk.Label(self.left_panel_frame, text="Воркспейс:")
        self.workspaces_frame = tk.Frame(self.left_panel_frame)
        self.workspace_combobox = ttk.Combobox(self.workspaces_frame, values=self.workspaces)
        self.workspace_combobox.configure(state="readonly")
        self.refresh_workspaces_button = ttk.Button(self.workspaces_frame, image=self.refresh_icon_tk, width=20,
                                                    command=self.load_workspaces)

        self.tiles_folder_combobox_label = tk.Label(self.left_panel_frame, text="Папка с тайлами:")
        self.tiles_folder_frame = tk.Frame(self.left_panel_frame)
        self.tiles_folders = GlobalSettings.get_setting('tiles_folders')

        if not self.tiles_folders:
            self.tiles_folders = GlobalSettings.add_setting('tiles_folders', [])

        self.tiles_folder_combobox = ttk.Combobox(self.tiles_folder_frame, values=self.tiles_folders)

        if len(self.tiles_folders) > 0:
            self.tiles_folder_combobox.set(GlobalSettings.get_setting('selected_tiles_folder'))

        self.tiles_folder_combobox.configure(state="readonly")
        self.add_tiles_folder_button = ttk.Button(self.tiles_folder_frame, image=self.plus_icon_tk, width=20,
                                                  command=self.add_tiles_folder)

        self.selected_tiles_listbox = tk.Listbox(self.right_panel_frame)

        # self.selected_tiles_listbox.pack(fill=tk.X)

        self.refresh_button.pack(ipady=5, ipadx=5, fill=tk.X)
        self.clear_button.pack(ipady=5, ipadx=5, pady=10, fill=tk.X)
        self.checkout_button.pack(ipady=5, ipadx=5, fill=tk.X)
        self.settings_button.pack(ipady=5, ipadx=5, fill=tk.X, side=tk.BOTTOM)
        self.perforce_status.pack(ipady=5, ipadx=5, fill=tk.X, side=tk.BOTTOM)

        self.separator.pack(pady=(15, 10), fill=tk.X)

        self.workspace_combobox_label.pack(pady=(0, 3), fill=tk.X)
        self.workspaces_frame.pack(fill=tk.X)
        self.workspace_combobox.pack(ipady=3, ipadx=5, padx=(0, 5), fill=tk.X, side=tk.LEFT, expand=True)
        self.refresh_workspaces_button.pack(side=tk.RIGHT, expand=False)

        self.tiles_folder_combobox_label.pack(pady=(10, 3), fill=tk.X)
        self.tiles_folder_frame.pack(fill=tk.X)
        self.tiles_folder_combobox.pack(ipady=3, ipadx=5, padx=(0, 5), fill=tk.X, side=tk.LEFT, expand=True)
        self.add_tiles_folder_button.pack(side=tk.RIGHT, expand=False)

        self.canvas.bind("<Button-1>", self.on_click, add=True)
        self.tiles_folder_combobox.bind("<<ComboboxSelected>>", self.select_tiles_folder)
        self.workspace_combobox.bind("<<ComboboxSelected>>", self.select_workspace)

    def open_settings_modal(self):
        SettingsModal(self.master)

    def on_click(self, event):
        mat_inv = np.linalg.inv(self.canvas_image.mat_affine)
        image_coords = np.dot(mat_inv, [event.x, event.y, 1])
        image_x, image_y = image_coords[0], image_coords[1]

        tile_size = 256
        border_size = 3

        total_tile_size = tile_size + border_size

        tile_x = int(image_x // total_tile_size)
        tile_y = int(image_y // total_tile_size)

        tile = self.get_tile_by_coords(tile_x, tile_y)

        if tile is not None:
            if tile.checkout_info is not None:
                showwarning(title='Тайл занят', message='Тайл уже занят другим пользователем')
            else:
                self.selected_tiles.remove(tile)
                self.update_tiles_info_canvas()
                self.canvas_image.redraw_image()
            return

        tile = Tile(tile_x, tile_y)

        self.selected_tiles.add(tile)
        self.update_tiles_info_canvas()
        self.canvas_image.redraw_image()

        # self.selected_tiles_listbox.delete(0, tk.END)
        # for index, tile in enumerate(sorted(self.canvas_image.selected_tiles)):
        #     if not tile.checkout_info:
        #         self.selected_tiles_listbox.insert(tk.END, f"{tile.x}, {tile.y})")

    def clear_tiles(self):
        tiles_to_remove = {tile for tile in self.selected_tiles if tile.checkout_info is None}
        self.selected_tiles -= tiles_to_remove
        self.canvas_image.redraw_image()

    def load_workspaces(self):
        self.workspaces = self.p4.load_workspaces()

        if len(self.workspaces) == 0:
            showwarning(title='Вокспейсов не найдено',
                        message='Вокспейсов не найдено, возможно вы некорректно указали свой ник или название вокрспейса в P4V.')
            return

        formatted_workspaces = [
            f"Название: '{workspace['client']}' | Папка: '{workspace['root']}'"
            for workspace in self.workspaces
        ]
        self.workspace_combobox['values'] = formatted_workspaces
        self.workspace_combobox.set(formatted_workspaces[0])
        self.p4.set_client(self.workspaces[0]['client'])

    def load_tiles(self, show_message=True):
        self.checkouted_tiles = self.p4.load_tiles()

        replaced = False

        for checkouted_tile in self.checkouted_tiles:
            user, tiles = checkouted_tile['user'], checkouted_tile['tiles']

            if user not in self.user_colors:
                self.user_colors[user] = utils.get_random_color()

            color = self.user_colors[user]
            checkouted_tile['color'] = color

            for tile in tiles:
                x, y = tile['x'], tile['y']
                selected_tile = self.get_tile_by_coords(x, y)
                if selected_tile is not None and selected_tile.checkout_info is None:
                    selected_tile.checkout_info = CheckoutInfo(user)
                    selected_tile.color = color
                    replaced = True
                elif selected_tile is None:
                    self.selected_tiles.add(Tile(x, y, color, CheckoutInfo(user)))

        self.update_tiles_info_canvas()
        self.canvas_image.redraw_image()

        if show_message and replaced:
            showwarning(title='Тайлы заменены', message='В результате обновления некоторые выбранные вами тайлы '
                                                        'оказались заняты и были заменены.')

        return replaced

    def checkout_tiles(self):
        replaced = self.load_tiles(show_message=False)
        if replaced:
            showwarning(title='Тайлы заменены', message='В результате обновления некоторые выбранные вами тайлы '
                                                        'оказались заняты и были заменены, просмотрите выбранные тайлы и сделайте чекаут повторно.')
            return

        tiles_to_checkout = {tile for tile in self.selected_tiles if tile.checkout_info is None}

        self.p4.checkout_tiles(tiles_to_checkout, self.tiles_folder_combobox.get())
        self.clear_tiles()
        self.load_tiles()


    def add_tiles_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            if folder_selected not in self.tiles_folders:
                self.tiles_folders.append(folder_selected)
                self.tiles_folder_combobox['values'] = self.tiles_folders
                self.tiles_folder_combobox.set(folder_selected)
                GlobalSettings.set_setting('selected_tiles_folder', folder_selected)
                GlobalSettings._save_settings()

    def select_tiles_folder(self, event):
        selected_folder = self.tiles_folder_combobox.get()
        GlobalSettings.set_setting('selected_tiles_folder', selected_folder)

    def select_workspace(self, event):
        selected_workspace = self.workspace_combobox.get()

    def update_tiles_info_canvas(self):
        self.tiles_info_canvas.delete("all")

        y_offset = 0
        user_name = GlobalSettings.get_setting('user_name')

        for checkouted_tile in self.checkouted_tiles:
            user, color = checkouted_tile['user'], checkouted_tile['color']

            self.tiles_info_canvas.create_rectangle(5, y_offset + 5, 25, y_offset + 25, fill=color, outline=color)
            self.tiles_info_canvas.create_text(35, y_offset + 15, anchor="w", text=f"занят {user} {'(ты)' if user == user_name else ''}")
            y_offset += 30

    def get_tile_by_coords(self, x, y):
        for tile in self.selected_tiles:
            if tile.x == x and tile.y == y:
                return tile
        return None
