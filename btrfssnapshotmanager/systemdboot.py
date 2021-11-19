#!/usr/bin/python3

from btrfssnapshotmanager.common import *

from pathlib import PosixPath
import re


default_boot_dir = '/boot'
entry_line_regex = re.compile(r'(\S+)(\s*)(.*?)')

def boot_entry_name_parse(entry, name):
    file_regex = re.compile('snapshot\-(\d\d\d\d-\d\d-\d\d_\d\d-\d\d-\d\d_?[HDWM]*)\-' + entry)
    file_match = file_regex.fullmatch(name)
    if file_match:
        return file_match.group(1)
    return None

def boot_entry_name_format(entry, name):
    return "snapshot-{0}-{1}".format(name, entry)


class SystemdBoot():

    entries_dir = 'loader/entries'

    def __init__(self, subvol, entry, retention):
        self.subvol = subvol
        self.entry = entry
        self.retention = retention
        self.boot_path = default_boot_dir
        self.load_entries()

    def load_entries(self):
        self.entries = {}
        path = PosixPath(self.boot_path, self.entries_dir)
        if not path.is_dir():
            raise SnapshotException("Boot path {0} does not exist".format(path))
        for child in path.iterdir():
            if child.is_file():
                snapshot_name = boot_entry_name_parse(self.entry, child.name)
                if snapshot_name is not None:
                    snapshot = self.subvol.find_snapshot(snapshot_name)
                    self.entries[child.name] = snapshot
                    if snapshot is not None:
                        snapshot.systemdboot = self
                        snapshot.systemdboot_entry = child.name

    def create_entry(self, snapshot):
        entry_name = boot_entry_name_format(self.entry, snapshot.name)
        ref_entry_path = PosixPath(self.boot_path, self.entries_dir, self.entry)
        new_entry_filename = PosixPath(self.boot_path, self.entries_dir, entry_name)
        if not ref_entry_path.is_file():
            raise SnapshotException("Reference systemd-boot entry file {0} not found".format(ref_entry_path))

        # Generate path to snapshot from btrfs toplevel
        snapshot_toplevel_path = PosixPath(
            '/',
            self.subvol.label,
            self.subvol.snapshots_dir.relative_to(self.subvol.path),
            snapshot.name
        )

        # Read reference entry one line at a time, modify and write to new entry
        info("Creating new entry {0}".format(entry_name))
        info("---")
        with open(ref_entry_path, 'r') as fhin:
            with open(new_entry_filename, 'w') as fhout:
                while True:
                    line = fhin.readline().strip()
                    if not line:
                        break

                    entry_line_match = entry_line_regex.fullmatch(line)
                    if entry_line_match:
                        key = entry_line_match.group(1)
                        space = entry_line_match.group(2)
                        value = entry_line_match.group(3)

                        if key == 'title':
                            value = "Snapshot - {0} - {1}".format(snapshot.date.strftime('%a %d-%b %H:%M:%S'), value)

                        elif key == 'options':
                            options = value.split()
                            for o in options:
                                # Options - rootflags
                                if o.startswith('rootflags='):
                                    flags = o[10:].split(',')
                                    for i, f in enumerate(flags.copy()):
                                        if f.startswith('subvol='):
                                            flags[i] = "subvol={0}".format(snapshot_toplevel_path)
                                    new_rootflags = 'rootflags=' + ','.join(flags)
                                    value = value.replace(o, new_rootflags)

                        line = key + space + value
                    else:
                        warn("Invalid line: `{0}`".format(line))

                    info(line)
                    print(line, file=fhout)
        info("---")

        self.entries[entry_name] = snapshot

    def delete_entry(self, entry_name):
        if entry_name not in self.entries:
            raise SnapshotException("No such systemd-boot entry: {}".format(entry_name))
        entry_file = PosixPath(self.boot_path, self.entries_dir, entry_name)
        entry_file.unlink()
        del self.entries[entry_name]

    def sync(self):
        snapshots_needed = set()
        for period, count in self.retention.items():
            snapshots = self.subvol.search_snapshots(periods=[period])
            if len(snapshots) > count:
                snapshots = snapshots[len(snapshots) - count :]
            for s in snapshots:
                snapshots_needed.add(s)
        snapshots_needed = sorted(list(snapshots_needed), key=lambda s: s.name)
        debug("Snapshots found that should have systemd-boot entries:")
        for s in snapshots_needed:
            debug("-", s.name)

        # Create missing entries
        for s in snapshots_needed:
            if s not in self.entries.values():
                info("Snapshot {0} requires an entry".format(s.name))
                self.create_entry(s)

        # Delete entries not required
        for entry_name, snapshot in self.entries.copy().items():
            if snapshot not in snapshots_needed:
                info("Snapshot {0} no longer requires an entry".format(snapshot.name))
                self.delete_entry(entry_name)
