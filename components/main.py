import json
import tkinter as tk
from tkinter import ttk as ttk

import numpy as np
from tkinter.messagebox import showwarning
import os

from models.level import Level
from models.map import MapData
from resources import icons
from utils import utils
from p4 import P4Manager
from components.settings import SettingsModal, GlobalSettings
from components.map import MapCanvas
from models.tile import Tile, CheckoutInfo


class MainModal:
    def __init__(self, master):
        self.p4 = P4Manager()
        self.level = None

        self.master = master
        self.settings = GlobalSettings()

        self.start_selection = None
        self.user_colors = {}

        self.workspaces = []
        self.levels = []

        self.workspace = None
        self.level = None

        self.setup_ui()

        self.load_workspaces()

    def setup_ui(self):
        self.master.geometry('1270x700')
        self.master.title('Map')
        self.master.resizable(False, False)

        self.red_button_style = ttk.Style()
        self.red_button_style.configure('Green.TButton', foreground="green", background="green")

        self.red_button_style = ttk.Style()
        self.red_button_style.configure('Red.TButton', foreground="red3", background='red3')

        self.plus_icon_tk = tk.PhotoImage(data=icons.add_icon)
        self.refresh_icon_tk = tk.PhotoImage(data=icons.refresh_icon)

        self.control_frame = tk.Frame(self.master, width=700, height=700)
        self.control_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        self.left_panel_frame = tk.Frame(self.control_frame, width=200)
        self.left_panel_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=15, pady=5)

        self.right_panel_frame = tk.Frame(self.control_frame, width=200)
        self.right_panel_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=15, pady=5)

        self.canvas_image = MapCanvas(self.control_frame, 700, 700, self.level, self.right_panel_frame)
        self.canvas = self.canvas_image.canvas

        self.selected_tiles = self.canvas_image.selected_tiles

        self.tiles_info_canvas = tk.Canvas(self.right_panel_frame, width=200)
        self.tiles_info_canvas.pack(fill=tk.BOTH, expand=True)

        self.refresh_button = ttk.Button(self.left_panel_frame, text="Обновить", command=self.refresh_level)
        self.clear_button = ttk.Button(self.left_panel_frame, text="Очистить выбранные тайлы", command=self.clear_tiles)
        self.checkout_button = ttk.Button(self.left_panel_frame, text="Чекаут", command=self.checkout_tiles, style='Green.TButton')
        self.uncheckout_button = ttk.Button(self.left_panel_frame, text="Анчекаут", command=self.uncheckout_tiles, style='Red.TButton')
        self.settings_button = ttk.Button(self.left_panel_frame, text="Настройки", command=self.open_settings_modal)

        self.separator = ttk.Separator(self.left_panel_frame, orient='horizontal')
        self.second_separator = ttk.Separator(self.left_panel_frame, orient='horizontal')

        self.workspace_combobox_label = ttk.Label(self.left_panel_frame, text="Воркспейс:")
        self.workspace_combobox = ttk.Combobox(self.left_panel_frame, values=self.workspaces)
        self.workspace_combobox.configure(state="readonly")

        self.level_combobox_label = ttk.Label(self.left_panel_frame, text="Уровень:")
        self.level_combobox = ttk.Combobox(self.left_panel_frame, values=[level.name for level in self.levels])
        self.level_combobox.configure(state="readonly")

        self.selected_tiles_listbox = tk.Listbox(self.right_panel_frame)

        # self.selected_tiles_listbox.pack(fill=tk.X)

        self.checkout_button.pack(ipady=5, ipadx=5, pady=(0, 10), fill=tk.X)
        self.uncheckout_button.pack(ipady=5, ipadx=5, fill=tk.X)

        self.separator.pack(pady=15, fill=tk.X)

        self.refresh_button.pack(ipady=5, ipadx=5, pady=(0, 10), fill=tk.X)
        self.clear_button.pack(ipady=5, ipadx=5, fill=tk.X)

        self.settings_button.pack(ipady=5, ipadx=5, fill=tk.X, side=tk.BOTTOM)

        self.second_separator.pack(pady=(15, 10), fill=tk.X)

        self.workspace_combobox_label.pack(pady=(0, 3), fill=tk.X)
        self.workspace_combobox.pack(ipady=3, ipadx=5, pady=(0, 10), fill=tk.X)

        self.level_combobox_label.pack(pady=(0, 3), fill=tk.X)
        self.level_combobox.pack(ipady=3, ipadx=5, pady=(0, 5), fill=tk.X)

        self.canvas.bind("<Button-1>", self.on_click, add=True)
        self.workspace_combobox.bind("<<ComboboxSelected>>", self.change_workspace)
        self.level_combobox.bind("<<ComboboxSelected>>", self.change_level)

    def open_settings_modal(self):
        SettingsModal(self.master, self.load_workspaces)

    def on_click(self, event):
        if not self.level:
            return

        mat_inv = np.linalg.inv(self.canvas_image.mat_affine)
        image_coords = np.dot(mat_inv, [event.x, event.y, 1])
        image_x, image_y = image_coords[0], image_coords[1]

        tile_size = self.level.map_data.tile_size
        border_size = self.level.map_data.border_size

        total_tile_size = tile_size + border_size

        tile_x = int(image_x // total_tile_size)
        tile_y = int(image_y // total_tile_size)

        tile: Tile = self.get_tile_by_coords(tile_x, tile_y)

        if tile is not None:
            if tile.checkout_info is not None:
                if tile.checkout_info.workspace == self.workspace.name:
                    if tile.checkout_info.unchekout:
                        tile.checkout_info.unchekout = False
                        tile.color = self.user_colors[tile.checkout_info.workspace]
                        self.update_tiles_info_canvas()
                        self.canvas_image.redraw_image()
                        return

                    tile.color = 'red'
                    tile.checkout_info.unchekout = True
                    self.update_tiles_info_canvas()
                    self.canvas_image.redraw_image()
                    return

            if tile.checkout_info is not None:
                showwarning(title='Тайл занят', message='Тайл уже занят другим пользователем')
            else:
                self.selected_tiles.remove(tile)
                self.update_tiles_info_canvas()
                self.canvas_image.redraw_image()
            return

        if event.state & 0x0004 and self.start_selection is not None:
            x1, y1 = self.start_selection
            x2, y2 = tile_x, tile_y
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    tile = Tile(x, y)
                    if tile not in self.selected_tiles:
                        self.selected_tiles.add(tile)

            self.start_selection = None
        else:
            self.start_selection = (tile_x, tile_y)
            tile = Tile(tile_x, tile_y)
            self.selected_tiles.add(tile)

        self.update_tiles_info_canvas()
        self.canvas_image.redraw_image()

    def load_workspaces(self):
        self.workspaces = self.p4.load_workspaces()
        self.workspace_combobox['values'] = self.workspaces

        if self.workspaces:
            self.workspace_combobox.current(0)
            self.select_workspace(self.workspaces[0])
        else:
            self.workspace_combobox.set('')
            self.select_workspace(None)

    def load_levels(self, workspace):
        if workspace is None:
            self.levels = []
            self.level_combobox['value'] = self.levels
            self.level_combobox.set('')
            self.select_level(None)
            return

        depot = self.settings.get_setting('depot')

        levels_path = os.path.join(workspace.folder, 'workspace', 'levels')
        dlc_levels_path = os.path.join(workspace.folder, 'workspace', 'dlc', depot, 'data', 'levels')

        levels = self._get_levels_from_path(levels_path)
        dlc_levels = self._get_levels_from_path(dlc_levels_path, True)

        self.levels = levels + dlc_levels
        self.level_combobox['value'] = self.levels

        if self.levels:
            selected_level_path = self.settings.get_setting('level')
            selected_level = next((level for level in self.levels if level.path == selected_level_path),
                                  self.levels[0] if self.levels else None)

            index = self.levels.index(selected_level)
            self.level_combobox.current(index)
            self.select_level(selected_level)
        else:
            self.level_combobox.set('')
            self.select_level(None)

    def load_tiles(self, level, show_message=True):
        self.checkouted_tiles = self.p4.load_tiles(level=level)

        replaced = False

        for checkouted_tile in self.checkouted_tiles:
            workspace, tiles = checkouted_tile['workspace'], checkouted_tile['tiles']

            if workspace not in self.user_colors:
                if workspace == self.workspace.name:
                    self.user_colors[workspace] = utils.get_user_color()
                else:
                    self.user_colors[workspace] = utils.get_random_color()

            color = self.user_colors[workspace]
            checkouted_tile['color'] = color

            for tile in tiles:
                x, y = tile['x'], tile['y']
                selected_tile = self.get_tile_by_coords(x, y)
                if selected_tile is not None and selected_tile.checkout_info is None:
                    selected_tile.checkout_info = CheckoutInfo(workspace)
                    selected_tile.color = color
                    replaced = True
                elif selected_tile is None:
                    self.selected_tiles.add(Tile(x, y, color, CheckoutInfo(workspace)))

        self.update_tiles_info_canvas()
        self.canvas_image.redraw_image()

        if show_message and replaced:
            showwarning(title='Тайлы заменены', message='В результате обновления некоторые выбранные вами тайлы '
                                                        'оказались заняты и были заменены.')

        return replaced

    def select_workspace(self, workspace):
        self.workspace = workspace

        self.p4.set_client(workspace)
        self.load_levels(workspace)

    def select_level(self, level):
        if level is not None:
            self.settings.set_setting('level', level.path)

        self.level = level

        self.selected_tiles.clear()
        self.canvas_image.set_level(level)

        self.load_tiles(level)

    def change_workspace(self, event):
        workspace = self.workspaces[self.workspace_combobox.current()]
        self.select_workspace(workspace)

    def change_level(self, event):
        level = self.levels[self.level_combobox.current()]
        self.select_level(level)

    def refresh_level(self):
        self.load_tiles(self.level)

    def checkout_tiles(self):
        if self.level is None:
            return

        replaced = self.load_tiles(self.level, show_message=False)
        if replaced:
            showwarning(title='Тайлы заменены', message='В результате обновления некоторые выбранные вами тайлы '
                                                        'оказались заняты и были заменены, просмотрите выбранные тайлы и сделайте чекаут повторно.')
            return

        tiles_to_checkout = {tile for tile in self.selected_tiles if tile.checkout_info is None}

        if not tiles_to_checkout:
            return

        self.p4.checkout_tiles(tiles_to_checkout, self.level)
        self.selected_tiles.clear()
        self.load_tiles(self.level)

    def uncheckout_tiles(self):
        if self.level is None:
            return

        tiles_to_uncheckout = {tile for tile in self.selected_tiles if tile.checkout_info is not None and tile.checkout_info.unchekout == True}

        if not tiles_to_uncheckout:
            return

        self.p4.uncheckout_tiles(tiles_to_uncheckout, self.level)
        self.selected_tiles.clear()
        self.load_tiles(self.level)

    def clear_tiles(self):
        tiles_to_remove = {tile for tile in self.selected_tiles if tile.checkout_info is None}
        self.selected_tiles -= tiles_to_remove

        for tile in self.selected_tiles:
            if tile.checkout_info.unchekout:
                tile.checkout_info.unchekout = False
                tile.color = self.user_colors[tile.checkout_info.workspace]

        self.canvas_image.redraw_image()

    def update_tiles_info_canvas(self):
        self.tiles_info_canvas.delete("all")

        y_offset = 0
        user_name = GlobalSettings.get_setting('user_name')

        for checkouted_tile in self.checkouted_tiles:
            workspace, color = checkouted_tile['workspace'], checkouted_tile['color']

            user = workspace.split('_')[0]

            self.tiles_info_canvas.create_rectangle(5, y_offset + 5, 25, y_offset + 25, fill=color, outline=color)
            self.tiles_info_canvas.create_text(35, y_offset + 15, anchor="w",
                                               text=f"занят {user} {'(ты)' if user == user_name else ''}")
            y_offset += 30

    def get_tile_by_coords(self, x, y):
        for tile in self.selected_tiles:
            if tile.x == x and tile.y == y:
                return tile
        return None

    @staticmethod
    def _get_levels_from_path(path, is_dlc=False):
        if not os.path.exists(path):
            return []

        levels = []
        for level_name in os.listdir(path):
            level_folder = os.path.join(path, level_name)
            map_folder = os.path.join(level_folder, 'map_data')
            map_image_path = os.path.join(map_folder, 'map.png')
            map_json_path = os.path.join(map_folder, 'map.json')

            if os.path.exists(map_folder) and os.path.exists(map_image_path) and os.path.exists(map_json_path):
                with open(map_json_path, 'r') as f:
                    map_data_json = json.load(f)
                map_data = MapData.from_json(map_data_json)
                levels.append(Level(level_name, map_image_path, map_data, level_folder, is_dlc))
        return levels
