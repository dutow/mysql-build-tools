
class MbtConfigurator:
    def __init__(self):
        self.username = None
        self.user_email = None
        self.remotes = {}
        self.series = []
        self.build_configs = {}

    def add_remote(self, name, url):
        self.remotes[name] = url

    def add_series(self, ver):
        self.series.append(ver)

    def set_user(self, name, email):
        self.user_name = name
        self.user_email = email

    def add_build_config(self, name, image, environment={}, config={}):
        self.build_configs[name] = {
                "image": image,
                "environment": environment,
                "config": config
                }

    def has_series(self, version):
        return version in self.series

    def has_build_config(self, name):
        return name in self.build_configs
