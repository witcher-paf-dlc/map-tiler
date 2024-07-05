import os
from P4 import P4, P4Exception
from components.settings import GlobalSettings
from models.workspace import Workspace

class P4Manager:
    def __init__(self):
        self.p4 = P4()
        self.p4.port = "ssl:18.198.116.34:1666"
        self.settings = GlobalSettings

    def set_client(self, workspace):
        if workspace is not None:
            self.p4.client = workspace.name
        else:
            self.p4.client = ''

    def connect_and_execute(self, func, *args, **kwargs):
        try:
            self.p4.connect()
            return func(*args, **kwargs)
        except P4Exception as e:
            print(e)
        finally:
            self.p4.disconnect()

    def checkout_tiles(self, tiles, level):
        def fetch(tile_paths):
            return self.p4.run('edit', *tile_paths)

        tile_paths = [os.path.join(level.path, 'terrain_tiles', f'tile_{tile.x}_x_{tile.y}_res{level.map_data.resolution}.w2ter') for tile in
                      tiles]

        self.connect_and_execute(lambda: fetch(tile_paths))

    def uncheckout_tiles(self, tiles, level):
        def fetch(tile_paths):
            return self.p4.run('revert', '-a', *tile_paths)

        tile_paths = [os.path.join(level.path, 'terrain_tiles', f'tile_{tile.x}_x_{tile.y}_res{level.map_data.resolution}.w2ter') for tile in
                      tiles]

        self.connect_and_execute(lambda: fetch(tile_paths))

    def load_tiles(self, level):
        def fetch():
            return self.p4.run('opened', '-a')

        if level is None:
            return []

        tile_files = self.connect_and_execute(fetch)

        result = []

        for file in tile_files:
            depot_file = file['depotFile']

            depot = self.settings.get_setting('depot')

            level_path = f'//{depot}/development/workspace/levels/{level.name}'
            dlc_level_path = f'//{depot}/development/workspace/dlc/{depot}/data/levels/{level.name}'

            if not depot_file.startswith(level_path) and not depot_file.startswith(dlc_level_path):
                continue

            file_name = os.path.basename(depot_file)
            if file_name.startswith("tile_") and file_name.endswith(".w2ter"):
                parts = file_name.split('_')
                x = int(parts[1])
                y = int(parts[3])
                workspace = file['client']

                user_entry = next((item for item in result if item['workspace'] == workspace), None)

                if user_entry:
                    user_entry['tiles'].append({'x': x, 'y': y})
                else:
                    new_user_entry = {'workspace': workspace, 'tiles': [{'x': x, 'y': y}]}
                    result.append(new_user_entry)

        return result

    def load_workspaces(self):
        def fetch_workspaces():
            user_name = self.settings.get_setting('user_name')
            stream = '//' + self.settings.get_setting('depot') + '/development'
            return self.p4.run('clients', '-e', user_name + '_*', '-S', stream)

        workspaces = self.connect_and_execute(fetch_workspaces)

        extracted_workspaces = [
            Workspace(workspace['client'], workspace['Root'], workspace['client'].split('_')[0])
            for workspace in workspaces
        ]

        return extracted_workspaces
