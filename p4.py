import os

from P4 import P4, P4Exception

from settings import GlobalSettings


class P4Manager:
    def __init__(self):
        self.p4 = P4()
        self.p4.port = "ssl:18.198.116.34:1666"
        self.p4.user = 'perforce'
        self.settings = GlobalSettings

    def set_client(self, client):
        self.p4.client = client

    def connect_and_execute(self, func, *args, **kwargs):
        try:
            self.p4.connect()
            return func(*args, **kwargs)
        except P4Exception as e:
            print(e)
        finally:
            self.p4.disconnect()

    def checkout_tiles(self, tiles, tiles_folder):
        def fetch(tile_path):
            return self.p4.run('edit', tile_path)

        for tile in tiles:
            tile_path = os.path.join(tiles_folder, f'tile_{tile.x}_x_{tile.y}_res512.w2ter')
            tile_path = tile_path.replace('\\', '/')
            self.connect_and_execute(lambda: fetch(tile_path))

    def load_tiles(self):
        def fetch():
            return self.p4.run('opened', '-a')

        tile_files = self.connect_and_execute(fetch)
        result = []

        for file in tile_files:
            depot_file = file['depotFile']

            if depot_file.startswith('//paf_test'):
                break

            file_name = os.path.basename(depot_file)
            if file_name.startswith("tile_") and file_name.endswith(".w2ter"):
                parts = file_name.split('_')
                x = int(parts[1])
                y = int(parts[3])
                user = file['client'].split('_')[0]

                user_entry = next((item for item in result if item['user'] == user), None)

                if user_entry:
                    user_entry['tiles'].append({'x': x, 'y': y})
                else:
                    new_user_entry = {'user': user, 'tiles': [{'x': x, 'y': y}]}
                    result.append(new_user_entry)

        return result

    def load_workspaces(self):
        def fetch_workspaces():
            user_name = self.settings.get_setting('user_name')
            return self.p4.run('clients', '-e', user_name + '_*')

        workspaces = self.connect_and_execute(fetch_workspaces)

        print(workspaces)

        extracted_workspaces = [
            {'client': workspace['client'], 'root': workspace['Root']}
            for workspace in workspaces
        ]

        return extracted_workspaces
