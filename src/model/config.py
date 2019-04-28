import configparser
import appdirs
from os import path, makedirs

user_config_dir = appdirs.user_config_dir('sequins')
user_config_path = path.join(user_config_dir, 'user_config.ini')


class UserConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()
        makedirs(user_config_dir, exist_ok=True)

    def load(self):
        self.config.read(user_config_path)

    def save(self):
        with open(user_config_path, 'w') as user_config_file:
            self.config.write(user_config_file)

    def get_input(self):
        return self._get_or_create_section('input')

    def set_input(self, input_config):
        self.config['input'] = input_config

    def get_output(self):
        return self._get_or_create_section('output')

    def set_output(self, output_config):
        self.config['output'] = output_config

    def _get_or_create_section(self, section):
        if not self.config.has_section(section):
            self.config[section] = {}
        return self.config[section]
