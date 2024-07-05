from models.map import MapData


class Level:
    def __init__(self, name, map_image_path, map_data: MapData, path, dlc):
        self.name = name
        self.map_image_path = map_image_path
        self.map_data = map_data
        self.path = path
        self.dlc = dlc

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        formatted_name = self.name.replace('_', ' ').title()

        return formatted_name + (' | DLC' if self.dlc else '')