#!/usr/bin/python3

from btrfssnapshotmanager.snapshots import *

from pathlib import PosixPath
import re


def boot_entry_name_parse(entry, name):
    file_regex = re.compile('snapshot\-(\d\d\d\d-\d\d-\d\d_\d\d-\d\d-\d\d_?[HDWM]*)\-' + entry)
    file_match = file_regex.fullmatch(name)
    if file_match:
        return file_match.group(1)
    return None

def boot_entry_name_format(entry, name):
    return "snapshot-{0}-{1}".format(name, entry)


class SystemdBoot():

    def __init__(self, subvol, entry, retention):
        self.subvol = subvol
        self.entry = entry
        self.retention = retention
        self.boot_path = '/boot'
        self.load_entries()

    def load_entries(self):
        self.entries = {}
        path = PosixPath(self.boot_path, 'loader/entries')
        if not path.is_dir():
            raise SnapshotException("Boot path {0} does not exist".format(path))
        for child in path.iterdir():
            if child.is_file():
                snapshot_name = boot_entry_name_parse(self.entry, child.name)
                if snapshot_name is not None:
                    snapshot = self.subvol.find_snapshot(snapshot_name)
                    self.entries[child.name] = snapshot
