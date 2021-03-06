#!/usr/bin/python3

from btrfssnapshotmanager.common import *

from datetime import *
from pathlib import PosixPath, PurePosixPath
import re


systemdboot_default_boot_dir = '/boot'
systemdboot_default_entries_dir = 'loader/entries'
systemdboot_default_snapshots_dir = 'snapshots'
systemdboot_entry_line_regex = re.compile(r'(\S+)(\s*)(.*?)')
systemdboot_snapshot_format = '%Y-%m-%d_%H-%M-%S'

def boot_entry_name_parse(entry, name):
    file_regex = re.compile('snapshot\-(\d\d\d\d-\d\d-\d\d_\d\d-\d\d-\d\d_?[HDWM]*)\-' + entry)
    file_match = file_regex.fullmatch(name)
    if file_match:
        return file_match.group(1)
    return None

def boot_entry_name_format(entry, name):
    return "snapshot-{0}-{1}".format(name, entry)

def systemdboot_snapshot_name_parse(name):
    return datetime.strptime(name, systemdboot_snapshot_format)

def systemdboot_snapshot_name_format(date):
    return date.strftime(systemdboot_snapshot_format)


class SystemdBootSnapshot():

    def __init__(self, systemdboot_manager, name):
        self.systemdboot_manager = systemdboot_manager
        self.name = name
        self.date = systemdboot_snapshot_name_parse(name)

    def path(self):
        return PosixPath(self.systemdboot_manager.snapshots_dir, self.name)

    def path_for_bootloader(self):
        return PurePosixPath(
            '/',
            PosixPath(
                self.systemdboot_manager.snapshots_dir,
                self.name
            ).relative_to(self.systemdboot_manager.boot_path)
        )

    def delete(self):
        info("Deleting systemd-boot boot snapshot {0}".format(self.name))
        cmd("rm -rf {0}".format(self.path()))
        self.systemdboot_manager.boot_snapshots.remove(self)
        for entry_manager in self.systemdboot_manager.entry_managers:
            entry_manager.delete_using_nonexistent_boot_snapshot()

    def exists(self):
        return self.path().is_dir()


class SystemdBootManager():

    def __init__(self):
        self.entry_managers = []
        self.init_file_list = None
        self.set_boot_path(systemdboot_default_boot_dir)

    def set_boot_path(self, boot_path):
        self.boot_path = boot_path
        self.snapshots_dir = PosixPath(boot_path, systemdboot_default_snapshots_dir)
        self.load_boot_snapshots()
        self.load_init_files()
        self.entries_dir = PosixPath(self.boot_path, systemdboot_default_entries_dir)
        for entry_manager in self.entry_managers:
            entry_manager.load_entries()

    def set_init_file_list(self, init_file_list):
        self.init_file_list = init_file_list
        self.load_init_files()

    def load_boot_snapshots(self):
        self.boot_snapshots = []
        if not self.snapshots_dir.is_dir():
            info("Creating boot snapshots directory: {0}".format(self.snapshots_dir))
            self.snapshots_dir.mkdir()
        for child in self.snapshots_dir.iterdir():
            if child.is_dir():
                try:
                    self.boot_snapshots.append(SystemdBootSnapshot(self, child.name))
                except ValueError:
                    pass
        self.boot_snapshots = sorted(self.boot_snapshots, key=lambda s: s.date)

    def load_init_files(self):
        self.init_files = []
        for child in PosixPath(self.boot_path).iterdir():
            if child.is_file() and (self.init_file_list is None or child.name in self.init_file_list):
                self.init_files.append(child.name)
        self.init_files = sorted(self.init_files)

    def create_boot_snapshot(self, date=None):
        if date is None:
            date = datetime.now()
        boot_snapshot_name = systemdboot_snapshot_name_format(date)
        info("Creating systemd-boot boot snapshot: {0}/{1}".format(self.snapshots_dir, boot_snapshot_name))

        cmd("mkdir {0}/{1}".format(self.snapshots_dir, boot_snapshot_name))
        for init_file in self.init_files:
            cmd("cp {1}/{0} {2}/{3}/{0}".format(init_file, self.boot_path, self.snapshots_dir, boot_snapshot_name))

        boot_snapshot = SystemdBootSnapshot(self, boot_snapshot_name)
        self.boot_snapshots.append(boot_snapshot)
        return boot_snapshot

    def create_boot_snapshot_if_needed(self, date=None):
        debug("Determining if new systemd-boot boot snapshot required...")
        needed = False
        if len(self.boot_snapshots) == 0:
            needed = True
            debug("- No systemd-boot boot snapshots found, new boot snapshot required")
        else:
            last_boot_snapshot = self.boot_snapshots[-1]
            for init_file in self.init_files:
                command = "diff {1}/{0} {2}/{3}/{0}".format(init_file, self.boot_path, self.snapshots_dir, last_boot_snapshot.name)
                code = cmd(command, return_code=True)[2]
                if code != 0:
                    needed = True
                    debug("- Init file {0} has changed, new systemd-boot boot snapshot required".format(init_file))
                    break

        if needed:
            self.create_boot_snapshot(date=date)
        else:
            debug("New systemd-boot boot snapshot is not required")

    def delete_boot_snapshot(self, boot_snapshot_name):
        boot_snapshot = [b for b in self.boot_snapshots if b.name == boot_snapshot_name]
        if len(boot_snapshot) != 1:
            raise SnapshotException("Could not find boot snapshot {0}".format(boot_snapshot_name))
        boot_snapshot = boot_snapshot[0]
        boot_snapshot.delete()

    def get_boot_snapshot_for_snapshot(self, snapshot):
        for boot_snapshot in reversed(self.boot_snapshots):
            if boot_snapshot.date <= snapshot.date:
                return boot_snapshot
        return None

    def remove_unused_boot_snapshots(self):
        debug("Checking if any systemd-boot boot snapshots can be deleted...")
        boot_snapshots_to_delete = set(self.boot_snapshots)
        for subvol in self._subvols():
            debug("- Checking subvolume {0}".format(subvol.name))
            for snapshot in subvol.snapshots:
                boot_snapshot = self.get_boot_snapshot_for_snapshot(snapshot)
                if boot_snapshot is not None and boot_snapshot in boot_snapshots_to_delete:
                    boot_snapshots_to_delete.remove(boot_snapshot)
        for boot_snapshot in boot_snapshots_to_delete:
            debug("No longer need systemd-boot boot snapshot {0}".format(boot_snapshot.name))
            boot_snapshot.delete()

    def _subvols(self):
        subvols = []
        for entry_manager in self.entry_managers:
            subvol = entry_manager.subvol
            if subvol not in subvols:
                subvols.append(subvol)
        return subvols


class SystemdBootEntry():

    def __init__(self, entry_manager, name, snapshot, boot_snapshot=None):
        self.entry_manager = entry_manager
        self.name = name
        self.snapshot = snapshot
        self.boot_snapshot = boot_snapshot
        if self.boot_snapshot is None:
            self.boot_snapshot = self.find_boot_snapshot()

    def path(self):
        return PosixPath(self.entry_manager.manager.entries_dir, self.name)

    def delete(self):
        info("Deleting systemd-boot entry {0}".format(self.name))
        entry_file = self.path()
        entry_file.unlink()
        if self.snapshot is not None:
            del self.snapshot.systemdboot[self.entry_manager]
        self.entry_manager.entries.remove(self)

    def find_boot_snapshot(self):
        entry_file = self.path()
        with open(entry_file, 'r') as fhin:
            while line := fhin.readline().strip():

                entry_line_match = systemdboot_entry_line_regex.fullmatch(line)
                if entry_line_match:
                    key = entry_line_match.group(1)
                    space = entry_line_match.group(2)
                    value = entry_line_match.group(3)

                if key in ('linux', 'initrd'):
                    init_file_path = PurePosixPath(value)
                    parent_dir = init_file_path.parts[-2]
                    try:
                        return SystemdBootSnapshot(self.entry_manager.manager, str(parent_dir))
                    except ValueError:
                        return None


class SystemdBootEntryManager():

    def __init__(self, manager, subvol, entry, retention):
        self.manager = manager
        self.subvol = subvol
        self.reference_entry = entry
        self.retention = retention
        self.load_entries()

    def load_entries(self):
        self.entries = []
        if not self.manager.entries_dir.is_dir():
            raise SnapshotException("Systemd-boot entries path {0} does not exist".format(self.manager.entries_dir))
        for child in self.manager.entries_dir.iterdir():
            if child.is_file():
                snapshot_name = boot_entry_name_parse(self.reference_entry, child.name)
                if snapshot_name is not None:
                    snapshot = self.subvol.find_snapshot(snapshot_name)
                    boot_entry = SystemdBootEntry(self, child.name, snapshot)
                    self.entries.append(boot_entry)
                    if snapshot is not None:
                        snapshot.systemdboot[self] = child.name
        self.entries = sorted(self.entries, key=lambda e: e.name)

    def create_entry(self, snapshot):
        entry_name = boot_entry_name_format(self.reference_entry, snapshot.name)
        ref_entry_path = PosixPath(self.manager.entries_dir, self.reference_entry)
        new_entry_filename = PosixPath(self.manager.entries_dir, entry_name)
        if not ref_entry_path.is_file():
            raise SnapshotException("Reference systemd-boot entry file {0} not found".format(ref_entry_path))

        # Generate path to snapshot from btrfs toplevel
        snapshot_toplevel_path = PosixPath(
            '/',
            self.subvol.top_level_path,
            self.subvol.snapshots_dir.relative_to(self.subvol.path),
            snapshot.name
        )

        # Get boot snapshot for this snapshot
        boot_snapshot = self.manager.get_boot_snapshot_for_snapshot(snapshot)

        # Read reference entry one line at a time, modify and write to new entry
        info("Creating systemd-boot entry {0}".format(entry_name))
        debug("---")
        with open(ref_entry_path, 'r') as fhin:
            with open(new_entry_filename, 'w') as fhout:
                while line := fhin.readline().strip():

                    entry_line_match = systemdboot_entry_line_regex.fullmatch(line)
                    if entry_line_match:
                        key = entry_line_match.group(1)
                        space = entry_line_match.group(2)
                        value = entry_line_match.group(3)

                        if key == 'title':
                            value = "Snapshot - {0} - {1}".format(snapshot.date.strftime('%a %d-%b %H:%M:%S'), value)

                        elif key in ('linux', 'initrd') and boot_snapshot is not None:
                            # If there is a boot snapshot, use the linux / initrds in that
                            value = str(PosixPath(boot_snapshot.path_for_bootloader(), PosixPath(value).relative_to('/')))

                        elif key == 'options':
                            options = value.split()
                            for oi, o in enumerate(options.copy()):
                                # Options - rootflags
                                if o.startswith('rootflags='):
                                    flags = o[10:].split(',')
                                    for fi, f in enumerate(flags.copy()):
                                        if f.startswith('subvol='):
                                            flags[fi] = "subvol={0}".format(snapshot_toplevel_path)
                                    options[oi] = 'rootflags=' + ','.join(flags)
                            value = ' '.join(options)

                        line = key + space + value
                    else:
                        warn("Invalid line: `{0}`".format(line))

                    debug(line)
                    print(line, file=fhout)
        debug("---")

        boot_entry = SystemdBootEntry(self, entry_name, snapshot, boot_snapshot)
        self.entries.append(boot_entry)

    def delete_entry(self, entry_name):
        for entry in self.entries:
            if entry.name == entry_name:
                entry.delete()
                break
        else:
            raise SnapshotException("No such systemd-boot entry: {}".format(entry_name))

    def delete_using_nonexistent_snapshot(self):
        for entry in self.entries.copy():
            if entry.snapshot is None:
                debug("Systemd-boot entry {0} not associated with an existing snapshot".format(entry.name))
                entry.delete()

    def delete_using_nonexistent_boot_snapshot(self):
        for entry in self.entries.copy():
            if entry.boot_snapshot is not None and not entry.boot_snapshot.exists():
                 debug("Systemd-boot entry {0} is using non-existent boot snapshot {1}".format(entry.name, entry.boot_snapshot.name))
                 entry.delete()

    def run(self):
        snapshots_needed = set()
        for period, count in self.retention.items():
            snapshots = self.subvol.search_snapshots(periods=[period])
            debug("systemdboot - searched for snapshots with period {}".format(period))
            if len(snapshots) > count:
                snapshots = snapshots[len(snapshots) - count :]
            for s in snapshots:
                snapshots_needed.add(s)
                debug("- Snapshot: {}".format(s.name))
        snapshots_needed = sorted(list(snapshots_needed), key=lambda s: s.name)
        debug("Snapshots found that should have systemd-boot {0} entries:".format(self.reference_entry))
        for s in snapshots_needed:
            debug("-", s.name)

        # Delete entries not required or broken
        self.delete_using_nonexistent_snapshot()
        self.delete_using_nonexistent_boot_snapshot()
        for entry in self.entries.copy():
            snapshot = entry.snapshot
            if snapshot not in snapshots_needed:
                debug("A systemd-boot {0} entry is not longer required for snapshot {1}".format(self.reference_entry, snapshot.name))
                entry.delete()

        # Create missing entries
        entry_snapshots = [e.snapshot for e in self.entries]
        for snapshot in snapshots_needed:
            if snapshot not in entry_snapshots:
                debug("A systemd-boot {0} entry is required for snapshot {1}".format(self.reference_entry, snapshot.name))
                self.create_entry(snapshot)
