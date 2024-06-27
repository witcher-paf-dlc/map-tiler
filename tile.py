from constants import TILE_COLOR


class Tile:
    def __init__(self, x, y, color=TILE_COLOR, checkout_info=None):
        self.x = x
        self.y = y
        self.color = color
        self.checkout_info = checkout_info

    def __eq__(self, other):
        return isinstance(other, Tile) and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __lt__(self, other):
        if self.x == other.x:
            return self.y < other.y
        else:
            return self.x < other.x

    def __repr__(self):
        return f"Tile({self.x}, {self.y}, {self.color}"


class CheckoutInfo:
    def __init__(self, workspace):
        self.workspace = workspace

    def get_user(self):
        return self.workspace.split('_')[0]
