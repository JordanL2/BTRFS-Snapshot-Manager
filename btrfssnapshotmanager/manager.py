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
        self.systemdboot_manager = self.config.systemdboot_manager

    def execute(self, subvols=None, cleanup=True, backup=True, systemdboot_run=True):
        managers_to_run = self.managers
        if subvols is not None and len(subvols) > 0:
            managers_to_run = dict([(s, m) for s, m in managers_to_run.items() if s in subvols])

        for subvol, manager in managers_to_run.items():
            info('================')
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
                    info('----------------')
                    info("Cleanup...")
                    manager.cleanup()

                # If required, ensure backups are in sync
                if backup:
                    info('----------------')
                    info("Backup...")
                    manager.backup()

            else:
                info("No periods reached")

        # If required, sync systemd-boot entries
        if systemdboot_run and self.systemdboot_manager is not None:
            info('================')
            info("Systemd-boot...")
            for entry_manager in self.systemdboot_manager.entry_managers:
                entry_manager.run()

    def cleanup(self, subvols=None):
        managers_to_run = self.managers
        if subvols is not None and len(subvols) > 0:
            managers_to_run = dict([(s, m) for s, m in managers_to_run.items() if s in subvols])

        empty_line = False
        for subvol, manager in managers_to_run.items():
            if empty_line:
                info('---')
            empty_line = True
            info("Subvolume:", subvol)
            manager.cleanup()

    def backup(self, subvols=None, ids=None):
        managers_to_run = self.managers
        if subvols is not None and len(subvols) > 0:
            managers_to_run = dict([(s, m) for s, m in managers_to_run.items() if s in subvols and len(m.backups) > 0])

        empty_line = False
        for subvol, manager in managers_to_run.items():
            if empty_line:
                info('---')
            manager.backup(ids=ids)
            empty_line = True


class SubvolumeManager():

    def __init__(self, snapshot_manager, subvol_instance, retention_config, backup_config):
        self.snapshot_manager = snapshot_manager
        self.subvol = subvol_instance
        if not self.subvol.has_snapshots():
            self.subvol.init_snapshots()
        self.retention_config = retention_config
        self.backups = backup_config

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
                snapshot.delete()
                count += 1
        if count == 0:
            info("Nothing to do")

    def backup(self, ids=None):
        if ids is not None and len(ids) > 0:
            for i in ids:
                if i < 0 or i >= len(self.backups) or i != int(i):
                    raise SnapshotException("Invalid backup ID {0} for subvolume {1}".format(i, self.subvol.name))

        empty_line = False
        backups = self.get_backups(ids)
        for i, backup in sorted(backups.items(), key=lambda b: b[0]):
            if ids is not None and i not in ids:
                continue
            if empty_line:
                info('---')
            empty_line = True
            info("Running backup for {0} to {1}".format(self.subvol.path, backup.location()))
            backup.backup()

    def get_backups(self, ids=None):
        if ids is not None and len(ids) > 0:
            for i in ids:
                if i < 0 or i >= len(self.backups) or i != int(i):
                    raise SnapshotException("Invalid backup ID {0} for subvolume {1}".format(i, self.subvol.name))

        backups = {}
        for i, backup in enumerate(self.backups):
            if ids is None or i in ids:
                backups[i] = backup
        return backups
