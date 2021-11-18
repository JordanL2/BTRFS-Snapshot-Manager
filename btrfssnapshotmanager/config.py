#!/usr/bin/python3

from btrfssnapshotmanager.backups import *
from btrfssnapshotmanager.common import *
from btrfssnapshotmanager.periods import *

from pathlib import PosixPath
import yaml


class Config():

    config_file = PosixPath('/etc/btrfs-snapshot-manager/config.yml')

    def __init__(self):
        self.load_config()

    def load_config(self):
        if not self.config_file.is_file():
            raise SnapshotException("No file found at: {0}".format(self.filepath))
        with open(self.config_file, 'r') as fh:
            config = yaml.load(fh, Loader=yaml.CLoader)

        if config is None:
            return

        self.schedules = {}
        self.backups = {}
        for subvol in config:
            if config[subvol] is not None:

                # Schedules
                schedule = {}
                if 'retention' in config[subvol] and config[subvol]['retention'] is not None:
                    for period in PERIODS:
                        if period.name in config[subvol]['retention']:
                            schedule[period] = int(config[subvol]['retention'][period.name])
                self.schedules[subvol] = schedule

                # Backups
                self.backups[subvol] = []
                if 'backup' in config[subvol] and config[subvol]['backup'] is not None:
                    for backup_config in config[subvol]['backup']:

                        backup = None

                        if 'type' not in backup_config:
                            raise SnapshotException("Backup type not found for subvolume " + subvol.path)
                        backup_type = backup_config['type']
                        if backup_type not in ('btrfs', 'rsync'):
                            raise SnapshotException("Backup type '{0}' invalid for subvolume {1}".format(backup_type, subvol.path))

                        if 'retention' not in backup_config or backup_config['retention'] is None:
                            raise SnapshotException("Backup retention config not found fore subvolume {0}".format(subvol.path))
                        retention = {}
                        for period in PERIODS:
                            if period.name in backup_config['retention']:
                                retention[period] = int(backup_config['retention'][period.name])

                        if 'local' in backup_config:
                            if backup_config['local'] is None or 'path' not in backup_config['local']:
                                raise SnapshotException("Local backup config missing path for subvolume " + subvol.path)
                            path = backup_config['local']['path']

                            if backup_type == 'btrfs':
                                backup = LocalBtrfsBackup(subvol, retention, path)
                            elif backup_type == 'rsync':
                                backup = LocalRsyncBackup(subvol, retention, path)

                        elif 'remote' in backup_config:
                            if backup_config['remote'] is None or 'host' not in backup_config['remote']:
                                raise SnapshotException("Remote backup config missing host for subvolume " + subvol.path)
                            host = backup_config['remote']['host']

                            if 'path' not in backup_config['remote']:
                                raise SnapshotException("Remote backup config missing path for subvolume " + subvol.path)
                            path = backup_config['remote']['path']

                            user = None
                            if 'user' in backup_config['remote']:
                                user = backup_config['remote']['user']

                            ssh_options = None
                            if 'ssh-options' in backup_config['remote']:
                                ssh_options = backup_config['remote']['ssh-options']

                            if backup_type == 'btrfs':
                                backup = RemoteBtrfsBackup(subvol, retention, host, user, ssh_options, path)
                            elif backup_type == 'rsync':
                                backup = RemoteRsyncBackup(subvol, retention, host, user, ssh_options, path)

                        if backup is not None:
                            if 'last_sync_file' in backup_config:
                                backup.last_sync_file = backup_config['last_sync_file']
                            self.backups[subvol].append(backup)
