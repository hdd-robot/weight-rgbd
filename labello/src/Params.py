import os
import configparser


class Params:
    """ Params  """
    def __init__(self):
        self.config = None
        self.read_config_file()
        self.base_path = self.config['GLOBAL']['base_path']
        self.image_path = self.base_path + "img/"
        self.point_cloud_path = self.base_path + "pcd/"
        self.spectro_path = self.base_path + "spectro/"
        self.graph_path = self.base_path + "graph/"
        self.check_paths()

    def get_spectro_ip(self):
        return self.config['SPECTRO']['ip']

    def get_spectro_port(self):
        return int(self.config['SPECTRO']['port'])

    def read_config_file(self):
        self.config = configparser.ConfigParser()
        self.config.read('params.conf')

    def get_image_path(self):
        return self.image_path

    def get_cloud_path(self):
        return self.point_cloud_path

    def get_spectro_path(self):
        return self.spectro_path

    def get_graph_path(self):
        return self.graph_path

    def check_paths(self):
        if os.path.exists(self.base_path) is False:
            os.makedirs(self.base_path)

        if os.path.exists(self.image_path) is False:
            os.makedirs(self.image_path)

        if os.path.exists(self.point_cloud_path) is False:
            os.makedirs(self.point_cloud_path)

        if os.path.exists(self.spectro_path) is False:
            os.makedirs(self.spectro_path)

        if os.path.exists(self.graph_path) is False:
            os.makedirs(self.graph_path)
