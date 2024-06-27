import math
import warnings
import tkinter as tk

from tkinter import ttk
from PIL import Image, ImageTk
from PIL.Image import Resampling

import constants
from tile import Tile


class CanvasImage:
    def __init__(self, placeholder, path):
        self.imscale = 1
        self.__delta = 1.1
        self.selected_tiles = set()
        self.__filter = Resampling.LANCZOS  # could be: NEAREST, BILINEAR, BICUBIC and ANTIALIAS
        self.__previous_state = 0  # previous state of the keyboard
        self.path = path  # path to the image, should be public for outer classes
        # Create ImageFrame in placeholder widget
        self.__imframe = ttk.Frame(placeholder)  # placeholder of the ImageFrame object
        # Vertical and horizontal scrollbars for canvas
        # Create canvas and bind it with scrollbars. Public for outer classes
        self.canvas = tk.Canvas(self.__imframe, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait till canvas is created
        # Bind events to the Canvas
        self.canvas.bind('<Configure>', lambda event: self.__show_image())  # canvas is resized
        self.canvas.bind('<ButtonPress-1>', self.__move_from)  # remember canvas position
        self.canvas.bind('<B1-Motion>', self.__move_to)  # move canvas to the new position
        self.canvas.bind('<MouseWheel>', self.__wheel)  # zoom for Windows and MacOS, but not Linux
        # Handle keystrokes in idle mode, because program slows down on a weak computers,
        # when too many key stroke events in the same time
        self.canvas.bind('<Key>', lambda event: self.canvas.after_idle(self.__keystroke, event))
        # Decide if this image huge or not
        self.__huge = False  # huge or not
        self.__huge_size = 14000  # define size of the huge image
        self.__band_width = 1024  # width of the tile band
        Image.MAX_IMAGE_PIXELS = None  # suppress DecompressionBombError for the big image
        with warnings.catch_warnings():  # suppress DecompressionBombWarning
            warnings.simplefilter('ignore')
            self.__image = Image.open(self.path)  # open image, but down't load it
        self.imwidth, self.imheight = self.__image.size  # public for outer classes
        if self.imwidth * self.imheight > self.__huge_size * self.__huge_size and \
                self.__image.tile[0][0] == 'raw':  # only raw images could be tiled
            self.__huge = True  # image is huge
            self.__offset = self.__image.tile[0][2]  # initial tile offset
            self.__tile = [self.__image.tile[0][0],  # it have to be 'raw'
                           [0, 0, self.imwidth, 0],  # tile extent (a rectangle)
                           self.__offset,
                           self.__image.tile[0][3]]  # list of arguments to the decoder
        self.__min_side = min(self.imwidth, self.imheight)  # get the smaller image side
        # Create image pyramid
        self.__pyramid = [self.smaller()] if self.__huge else [Image.open(self.path)]
        # Set ratio coefficient for image pyramid
        self.__ratio = max(self.imwidth, self.imheight) / self.__huge_size if self.__huge else 1.0
        self.__curr_img = 0  # current image from the pyramid
        self.__scale = self.imscale * self.__ratio  # image pyramide scale
        self.__reduction = 2  # reduction degree of image pyramid
        w, h = self.__pyramid[-1].size
        while w > 512 and h > 512:  # top pyramid image is around 512 pixels in size
            w /= self.__reduction  # divide on reduction degree
            h /= self.__reduction  # divide on reduction degree
            self.__pyramid.append(self.__pyramid[-1].resize((int(w), int(h)), self.__filter))
        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle((0, 0, self.imwidth, self.imheight), width=0)
        self.__show_image()  # show image on the canvas
        self.canvas.focus_set()  # set focus on the canvas

    def smaller(self):
        w1, h1 = float(self.imwidth), float(self.imheight)
        w2, h2 = float(self.__huge_size), float(self.__huge_size)
        aspect_ratio1 = w1 / h1
        aspect_ratio2 = w2 / h2
        if aspect_ratio1 == aspect_ratio2:
            image = Image.new('RGB', (int(w2), int(h2)))
            k = h2 / h1
            w = int(w2)
        elif aspect_ratio1 > aspect_ratio2:
            image = Image.new('RGB', (int(w2), int(w2 / aspect_ratio1)))
            k = h2 / w1
            w = int(w2)
        else:
            image = Image.new('RGB', (int(h2 * aspect_ratio1), int(h2)))
            k = h2 / h1  # compression ratio
            w = int(h2 * aspect_ratio1)  # band length
        i, j, n = 0, 1, round(0.5 + self.imheight / self.__band_width)
        while i < self.imheight:
            print('\rOpening image: {j} from {n}'.format(j=j, n=n), end='')
            band = min(self.__band_width, self.imheight - i)
            self.__tile[1][3] = band
            self.__tile[2] = self.__offset + self.imwidth * i * 3
            self.__image.close()
            self.__image = Image.open(self.path)
            self.__image.size = (self.imwidth, band)
            self.__image.tile = [self.__tile]
            cropped = self.__image.crop((0, 0, self.imwidth, band))
            image.paste(cropped.resize((w, int(band * k) + 1), self.__filter), (0, int(i * k)))
            i += band
            j += 1
        return image

    def grid(self, **kw):
        self.__imframe.rowconfigure(0, weight=1)
        self.__imframe.columnconfigure(0, weight=1)
        self.__imframe.grid(**kw)
        self.__imframe.grid(sticky='nsew')

    def __show_image(self):
        self.canvas.delete("highlight")

        for tile in self.selected_tiles:
            x, y = tile.x, tile.y

            width = 3

            pos_x = x * (constants.TILE_SIZE + constants.TILE_BORDER_SIZE) + constants.TILE_BORDER_SIZE
            pos_y = y * (constants.TILE_SIZE + constants.TILE_BORDER_SIZE) + constants.TILE_BORDER_SIZE
            pos_x_scaled = int(pos_x * self.imscale)
            pos_y_scaled = int(pos_y * self.imscale)
            tile_size_scaled = int(constants.TILE_SIZE * self.imscale)

            color = tile.color

            self.canvas.create_rectangle(
                pos_x_scaled, pos_y_scaled,
                pos_x_scaled + tile_size_scaled, pos_y_scaled + tile_size_scaled,
                fill=tile.color,
                outline=tile.color,
                stipple='gray50',
                tags="highlight"
            )

        box_image_init = self.canvas.coords(self.container)

        init_x = box_image_init[0] + 0
        init_y = box_image_init[1] + 0

        box_canvas = [self.canvas.canvasx(0),
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height())]

        self.canvas.coords(self.container, 0, 0, box_image_init[2] - init_x,
                           box_image_init[3] - init_y)

        box_image = self.canvas.coords(self.container)

        box_img_int = tuple(map(int, box_image))
        box_scroll = [0, 0, box_img_int[2], box_img_int[3]]

        if init_x != 0:
            x_dif = abs(box_canvas[2] - box_scroll[2])
            y_dif = abs(box_canvas[3] - box_scroll[3])
            box_canvas[0] -= x_dif
            box_canvas[1] -= y_dif

        self.canvas.configure(scrollregion=tuple(map(int, box_scroll)))

        x1 = max(box_canvas[0] - box_image[0], 0)
        y1 = max(box_canvas[1] - box_image[1], 0)
        x2 = min(box_canvas[2], box_image[2]) - box_image[0]
        y2 = min(box_canvas[3], box_image[3]) - box_image[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:
            if self.__huge and self.__curr_img < 0:
                h = int((y2 - y1) / self.imscale)
                self.__tile[1][3] = h
                self.__tile[2] = self.__offset + self.imwidth * int(y1 / self.imscale) * 3
                self.__image.close()
                self.__image = Image.open(self.path)
                self.__image.size = (self.imwidth, h)
                self.__image.tile = [self.__tile]
                image = self.__image.crop((int(x1 / self.imscale), 0, int(x2 / self.imscale), h))
            else:
                image = self.__pyramid[max(0, self.__curr_img)].crop(
                    (int(x1 / self.__scale), int(y1 / self.__scale),
                     int(x2 / self.__scale), int(y2 / self.__scale)))

            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1)), self.__filter))

            self.imageid = self.canvas.create_image(max(box_canvas[0], box_img_int[0]),
                                               max(box_canvas[1], box_img_int[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(self.imageid)
            self.canvas.imagetk = imagetk

    def __move_from(self, event):
        self.canvas.scan_mark(event.x, event.y)
        canvas_x, canvas_y = event.x, event.y

        box_image = self.canvas.coords(self.container)
        box_canvas = (self.canvas.canvasx(0),
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))

        x_offset = (box_canvas[0] - box_image[0]) / self.imscale
        y_offset = (box_canvas[1] - box_image[1]) / self.imscale

        orig_x = (canvas_x - box_image[0]) / self.imscale + x_offset
        orig_y = (canvas_y - box_image[1]) / self.imscale + y_offset

        x = int(orig_x // (constants.TILE_SIZE + constants.TILE_BORDER_SIZE))
        y = int(orig_y // (constants.TILE_SIZE + constants.TILE_BORDER_SIZE))

        tile = Tile(x, y)
        self.selected_tiles.add(tile)

        self.__show_image()

    def __move_to(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.__show_image()

    def __scroll_x(self, *args, **kwargs):
        """ Scroll canvas horizontally and redraw the image """
        self.canvas.xview(*args)  # scroll horizontally
        self.__show_image()  # redraw the image

    # noinspection PyUnusedLocal
    def __scroll_y(self, *args, **kwargs):
        """ Scroll canvas vertically and redraw the image """
        self.canvas.yview(*args)  # scroll vertically
        self.__show_image()  # redraw the image

    def outside(self, x, y):
        bbox = self.canvas.coords(self.container)
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            return False
        else:
            return True

    def __wheel(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasx(event.y)

        print(f'x: {x}, y:{y}')

        if self.outside(x, y): return
        scale = 1.0

        min_scale_factor = max(700 / self.imwidth, 700 / self.imheight)

        print(min_scale_factor)

        if event.num == 5 or event.delta == -120:  # scroll down, smaller
            if self.imscale <= min_scale_factor: return
            self.imscale /= self.__delta
            scale /= self.__delta
        if event.num == 4 or event.delta == 120:  # scroll up, bigger
            if self.imscale >= 1: return
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height()) >> 1
            if i < self.imscale: return
            self.imscale *= self.__delta
            scale *= self.__delta
        k = self.imscale * self.__ratio
        self.__curr_img = min((-1) * int(math.log(k, self.__reduction)), len(self.__pyramid) - 1)
        self.__scale = k * math.pow(self.__reduction, max(0, self.__curr_img))
        self.canvas.scale('all', x, y, scale, scale)
        self.__show_image()

    def __keystroke(self, event):
        if event.state - self.__previous_state == 4:
            pass
        else:
            self.__previous_state = event.state
            if event.keycode in [68, 39, 102]:
                self.__scroll_x('scroll', 1, 'unit', event=event)
            elif event.keycode in [65, 37, 100]:
                self.__scroll_x('scroll', -1, 'unit', event=event)
            elif event.keycode in [87, 38, 104]:
                self.__scroll_y('scroll', -1, 'unit', event=event)
            elif event.keycode in [83, 40, 98]:
                self.__scroll_y('scroll', 1, 'unit', event=event)

    def crop(self, bbox):
        if self.__huge:
            band = bbox[3] - bbox[1]
            self.__tile[1][3] = band
            self.__tile[2] = self.__offset + self.imwidth * bbox[1] * 3
            self.__image.close()
            self.__image = Image.open(self.path)
            self.__image.size = (self.imwidth, band)
            self.__image.tile = [self.__tile]
            return self.__image.crop((bbox[0], 0, bbox[2], band))
        else:
            return self.__pyramid[0].crop(bbox)

    def destroy(self):
        self.__image.close()
        map(lambda i: i.close, self.__pyramid)
        del self.__pyramid[:]
        del self.__pyramid
        self.canvas.destroy()
        self.__imframe.destroy()
