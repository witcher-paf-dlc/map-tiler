import os
import requests
import tkinter as tk
from tkinter import messagebox
import webbrowser

colors = [
    "#EF5350", "#0bb4ff", "#9b19f5", "#4CAF50",
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

def get_latest_release_info():
    url = f"https://api.github.com/repos/witcher-paf-dlc/map-tiler/releases"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    print(response.json())
    return response.json()
