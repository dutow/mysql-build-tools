
from argparse import ArgumentParser


class MbtParams:

    def __init__(self, config, context, prog_name="mbt"):
        self.config = config
        self.context = context
        self.parser = ArgumentParser(prog=prog_name)
        self.requires_topic = False
        self.requires_series = False
        self.requires_variant = False
        self.requires_installation = False

    def add_topic_arg(self):
        if self.requires_topic:
            return
        self.requires_topic = True
        self.parser.add_argument("-t", "--topic",
                                 required=(self.context.topic is None),
                                 help="Description of the changes, part of"
                                 " the feature branch name",
                                 default=self.context.topic
                                 )

    def add_series_arg(self):
        if self.requires_series:
            return
        self.requires_series = True
        self.parser.add_argument("-s", "--series",

                                 required=(self.context.series is None),
                                 help="Release series to work on",
                                 choices=self.config.series,
                                 default=self.context.series
                                 )

    def add_variant_arg(self):
        if self.requires_variant:
            return
        self.requires_variant = True
        self.parser.add_argument("-v", "--variant",
                                 required=(self.context.variant is None),
                                 help="Build variant to use",
                                 choices=self.config.build_configs.keys(),
                                 default=self.context.variant
                                 )

    def add_installation_arg(self):
        if self.requires_installation:
            return
        self.requires_installation = True

        self.add_topic_arg()
        self.add_series_arg()
        self.add_variant_arg()

        self.parser.add_argument("-i", "--installation",
                                 required=(self.context.installation is None),
                                 help="Tag of the installation",
                                 default=self.context.installation
                                 )

    def parse(self, args):
        self.results = self.parser.parse_args(args)
        return self.results
