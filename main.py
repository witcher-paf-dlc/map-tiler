import os
import tkinter as tk
from tkinter import ttk, messagebox, ALL
from PIL import Image, ImageDraw, ImageTk, ImageFont
import subprocess
from tkinter import filedialog
from P4 import P4, P4Exception
import utils
import constants
from components.CanvasImage import CanvasImage
from test2 import PanZoomCanvas
from tile import Tile
import time

p4 = P4()
p4.port = "ssl:18.198.116.34:1666"
p4.client = "perforce_DESKTOP-8HBDVCG_PAF-01-AT-Test_7248"

Image.MAX_IMAGE_PIXELS = None


class TileSelector:
    def __init__(self, master, image_path):
        self.master = master

        self.image_path = image_path
        self.tile_size = constants.TILE_SIZE
        self.grid_size = constants.GRID_ROWS
        self.border_size = constants.TILE_BORDER_SIZE

        self.scale_factor = constants.SCALE_FACTOR
        self.last_zoom_time = time.time()
        self.zoom_threshold = 0.05

        self.selected_tiles = set()
        self.start_selection = None

        self.user_colors = {}

        self.original_image = Image.open(image_path)
        self.image = self.original_image.resize(
            (int(self.original_image.width * self.scale_factor), int(self.original_image.height * self.scale_factor)))
        self.tk_image = ImageTk.PhotoImage(self.image)

        self.setup_ui()

        self.canvas.bind("<Button-1>", self.on_click)

        # self.refresh_tiles()

    def setup_ui(self):
        self.master.configure(bg='darkblue')

        self.control_frame = tk.Frame(self.master, bg='darkblue')
        self.control_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

        self.image_frame = tk.Frame(self.master, bg='darkblue', bd=2, relief=tk.RIDGE)
        self.image_frame.rowconfigure(0, weight=1)
        self.image_frame.columnconfigure(0, weight=1)
        self.image_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.canvas_image = PanZoomCanvas(self.image_frame, self.image_path)
        self.canvas_image.grid(row=0, column=0)

        self.canvas = self.canvas_image.canvas

        self.selected_tiles_listbox = tk.Listbox(self.control_frame)
        self.selected_tiles_listbox.pack(pady=10)

        self.ocupied_tiles_canvas = tk.Canvas(self.control_frame, bg='white', width=100, height=100)
        self.ocupied_tiles_canvas.pack(pady=10, fill=tk.BOTH, expand=True)

        self.clear_button = tk.Button(self.control_frame, text="Clear Selection", command=self.clear_selection)
        self.clear_button.pack(pady=10)

        self.checkout_button = tk.Button(self.control_frame, text="Checkout Tiles", command=self.checkout_tiles)
        self.checkout_button.pack(pady=10)

        self.refresh_button = tk.Button(self.control_frame, text="Refresh Tiles", command=self.refresh_tiles)
        self.refresh_button.pack(pady=10)

        self.client_label = tk.Label(self.control_frame, text="Workspace name:")
        self.client_label.pack(pady=5)
        self.client_entry = tk.Entry(self.control_frame)
        self.client_entry.pack(pady=5)

    def outside(self, x, y):
        """ Checks if the point (x,y) is outside the image area """
        bbox = self.canvas.coords(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            return False  # point (x,y) is inside the image area
        else:
            return True  # point (x,y) is outside the image area

    def clear_selection(self):
        self.selected_tiles.clear()
        self.canvas.delete("highlight")
        self.update_selected_tiles_list()

    def on_click(self, event):
        ctrl_pressed = (event.state & 0x4) != 0
        x = int((self.canvas.canvasx(event.x) / self.canvas_image.imscale - self.border_size) // (
                self.tile_size + self.border_size))
        y = int((self.canvas.canvasy(event.y) / self.canvas_image.imscale - self.border_size) // (
                self.tile_size + self.border_size))

        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            tile_coord = Tile(x, y)

            for tile in self.selected_tiles:
                if tile.x == x and tile.y == y:
                    if tile.checkout_info:
                        messagebox.showerror("Tile Occupied", f"Tile ({x},{y}) is occupied.")
                        return

            if ctrl_pressed and self.start_selection is not None:
                end_selection = (x, y)
                self.select_area(self.start_selection, end_selection)
                self.start_selection = None
            else:
                self.start_selection = (x, y)
                if tile_coord in self.selected_tiles:
                    self.selected_tiles.remove(tile_coord)
                    self.unhighlight_tile(x, y)
                else:
                    self.selected_tiles.add(tile_coord)
                    self.highlight_tile(x, y)

    def get_contiguous_regions(self):
        visited = set()
        contiguous_regions = []

        def dfs(tile, region):
            x = tile.x
            y = tile.y
            if tile in visited or tile not in self.selected_tiles:
                return
            visited.add(tile)
            region.append(tile)
            neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
            for neighbor in neighbors:
                if neighbor in self.selected_tiles:
                    dfs(neighbor, region)

        for tile in self.selected_tiles:
            if tile not in visited:
                region = []
                dfs(tile, region)
                contiguous_regions.append(region)

        return contiguous_regions

    def select_area(self, start, end):
        x1, y1 = start
        x2, y2 = end
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                tile_coord = Tile(x, y)
                if tile_coord not in self.selected_tiles:
                    self.selected_tiles.add(tile_coord)
                    self.highlight_tile(x, y)

    def on_zoom(self, event):
        scale_change = 0.05
        min_scale_factor = max(700 / self.original_image.width, 700 / self.original_image.height)
        if event.delta > 0:
            new_scale_factor = self.scale_factor + scale_change
        else:
            new_scale_factor = max(min_scale_factor, self.scale_factor - scale_change)

        self.scale_factor = new_scale_factor
        print(self.scale_factor)
        self.update_image()

    def on_drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def update_image(self):
        self.image = self.original_image.resize(
            (int(self.original_image.width * self.scale_factor), int(self.original_image.height * self.scale_factor)),
            Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        self.canvas.delete("highlight")
        for tile in self.selected_tiles:
            self.highlight_tile(tile.x, tile.y)

    def update_selected_tiles_list(self):
        self.ocupied_tiles_canvas.delete("all")
        self.selected_tiles_listbox.delete(0, tk.END)

        y_offset = 0
        authors = []

        for index, tile in enumerate(sorted(self.selected_tiles)):
            if tile.checkout_info is None:
                self.selected_tiles_listbox.insert(tk.END, f"{tile.x}, {tile.y})")
            if tile.checkout_info not in authors:
                authors.append(tile.checkout_info)
                color_rect = self.ocupied_tiles_canvas.create_rectangle(5, y_offset + 5, 25, y_offset + 25,
                                                                        fill=tile.color, outline=tile.color)
                self.ocupied_tiles_canvas.create_text(35, y_offset + 15, anchor="w", text=f"by {tile.checkout_info}")
                self.ocupied_tiles_canvas.tag_bind(color_rect, "<Button-1>",
                                                   lambda event, a=tile.checkout_info: self.highlight_occupied_tiles(a))
                self.ocupied_tiles_canvas.tag_bind(self.ocupied_tiles_canvas.create_text(35, y_offset + 15, anchor="w",
                                                                                         text=f"by {tile.checkout_info}"),
                                                   "<Button-1>",
                                                   lambda event, a=tile.checkout_info: self.highlight_occupied_tiles(a))
                y_offset += 30

    def highlight_occupied_tiles(self, author):
        self.canvas.delete("highlight")
        for tile in self.selected_tiles:
            tile.highlighted = False
            if tile.author == author:
                tile.highlighted = True
        self.highlight_tile(0, 0)

    def highlight_tile(self, x, y, color="red"):
        self.canvas.delete("highlight")

        for tile in self.selected_tiles:
            x, y = tile.x, tile.y

            width = 3

            pos_x = x * (self.tile_size + self.border_size) + self.border_size
            pos_y = y * (self.tile_size + self.border_size) + self.border_size
            pos_x_scaled = int(pos_x * self.scale_factor) + width
            pos_y_scaled = int(pos_y * self.scale_factor) + width
            tile_size_scaled = int(self.tile_size * self.scale_factor) - width * 2

            color = tile.color

            self.canvas.create_rectangle(
                pos_x_scaled, pos_y_scaled,
                pos_x_scaled + tile_size_scaled, pos_y_scaled + tile_size_scaled,
                fill=tile.color,
                outline=tile.color,
                stipple='gray50',
                tags="highlight"
            )

            if Tile(x - 1, y) not in self.selected_tiles:
                self.canvas.create_line(pos_x_scaled, pos_y_scaled, pos_x_scaled, pos_y_scaled + tile_size_scaled,
                                        fill=color, width=width, tags="highlight")
            else:
                left_tile = self.get_tile_by_coords(x - 1, y)
                if left_tile.color != color:
                    self.canvas.create_line(pos_x_scaled, pos_y_scaled, pos_x_scaled, pos_y_scaled + tile_size_scaled,
                                            fill=color, width=width, tags="highlight")
            if Tile(x + 1, y) not in self.selected_tiles:
                self.canvas.create_line(pos_x_scaled + tile_size_scaled, pos_y_scaled, pos_x_scaled + tile_size_scaled,
                                        pos_y_scaled + tile_size_scaled, fill=color, width=width, tags="highlight")
            else:
                right_tile = self.get_tile_by_coords(x + 1, y)
                if right_tile.color != color:
                    self.canvas.create_line(pos_x_scaled + tile_size_scaled, pos_y_scaled,
                                            pos_x_scaled + tile_size_scaled,
                                            pos_y_scaled + tile_size_scaled, fill=color, width=width, tags="highlight")
            if Tile(x, y - 1) not in self.selected_tiles:
                self.canvas.create_line(pos_x_scaled, pos_y_scaled, pos_x_scaled + tile_size_scaled, pos_y_scaled,
                                        fill=color, width=width, tags="highlight")
            else:
                bottom_tile = self.get_tile_by_coords(x, y - 1)
                if bottom_tile.color != color:
                    self.canvas.create_line(pos_x_scaled, pos_y_scaled, pos_x_scaled + tile_size_scaled, pos_y_scaled,
                                            fill=color, width=width, tags="highlight")
            if Tile(x, y + 1) not in self.selected_tiles:
                self.canvas.create_line(pos_x_scaled, pos_y_scaled + tile_size_scaled, pos_x_scaled + tile_size_scaled,
                                        pos_y_scaled + tile_size_scaled, fill=color, width=width, tags="highlight")
            else:
                top_tile = self.get_tile_by_coords(x, y + 1)
                if top_tile.color != color:
                    self.canvas.create_line(pos_x_scaled, pos_y_scaled + tile_size_scaled,
                                            pos_x_scaled + tile_size_scaled,
                                            pos_y_scaled + tile_size_scaled, fill=color, width=width, tags="highlight")

        self.update_selected_tiles_list()

    def get_tile_by_coords(self, x, y):
        for tile in self.selected_tiles:
            if tile.x == x and tile.y == y:
                return tile
        return None

    def unhighlight_tile(self, x, y):
        self.canvas.delete("highlight")
        for tile in self.selected_tiles:
            self.highlight_tile(tile.x, tile.y)
        self.update_selected_tiles_list()

    def get_checkout_status(self):
        checkout_status = {}
        try:
            opened_files = p4.run("opened", "-a")

            for file in opened_files:
                file_path = file['depotFile']
                user = file['client'].split('_')[0]
                checkout_status[file_path] = user

        except P4Exception as e:
            print(f"Perforce error: {e}")

        return checkout_status

    def refresh_tiles(self):
        p4.client = self.client_entry.get()

        p4.connect()
        checkout_status = self.get_checkout_status()
        p4.disconnect()

        self.clear_selection()

        for file_path, user in checkout_status.items():
            filename = os.path.basename(file_path)
            if filename.startswith("tile_") and filename.endswith(".w2ter"):
                parts = filename.split('_')
                x = int(parts[1])
                y = int(parts[3])
                if user not in self.user_colors:
                    self.user_colors[user] = utils.get_random_color()
                self.selected_tiles.add(Tile(x, y, self.user_colors[user], None))
                self.highlight_tile(x, y, self.user_colors[user])

    def checkout_tiles(self):
        workspace_folder = filedialog.askdirectory(title="Select Perforce Workspace Folder")
        if not workspace_folder:
            return

        p4.client = self.client_entry.get()
        p4.connect()
        for tile in self.selected_tiles:
            if tile.occupied is False:
                tile_path = os.path.join(workspace_folder, f'tile_{tile.x}_x_{tile.y}_res512.w2ter')
                self.perforce_checkout(tile_path)
        p4.disconnect()

    def perforce_checkout(self, file_path):
        try:
            p4.run('edit', file_path)
        except P4Exception as e:
            print(f"Error checking out {e}")


def stitch_tiles(input_folder, output_image_path, tile_size=1024, grid_size=16, border_size=3,
                 border_color=(255, 165, 0), resize_tile_size=256):
    final_image_size = resize_tile_size * grid_size + border_size * (grid_size + 1)
    final_image = Image.new('RGB', (final_image_size, final_image_size), border_color)

    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except IOError:
        font = ImageFont.load_default()

    for y in range(grid_size):
        for x in range(grid_size):
            tile_path = os.path.join(input_folder, f'Tile{x}x{y}.jpg')
            try:
                tile = Image.open(tile_path)
                tile = tile.resize((resize_tile_size, resize_tile_size))

                inverted_y = grid_size - 1 - y
                pos_x = x * (resize_tile_size + border_size) + border_size
                pos_y = inverted_y * (resize_tile_size + border_size) + border_size

                final_image.paste(tile, (pos_x, pos_y))

                draw = ImageDraw.Draw(final_image)
                text = f"({x},{y})"
                text_position = (pos_x + 5, pos_y + 5)
                draw.text(text_position, text, fill="black", font=font)
            except IOError:
                print(f"Error: Unable to open or paste tile {tile_path}")

    try:
        final_image.save(output_image_path)
        print(f"Final image saved to {output_image_path}")
    except IOError:
        print(f"Error: Unable to save final image to {output_image_path}")


if __name__ == "__main__":
    input_folder = "D:\paf\minimap\kaer_morhen\exterior\Full"
    output_image_path = "stitched_tiles.png"
    stitch_tiles(input_folder, output_image_path)
    #
    # root = tk.Tk()
    # app = TileSelector(root, output_image_path)
    # root.mainloop()
