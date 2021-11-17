#!/usr/bin/python3

from btrfssnapshotmanager.periods import *

from datetime import *
from pathlib import PosixPath
import re


snapshots_dir_name = '.snapshots'
snapshots_dir_regex = re.compile(r'(\d\d\d\d)-(\d\d)-(\d\d)_(\d\d)-(\d\d)-(\d\d)_?([HDWM]*)')


class Subvolume():

    snapshots = None

    def __init__(self, path):
        self.path = PosixPath(path)
        if not self._check_path():
            raise Exception("not a valid btrfs subvolume")
        self.snapshots_dir = PosixPath(path, snapshots_dir_name)
        if self.has_snapshots():
            self.load_snapshots()

    def _check_path(self):
        #TODO ensure this is a btrfs subvolume
        return True

    def has_snapshots(self):
        return self.snapshots_dir.is_dir()

    def init_snapshots(self):
        #TODO make .snapshots dir
        self.load_snapshots()

    def load_snapshots(self):
        if not self.has_snapshots():
            raise Exception("snapshot dir doesn't exist")
        self.snapshots = []
        for child in sorted(self.snapshots_dir.iterdir()):
            snapshots_dir_match = snapshots_dir_regex.fullmatch(child.name)
            if snapshots_dir_match:
                date = datetime(
                    int(snapshots_dir_match.group(1)),
                    int(snapshots_dir_match.group(2)),
                    int(snapshots_dir_match.group(3)),
                    int(snapshots_dir_match.group(4)),
                    int(snapshots_dir_match.group(5)),
                    int(snapshots_dir_match.group(6)))
                tags = SnapshotTags(snapshots_dir_match.group(7))
                self.snapshots.append(Snapshot(self, child.name, date, tags))


class Snapshot():

    def __init__(self, subvolume, name, date, tags, create=False):
        self.subvolume = subvolume
        self.name = name
        self.date = date
        self.tags = tags
        if create:
            self.create(tags)

    def create(self, tags):
        #TODO make snapshot
        pass

    def delete(self):
        #TODO delete
        pass


class SnapshotTags():

    def __init__(self, string):
        self.tags = {}
        for t, p in period_map.items():
            if t in string:
                self.tags[t] = p
