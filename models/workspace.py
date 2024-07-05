
class Workspace:
    def __init__(self, name, folder, user):
        self.name = name
        self.folder = folder
        self.user = user

    def __repr__(self):
        return f'Название: {self.name} | Папка: {self.folder}'

    def __eq__(self, other):
        return self.name == other.name