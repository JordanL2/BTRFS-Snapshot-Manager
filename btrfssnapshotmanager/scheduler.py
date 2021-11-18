#!/usr/bin/python3

from btrfssnapshotmanager.common import *
from btrfssnapshotmanager.config import *
from btrfssnapshotmanager.snapshots import *


class ScheduleManager():

    def __init__(self):
        self.config = Config()
        self.schedulers = {}
        for subvol in self.config.schedules:
            self.schedulers[subvol] = SubvolumeScheduleManager(self, subvol)

    def execute(self):
        for subvol, scheduler in self.schedulers.items():
            info("Subvolume:", subvol)
            periods = []
            for period, count in scheduler.config.items():
                if scheduler.should_run(period):
                    info("Period reached:", period.name)
                    periods.append(period)
            if len(periods) > 0:
                scheduler.run(periods)
            else:
                info("No periods reached")
            info()


class SubvolumeScheduleManager():

    def __init__(self, schedule_manager, subvol):
        self.schedule_manager = schedule_manager
        self.subvol = Subvolume(subvol)
        if not self.subvol.has_snapshots():
            self.subvol.init_snapshots()
        self.config = self.schedule_manager.config.schedules[subvol]
        self.backups = self.schedule_manager.config.backups[subvol]

    def last_run(self, period):
        if period not in self.config:
            raise SnapshotException("No {0} snapshot schedule set for subvolume {1}".format(period.name, self.subvol.path))
        snapshots = self.subvol.search_snapshots(periods=[period])
        if len(snapshots) == 0:
            return None
        else:
            return snapshots[-1].date

    def next_run(self, period):
        last_run = self.last_run(period)
        if last_run is None:
            return None
        else:
            return period.next_period(last_run)

    def should_run(self, period):
        now = datetime.now()
        next_run = self.next_run(period)
        if next_run is None or next_run <= now:
            return True
        return False

    def run(self, periods, auto_cleanup=True):
        info("Creating snapshot for:", ', '.join([p.name for p in periods]))
        self.subvol.create_snapshot(periods=periods)

        if auto_cleanup:
            self.cleanup()

    def cleanup(self):
        dont_delete = set()
        for period in PERIODS:
            max_snapshots = 0
            if period in self.config:
                max_snapshots = self.config[period]
            snapshots = self.subvol.search_snapshots(periods=[period])
            for snapshot in snapshots[max(0, len(snapshots) - max_snapshots) : ]:
                dont_delete.add(snapshot)
        snapshots = self.subvol.search_snapshots(periods=PERIODS)
        for snapshot in snapshots:
            if snapshot not in dont_delete:
                info("Deleting snapshot:", snapshot.name)
