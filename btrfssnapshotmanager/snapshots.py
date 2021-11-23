#!/usr/bin/python3

from btrfssnapshotmanager.common import *
from btrfssnapshotmanager.periods import *

from datetime import *
from pathlib import PosixPath
import re


snapshots_dir_name = '.snapshots'
snapshots_dir_regex = re.compile(r'(\d\d\d\d)-(\d\d)-(\d\d)_(\d\d)-(\d\d)-(\d\d)_?([HDWM]*)')
snapshots_dir_date_format = '%Y-%m-%d_%H-%M-%S'

def snapshot_name_parse(name):
    snapshots_dir_match = snapshots_dir_regex.fullmatch(name)
    if snapshots_dir_match:
        date = datetime(
            int(snapshots_dir_match.group(1)),
            int(snapshots_dir_match.group(2)),
            int(snapshots_dir_match.group(3)),
            int(snapshots_dir_match.group(4)),
            int(snapshots_dir_match.group(5)),
            int(snapshots_dir_match.group(6)))

        tags = snapshots_dir_match.group(7)
        periods = []
        for t, p in PERIOD_TAG_MAP.items():
            if t in tags:
                periods.append(p)

        return {'date': date, 'periods': periods}
    else:
        return None

def snapshot_name_format(date, periods):
    name = date.strftime(snapshots_dir_date_format)
    if periods is not None and len(periods) > 0:
        name += '_' + ''.join([p.tag for p in sorted(periods, key=lambda x: x.seconds)])
    return name


class Subvolume():

    def __init__(self, path):
        self.name = path
        self.path = PosixPath(path)
        if not self._check_path():
            raise SnapshotException("Not a valid btrfs subvolume")
        self.snapshots_dir = PosixPath(path, snapshots_dir_name)
        self.snapshots = None
        if self.has_snapshots():
            self.load_snapshots()

        # systemd-boot
        self.systemdboot_manager = None

    def set_snapshot_dir(self, path):
        self.snapshots_dir = PosixPath(self.path, path)
        self.load_snapshots()

    def has_snapshots(self):
        return self.snapshots_dir.is_dir()

    def init_snapshots(self):
        if self.has_snapshots():
            raise SnapshotException("Subvolume is already initialised for snapshots")
        cmd("btrfs subvolume create {0}".format(self.snapshots_dir))
        info("Initialised subvolume", self.path, "for snapshots")
        self.load_snapshots()

    def load_snapshots(self):
        if not self.has_snapshots():
            raise SnapshotException("Subvolume not initialised for snapshots")
        self.snapshots = []
        for child in self.snapshots_dir.iterdir():
            if child.is_dir():
                snapshot_details = snapshot_name_parse(child.name)
                if snapshot_details is not None:
                    snapshot = Snapshot(self, child.name, snapshot_details['date'], snapshot_details['periods'])
                    self.snapshots.append(snapshot)
        self._sort_snapshots()

    def create_snapshot(self, date=None, periods=None):
        info("Creating {1} snapshot for {0}".format(self.name, ', '.join([p.name for p in periods])))
        if not self.has_snapshots():
            raise SnapshotException("Subvolume not initialised for snapshots")
        if date is None:
            date = datetime.now()
        if periods is None:
            periods = []
        name = snapshot_name_format(date, periods)
        snapshot = Snapshot(self, name, date, periods)
        cmd("btrfs subvolume snapshot -r {0} {1}".format(self.path, snapshot.path))
        self.snapshots.append(snapshot)
        self._sort_snapshots()

        # systemd-boot
        if self.systemdboot_manager is not None:
            self.systemdboot_manager.create_boot_snapshot_if_needed(date=date)

        return snapshot

    def find_snapshot(self, name):
        if not self.has_snapshots():
            raise SnapshotException("Subvolume not initialised for snapshots")
        for s in self.snapshots:
            if s.name == name:
                return s
        return None

    def search_snapshots(self, periods=None):
        found_snapshots = []
        for snapshot in self.snapshots:
            if periods is not None:
                if None in periods and (snapshot.periods is None or len(snapshot.periods) == 0):
                    # This has no period, and we're allowing snapshots with no period
                    pass
                elif len([p for p in periods for t in snapshot.periods if p == t]) == 0:
                    continue
            found_snapshots.append(snapshot)
        return found_snapshots

    def _check_path(self):
        try:
            out = cmd("btrfs subvolume show {0}".format(self.path))
            self.top_level_path = out.split("\n")[0].strip()
        except CommandException:
            return False
        return True

    def _sort_snapshots(self):
        self.snapshots = sorted(self.snapshots, key=lambda s: s.date)


class Snapshot():

    def __init__(self, subvol, name, date, periods):
        self.subvol = subvol
        self.name = name
        self.path = PosixPath(subvol.snapshots_dir, name)
        self.date = date
        self.periods = periods

        # systemd-boot
        self.systemdboot = {}

    def delete(self):
        info("Deleting snapshot {0}".format(self.path))
        cmd("btrfs subvolume delete --commit-each {0}".format(self.path))
        self.subvol.snapshots.remove(self)

        # Delete systemd-boot entry
        for systemdboot, entry in self.systemdboot.copy().items():
            systemdboot.delete_entry(entry)

        # Check if systemd-boot boot-snapshots can be deleted
        if self.subvol.systemdboot_manager is not None:
            self.subvol.systemdboot_manager.remove_unused_boot_snapshots()

    def get_periods(self):
        return [p for p in sorted(self.periods, key=lambda x: x.seconds)]
