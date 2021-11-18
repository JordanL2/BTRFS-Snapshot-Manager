#!/usr/bin/python3

from btrfssnapshotmanager.common import *
from btrfssnapshotmanager.periods import *

from pathlib import PosixPath
import yaml


class Config():

    config_file = PosixPath('/etc/btrfs-snapshot-manager/config.yml')

    def __init__(self):
        self.load_config()

    def load_config(self):
        if not self.config_file.is_file():
            raise SnapshotException("No file found at: {0}".format(self.filepath))
        with open(self.config_file, 'r') as fh:
            config = yaml.load(fh, Loader=yaml.CLoader)

        # Schedules
        self.schedules = {}
        for subvol in config:
            schedule = {}
            if 'retention' in config[subvol]:
                for period in PERIODS:
                    if period.name in config[subvol]['retention']:
                        schedule[period] = int(config[subvol]['retention'][period.name])
            self.schedules[subvol] = schedule
