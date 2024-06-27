import tkinter as tk
import numpy as np

from PIL import Image, ImageTk
from PIL.Image import Resampling, Transform

import constants
from tile import Tile


class PanZoomCanvas:
    def __init__(self, placeholder, canvas_w, canvas_h, image, overview_frame):
        self.overview_photo = None
        self.overview_frame = overview_frame
        self.master = placeholder
        self.pil_image = None
        self.zoom_cycle = 0
        self.create_widget(canvas_w, canvas_h)
        self.reset_transform()

        self.selected_tiles = set()

        self.set_image(image)

    def create_widget(self, width, height):
        self.canvas = tk.Canvas(self.master, background="black", width=width, height=height)
        self.canvas.pack(side=tk.LEFT)

        self.overview_canvas = tk.Canvas(self.overview_frame, background="grey", width=200, height=200)
        self.overview_canvas.pack(fill=tk.X)

        self.canvas.bind("<Button-3>", self.mouse_down_left)
        self.canvas.bind("<B3-Motion>", self.mouse_move_left)
        self.canvas.bind("<Double-Button-1>", self.mouse_double_click_left)
        self.canvas.bind("<MouseWheel>", self.mouse_wheel)

    def set_image(self, filename):
        if not filename:
            return
        self.pil_image = Image.open(filename)
        self.zoom_fit(self.pil_image.width / 2, self.pil_image.height / 2)
        self.draw_image(self.pil_image)

    def mouse_down_left(self, event):
        self.__old_event = event

    def mouse_move_left(self, event):
        if self.pil_image is None:
            return

        self.translate(event.x - self.__old_event.x, event.y - self.__old_event.y)
        self.redraw_image()
        self.__old_event = event

    def mouse_double_click_left(self, event):
        if self.pil_image == None:
            return

        self.zoom_fit(self.pil_image.width / 2, self.pil_image.height / 2)
        self.redraw_image()

    def mouse_wheel(self, event):
        if self.pil_image is None:
            return

        if event.delta < 0:
            if self.zoom_cycle <= 0:
                return
            self.scale_at(0.8, event.x, event.y)
            self.zoom_cycle -= 1
        else:
            if self.mat_affine[0, 0] >= 1.0:
                return
            self.scale_at(1.25, event.x, event.y)
            self.zoom_cycle += 1

        self.redraw_image()

    def reset_transform(self):
        self.mat_affine = np.eye(3)

    def translate(self, offset_x, offset_y, zoom=False):
        mat = np.eye(3)
        mat[0, 2] = float(offset_x)
        mat[1, 2] = float(offset_y)

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        scale = self.mat_affine[0, 0]
        max_y = scale * 4147
        max_x = scale * 4147
        self.mat_affine = np.dot(mat, self.mat_affine)

        if not zoom:
            if abs(self.mat_affine[0, 2]) > abs(max_x - canvas_width):
                self.mat_affine[0, 2] = -(max_x - canvas_width)
            if abs(self.mat_affine[1, 2]) > abs(max_y - canvas_height):
                self.mat_affine[1, 2] = -(max_y - canvas_height)

        if self.mat_affine[0, 2] > 0.0:
            self.mat_affine[0, 2] = 0.0
        if self.mat_affine[1, 2] > 0.0:
            self.mat_affine[1, 2] = 0.0

    def scale(self, scale: float):
        mat = np.eye(3)

        mat[0, 0] = scale
        mat[1, 1] = scale

        new_mat_affine = np.dot(mat, self.mat_affine)

        if new_mat_affine[0, 0] > 1.0:
            new_mat_affine[0, 0] = 1.0
            new_mat_affine[1, 1] = 1.0

        self.mat_affine = new_mat_affine

    def scale_at(self, scale: float, cx: float, cy: float):
        self.translate(-cx, -cy, True)
        self.scale(scale)
        self.translate(cx, cy)

    def zoom_fit(self, image_width, image_height):
        self.master.update()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if (image_width * image_height <= 0) or (canvas_width * canvas_height <= 0):
            return

        self.reset_transform()

        scale = 0
        offsetx = 0.0
        offsety = 0.0
        if (canvas_width * image_height) > (image_width * canvas_height):
            scale = canvas_height / image_height
            offsetx = (canvas_width - image_width * scale) / 2
        else:
            scale = canvas_width / image_width
            offsety = (canvas_height - image_height * scale) / 2

        self.scale(scale)
        self.translate(-(4147 / 4) * scale, -(4147 / 4) * scale)
        self.zoom_cycle = 0

    def to_image_point(self, x, y):
        if self.pil_image == None:
            return []

        mat_inv = np.linalg.inv(self.mat_affine)
        image_point = np.dot(mat_inv, (x, y, 1.))
        if image_point[0] < 0 or image_point[1] < 0 or image_point[0] > self.pil_image.width or image_point[1] > self.pil_image.height:
            return []

        return image_point

    def draw_image(self, pil_image):

        if pil_image == None:
            return

        self.pil_image = pil_image

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        mat_inv = np.linalg.inv(self.mat_affine)

        affine_inv = (
            mat_inv[0, 0], mat_inv[0, 1], mat_inv[0, 2],
            mat_inv[1, 0], mat_inv[1, 1], mat_inv[1, 2]
        )

        dst = self.pil_image.transform(
            (canvas_width, canvas_height),
            Transform.AFFINE,
            affine_inv,
            Resampling.BICUBIC
        )

        im = ImageTk.PhotoImage(image=dst)

        self.canvas.delete("highlight")

        self.canvas.create_image(
            0, 0,
            anchor='nw',
            image=im
        )
        self.image = im

        tile_size = 256
        border_size = 3
        width = 3
        border_pad = 6
        pad = 4

        tile_size_scaled = ((tile_size - 1) * self.mat_affine[0, 0]) - (border_pad * 2)
        tile_box_size_scaled = ((tile_size - 1) * self.mat_affine[0, 0]) - (pad * 2)

        for tile in self.selected_tiles:
            x, y = tile.x, tile.y

            image_x = x * (tile_size + border_size) + border_size
            image_y = y * (tile_size + border_size) + border_size

            canvas_coords = np.dot(self.mat_affine, [image_x, image_y, 1])
            pos_x_scaled, pos_y_scaled = canvas_coords[0] + border_pad, canvas_coords[1] + border_pad
            pos_x_box_scaled, pos_y_box_scaled = canvas_coords[0] + pad, canvas_coords[1] + pad

            color = tile.color

            self.canvas.create_rectangle(
                pos_x_box_scaled, pos_y_box_scaled,
                pos_x_box_scaled + tile_box_size_scaled, pos_y_box_scaled + tile_box_size_scaled,
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

    def redraw_image(self):
        if self.pil_image == None:
            return
        self.draw_image(self.pil_image)
        self.draw_overview_image()

    def get_tile_by_coords(self, x, y):
        for tile in self.selected_tiles:
            if tile.x == x and tile.y == y:
                return tile
        return None

    def draw_overview_image(self):
        if self.pil_image is None:
            return

        if self.overview_photo is None:
            overview_width = self.overview_canvas.winfo_width()
            overview_height = self.overview_canvas.winfo_height()

            self.overview_scale = min(overview_width / self.pil_image.width, overview_height / self.pil_image.height)
            overview_image = self.pil_image.resize(
                (int(self.pil_image.width * self.overview_scale), int(self.pil_image.height * self.overview_scale)),
                Resampling.BICUBIC
            )

            self.overview_photo = ImageTk.PhotoImage(image=overview_image)
            self.overview_canvas.create_image(0, 0, anchor='nw', image=self.overview_photo)

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        mat_inv = np.linalg.inv(self.mat_affine)
        top_left = np.dot(mat_inv, (0, 0, 1))
        bottom_right = np.dot(mat_inv, (canvas_width, canvas_height, 1))

        overview_top_left = (top_left[0] * self.overview_scale, top_left[1] * self.overview_scale)
        overview_bottom_right = (bottom_right[0] * self.overview_scale, bottom_right[1] * self.overview_scale)

        self.overview_canvas.delete('box')

        self.overview_canvas.create_rectangle(
            overview_top_left[0], overview_top_left[1],
            overview_bottom_right[0], overview_bottom_right[1],
            outline='red',
            tags="box"
        )

        self.overview_canvas.delete('highlight')

        tile_size = 256
        for tile in self.selected_tiles:
            overview_tile_x = tile.x * (tile_size + 3) * self.overview_scale + 3
            overview_tile_y = tile.y * (tile_size + 3) * self.overview_scale + 3

            overview_tile_width = tile_size * self.overview_scale - 3
            overview_tile_height = tile_size * self.overview_scale - 3

            self.overview_canvas.create_rectangle(
                overview_tile_x, overview_tile_y,
                overview_tile_x + overview_tile_width, overview_tile_y + overview_tile_height,
                outline=tile.color,

                tags="highlight"
            )
