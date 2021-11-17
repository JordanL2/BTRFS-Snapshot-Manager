#!/usr/bin/python3

from btrfssnapshotmanager.config import *
from btrfssnapshotmanager.snapshots import *


class ScheduleManager():

    def __init__(self):
        self.config = Config()
        self.schedulers = {}
        for subvol in self.config.schedules:
            self.schedulers[subvol] = SubvolumeScheduleManager(self, subvol)


class SubvolumeScheduleManager():

    def __init__(self, schedule_manager, subvol):
        self.schedule_manager = schedule_manager
        self.subvol = Subvolume(subvol)
        self.config = self.schedule_manager.config.schedules[subvol]

    def last_run(self, period):
        if period not in self.config:
            raise SnapshotException("No {0} snapshot schedule set for subvolume {1}".format(period.name, self.subvol.path))
        snapshots = self.subvol.search_snapshots(periods=[period])
        if len(snapshots) == 0:
            return None
        else:
            return snapshots[0].date
