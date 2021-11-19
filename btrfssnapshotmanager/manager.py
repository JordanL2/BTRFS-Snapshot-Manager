#!/usr/bin/python3

from btrfssnapshotmanager.common import *
from btrfssnapshotmanager.config import *
from btrfssnapshotmanager.snapshots import *


class SnapshotManager():

    def __init__(self):
        self.config = Config(self)
        self.managers = {}
        for subvol in self.config.schedules:
            self.managers[subvol] = SubvolumeManager(self, subvol)
        self.config.load_backups()
        for subvol in self.managers:
            self.managers[subvol].load_backups()

    def execute(self):
        empty_line = False
        for subvol, manager in self.managers.items():
            if empty_line:
                info()
            empty_line = True
            info("Subvolume:", subvol)
            periods = []
            for period, count in manager.config.items():
                if manager.should_run(period):
                    info("Period reached:", period.name)
                    periods.append(period)
            if len(periods) > 0:
                manager.run(periods)
            else:
                info("No periods reached")


class SubvolumeManager():

    def __init__(self, snapshot_manager, subvol):
        self.snapshot_manager = snapshot_manager
        self.subvol_name = subvol
        self.subvol = Subvolume(subvol)
        if not self.subvol.has_snapshots():
            self.subvol.init_snapshots()
        self.config = self.snapshot_manager.config.schedules[subvol]

    def load_backups(self):
        self.backups = self.snapshot_manager.config.backups[self.subvol_name]

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

    def run(self, periods, cleanup=True, backup=True):
        info("Creating snapshot for:", ', '.join([p.name for p in periods]))
        self.subvol.create_snapshot(periods=periods)

        if cleanup:
            info()
            info("Cleanup...")
            self.cleanup()

        if backup:
            info()
            info("Backup...")
            self.backup()

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

    def backup(self, ids=None):
        empty_line = False
        for i, backup in enumerate(self.backups):
            if empty_line:
                info()
            empty_line = True
            if ids is not None and i not in ids:
                continue
            info("Running backup for {0} to {1}".format(self.subvol.path, backup.location()))
            backup.backup()
