#!/usr/bin/python3

from btrfssnapshotmanager.common import *
from btrfssnapshotmanager.periods import *

from datetime import *
from pathlib import PosixPath
import re


snapshots_dir_name = '.snapshots'
snapshots_dir_regex = re.compile(r'(\d\d\d\d)-(\d\d)-(\d\d)_(\d\d)-(\d\d)-(\d\d)_?([HDWM]*)')
snapshots_dir_date_format = '%Y-%m-%d_%H-%M-%S'


class Subvolume():

    snapshots = None

    def __init__(self, path):
        self.path = PosixPath(path)
        if not self._check_path():
            raise Exception("not a valid btrfs subvolume")
        self.snapshots_dir = PosixPath(path, snapshots_dir_name)
        if self.has_snapshots():
            self.load_snapshots()

    def has_snapshots(self):
        return self.snapshots_dir.is_dir()

    def init_snapshots(self):
        if self.has_snapshots():
            raise Exception("snapshot dir already exists")
        self.snapshots_dir.mkdir(mode=0o755)
        self.load_snapshots()

    def load_snapshots(self):
        if not self.has_snapshots():
            raise Exception("snapshot dir doesn't exist")
        self.snapshots = []
        for child in self.snapshots_dir.iterdir():
            if child.is_dir():
                snapshot = self._snapshot_name_parse(child.name)
                if snapshot is not None:
                    self.snapshots.append(snapshot)
        self._sort_snapshots()

    def create_snapshot(self, date=None, tags=None):
        if date is None:
            date = datetime.now()
        if tags is None:
            tags = SnapshotTags()
        name = self._snapshot_name_format(date, tags)
        snapshot = Snapshot(self, name, date, tags, create=True)
        self.snapshots.append(snapshot)
        self._sort_snapshots()
        return snapshot

    def find_snapshot(self, name):
        if not self.has_snapshots():
            raise Exception("snapshot dir doesn't exist")
        for s in self.snapshots:
            if s.name == name:
                return s
        return None

    def _check_path(self):
        try:
            cmd("sudo btrfs subvolume show {0}".format(self.path))
        except CommandException:
            return False
        return True

    def _sort_snapshots(self):
        self.snapshots = sorted(self.snapshots, key=lambda s: s.date)

    def _snapshot_name_parse(self, name):
        snapshots_dir_match = snapshots_dir_regex.fullmatch(name)
        if snapshots_dir_match:
            date = datetime(
                int(snapshots_dir_match.group(1)),
                int(snapshots_dir_match.group(2)),
                int(snapshots_dir_match.group(3)),
                int(snapshots_dir_match.group(4)),
                int(snapshots_dir_match.group(5)),
                int(snapshots_dir_match.group(6)))
            tags = SnapshotTags(snapshots_dir_match.group(7))
            return Snapshot(self, name, date, tags)
        else:
            return None

    def _snapshot_name_format(self, date, tags):
        name = date.strftime(snapshots_dir_date_format)
        if not tags.is_empty():
            name += '_' + tags.string()
        return name


class Snapshot():

    def __init__(self, subvolume, name, date, tags, create=False):
        self.subvolume = subvolume
        self.name = name
        self.path = PosixPath(subvolume.snapshots_dir, name)
        self.date = date
        self.tags = tags
        if create:
            self.create()

    def create(self):
        cmd("sudo btrfs subvolume snapshot -r {0} {1}".format(self.subvolume.path, self.path))

    def delete(self):
        cmd("sudo btrfs subvolume delete --commit-each {0}".format(self.path))
        self.subvolume.snapshots.remove(self)


class SnapshotTags():

    def __init__(self, string=None):
        self.tags = {}
        if string is not None:
            for t, p in period_map.items():
                if t in string:
                    self.tags[t] = p

    def periods(self):
        return [p for p in sorted(self.tags.values(), key=lambda x: x.seconds)]

    def string(self):
        return ''.join([p.tag for p in self.periods()])

    def is_empty(self):
        return len(self.tags) == 0
