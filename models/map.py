class MapData:
    def __init__(self, grid_size, tile_size, border_size, resolution):
        self.grid_size = grid_size
        self.tile_size = tile_size
        self.border_size = border_size
        self.resolution = resolution

    @classmethod
    def from_json(cls, json_data):
        return cls(
            grid_size=json_data.get('grid_size', 16),
            tile_size=json_data.get('tile_size', 256),
            border_size=json_data.get('border_size', 0),
            resolution=json_data.get('resolution', 256)
        )

    def __repr__(self):
        return f"MapData(grid_size={self.grid_size}, tile_size={self.tile_size}, border_size={self.border_size})"