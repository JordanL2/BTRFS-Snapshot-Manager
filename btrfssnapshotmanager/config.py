#!/usr/bin/python3

from btrfssnapshotmanager.backups import *
from btrfssnapshotmanager.systemdboot import *

from pathlib import PosixPath
import yaml


class Config():

    config_file = PosixPath('/etc/btrfs-snapshot-manager/config.yml')

    def __init__(self, snapshot_manager):
        self.snapshot_manager = snapshot_manager
        self.load_config()
        self.load_retention()
        self.load_backups()
        self.load_systemdboot()

    def load_config(self):
        if not self.config_file.is_file():
            self.raw_config = {}
            return
        with open(self.config_file, 'r') as fh:
            config = yaml.load(fh, Loader=yaml.CLoader)

        if config is None:
            self.raw_config = {}
        else:
            self.raw_config = config

    def get_subvolume_config(self):
        config = {}
        if 'subvolumes' in self.raw_config and self.raw_config['subvolumes'] is not None:
            for subvol_config in self.raw_config['subvolumes']:
                if subvol_config is not None:
                    config[subvol_config['path']] = subvol_config
        return config

    def load_retention(self):
        self.subvolumes = {}
        self.retention = {}
        config = self.get_subvolume_config()
        for subvol, subvol_config in config.items():
            # Initialise subvolume object
            self.subvolumes[subvol] = Subvolume(subvol)
            if 'snapshots-path' in subvol_config:
                self.subvolumes[subvol].set_snapshot_dir(subvol_config['snapshots_path'])

            subvol_retention = {}
            if 'retention' in subvol_config and subvol_config['retention'] is not None:
                for period in PERIODS:
                    if period.name in subvol_config['retention']:
                        subvol_retention[period] = int(subvol_config['retention'][period.name])
            self.retention[subvol] = subvol_retention

    def load_backups(self):
        self.backups = {}
        config = self.get_subvolume_config()
        for subvol, subvol_config in config.items():
            subvol_instance = self.subvolumes[subvol]

            self.backups[subvol] = []
            if 'backup' in subvol_config and subvol_config['backup'] is not None:
                for backup_config in subvol_config['backup']:

                    backup = None

                    if 'type' not in backup_config:
                        raise SnapshotException("Backup type not found for subvolume " + subvol)
                    backup_type = backup_config['type']
                    if backup_type not in ('btrfs', 'rsync'):
                        raise SnapshotException("Backup type '{0}' invalid for subvolume {1}".format(backup_type, subvol))

                    if 'retention' not in backup_config or backup_config['retention'] is None:
                        raise SnapshotException("Backup retention config not found fore subvolume {0}".format(subvol))
                    retention = {}
                    for period in PERIODS:
                        if period.name in backup_config['retention']:
                            retention[period] = int(backup_config['retention'][period.name])

                    if 'local' in backup_config:
                        if backup_config['local'] is None or 'path' not in backup_config['local']:
                            raise SnapshotException("Local backup config missing path for subvolume " + subvol)
                        path = backup_config['local']['path']

                        if backup_type == 'btrfs':
                            backup = LocalBtrfsBackup(subvol_instance, retention, path)
                        elif backup_type == 'rsync':
                            backup = LocalRsyncBackup(subvol_instance, retention, path)

                    elif 'remote' in backup_config:
                        if backup_config['remote'] is None or 'host' not in backup_config['remote']:
                            raise SnapshotException("Remote backup config missing host for subvolume " + subvol)
                        host = backup_config['remote']['host']

                        if 'path' not in backup_config['remote']:
                            raise SnapshotException("Remote backup config missing path for subvolume " + subvol)
                        path = backup_config['remote']['path']

                        user = None
                        if 'user' in backup_config['remote']:
                            user = backup_config['remote']['user']

                        ssh_options = None
                        if 'ssh-options' in backup_config['remote']:
                            ssh_options = backup_config['remote']['ssh-options']

                        if backup_type == 'btrfs':
                            backup = RemoteBtrfsBackup(subvol_instance, retention, host, user, ssh_options, path)
                        elif backup_type == 'rsync':
                            backup = RemoteRsyncBackup(subvol_instance, retention, host, user, ssh_options, path)

                    if backup is not None:
                        if 'last_sync_file' in backup_config:
                            backup.last_sync_file = backup_config['last_sync_file']
                        self.backups[subvol].append(backup)

    def load_systemdboot(self):
        self.systemdboots = {}
        config = self.get_subvolume_config()
        for subvol, subvol_config in config.items():
            subvol_instance = self.subvolumes[subvol]

            if 'systemd-boot' in subvol_config and subvol_config['systemd-boot'] is not None:
                systemdboot_config = subvol_config['systemd-boot']

                if 'entries' not in systemdboot_config:
                    raise SnapshotException("Systemd-boot config missing entries for subvolume " + subvol)

                self.systemdboots[subvol] = []

                for systemdboot_config_entry in systemdboot_config['entries']:

                    if 'entry' not in systemdboot_config_entry:
                        raise SnapshotException("Systemd-boot config missing entry for subvolume " + subvol)
                    entry = systemdboot_config_entry['entry']

                    if 'retention' not in systemdboot_config_entry or systemdboot_config_entry['retention'] is None:
                        raise SnapshotException("Systemd-boot retention config not found for subvolume {0}".format(subvol))
                    retention = {}
                    for period in PERIODS:
                        if period.name in systemdboot_config_entry['retention']:
                            retention[period] = int(systemdboot_config_entry['retention'][period.name])

                    systemdboot = SystemdBoot(subvol_instance, entry, retention)

                    if 'boot-path' in systemdboot_config:
                        systemdboot.set_boot_path(systemdboot_config['boot-path'])

                    self.systemdboots[subvol].append(systemdboot)
