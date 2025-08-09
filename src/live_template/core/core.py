import logging
from importlib.abc import Traversable
from importlib.resources import files


class Config:
    def __init__(self, config_dir: Traversable, filename: str):
        self._path = config_dir.joinpath(filename)
        self._data = dict()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)


logging.basicConfig(level=logging.INFO)
log = logging.getLogger("live_template")
log.setLevel(logging.INFO)
package_root = files("live_template")
config_dir = package_root.joinpath("config")
config = Config(config_dir, "config.json")
