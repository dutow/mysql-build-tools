
from os.path import relpath, commonprefix
from os import sep
from .mbt_error import MbtError


class DirectoryContext:

    def __init__(self, config, root_directory, current_directory):
        if not root_directory.endswith("/"):
            root_directory += "/"

        if not current_directory.endswith("/"):
            current_directory += "/"

        common = commonprefix([current_directory, root_directory])
        if common != root_directory:
            raise MbtError("Not within an MBT workspace")

        parts = relpath(current_directory, root_directory).split(sep)

        self.topic = None
        self.series = None
        self.variant = None
        self.installation = None

        if len(parts) >= 2 and parts[0] == "topics":
            # topics/<topicname>/<series>[-<variant>]
            self.topic = parts[1]

        if len(parts) >= 3:
            subparts = parts[2].split("-", 1)

            if config.has_series(subparts[0]):
                self.series = subparts[0]

            if self.series is not None and len(subparts) == 2:
                instparts = subparts[1].split("-inst-", 1)
                self.variant = instparts[0]

                if not config.has_build_config(self.variant):
                    raise MbtError("Unknown build config: " + self.variant)

                if len(instparts) == 2:
                    self.installation = instparts[1]
