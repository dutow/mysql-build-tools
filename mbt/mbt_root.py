
from os import getcwd, pardir
from os.path import isfile, join, abspath
from errno import ENOENT


class MbtRoot:
    def __init__(self, config_location=None):
        """Tries to find the root directory of the Mbt workspace.

        The workspace root is defined by the existence of the
        mbt-config.py config file.

        By default, Mbt searches for this file starting from the
        bcurrent working directory upwards, but this behavior can be
        customized by providing a custom location as the constructor
        parameter.

        Throws an IOExcpetion on failure.
        """
        self.config_location = (config_location
                                or MbtRoot.lookup_config_location(getcwd()))

        if not MbtRoot.validate_config_location(self.config_location):
            raise IOError(ENOENT,
                          "No config file in directory",
                          str(self.config_location))

    def root_dir(self):
        return self.config_location

    def config_file(self):
        return join(self.config_location, "mbt_config.py")

    @staticmethod
    def validate_config_location(loc):
        return loc and isfile(join(loc, "mbt_config.py"))

    @staticmethod
    def lookup_config_location(starting_dir):
        abs_path = abspath(starting_dir)
        while abs_path:
            if MbtRoot.validate_config_location(abs_path):
                return abs_path

            parent = abspath(join(abs_path, pardir))
            abs_path = parent if (abs_path != parent) else None

        return None
