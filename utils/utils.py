import requests

colors = [
    "#9b19f5", "#4CAF50",
    "#FFEB3B", "#ffa300", "#dc0ab4", "#18FFFF",
    "#FF6F00", "#00796B", "#303F9F", "#76FF03",
]

def color_generator(colors):
    while True:
        for color in colors:
            yield color


color_gen = color_generator(colors)

def get_random_color():
    return next(color_gen)

def get_user_color():
    return '#0bb4ff'

