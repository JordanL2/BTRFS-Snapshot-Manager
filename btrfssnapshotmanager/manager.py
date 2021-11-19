#!/usr/bin/python3

from btrfssnapshotmanager.config import *


class SnapshotManager():

    def __init__(self):
        self.config = Config(self)
        self.managers = {}
        for subvol, subvol_instance in self.config.subvolumes.items():
            self.managers[subvol] = SubvolumeManager(
                self,
                subvol_instance,
                self.config.retention[subvol],
                self.config.backups[subvol],
            )
            if subvol in self.config.systemdboot:
                self.managers[subvol].systemdboot = self.config.systemdboot[subvol]

    def execute(self, subvols=None, cleanup=True, backup=True, systemdboot_sync=True):
        managers_to_run = self.managers
        if subvols is not None and len(subvols) > 0:
            managers_to_run = dict([(s, m) for s, m in managers_to_run.items() if s in subvols])

        empty_line = False
        for subvol, manager in managers_to_run.items():
            if empty_line:
                info()
            empty_line = True
            info("Subvolume:", subvol)
            periods = []
            for period, count in manager.retention_config.items():
                if manager.should_run(period):
                    info("Period reached:", period.name)
                    periods.append(period)
            if len(periods) > 0:

                # Create a new snapshot for the required periods
                manager.create_snapshot(periods)

                # If specified, delete unwanted snapshots
                if cleanup:
                    info()
                    info("Cleanup...")
                    manager.cleanup()

                # If required, ensure backups are in sync
                if backup:
                    info()
                    info("Backup...")
                    manager.backup()

                # If requires, sync systemd-boot entries
                if systemdboot_sync and manager.systemdboot is not None:
                    info()
                    info("Systemd-boot entry sync...")
                    manager.systemdboot.sync()

            else:
                info("No periods reached")


class SubvolumeManager():

    def __init__(self, snapshot_manager, subvol_instance, retention_config, backup_config):
        self.snapshot_manager = snapshot_manager
        self.subvol = subvol_instance
        if not self.subvol.has_snapshots():
            self.subvol.init_snapshots()
        self.retention_config = retention_config
        self.backups = backup_config
        self.systemdboot = None

    def last_run(self, period):
        if period not in self.retention_config:
            raise SnapshotException("No {0} snapshot schedule set for subvolume {1}".format(period.name, self.subvol.name))
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

    def create_snapshot(self, periods):
        info("Creating snapshot for:", ', '.join([p.name for p in periods]))
        self.subvol.create_snapshot(periods=periods)

    def cleanup(self):
        dont_delete = set()
        for period in PERIODS:
            max_snapshots = 0
            if period in self.retention_config:
                max_snapshots = self.retention_config[period]
            snapshots = self.subvol.search_snapshots(periods=[period])
            for snapshot in snapshots[max(0, len(snapshots) - max_snapshots) : ]:
                dont_delete.add(snapshot)
        snapshots = self.subvol.search_snapshots(periods=PERIODS)
        count = 0
        for snapshot in snapshots:
            if snapshot not in dont_delete:
                info("Deleting snapshot:", snapshot.name)
                count += 1
        if count == 0:
            info("Nothing to do")

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
