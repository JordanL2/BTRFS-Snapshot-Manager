#!/usr/bin/python3

from btrfssnapshotmanager.backups import *
from btrfssnapshotmanager.systemdboot import *

from pathlib import PosixPath
import yaml


class ConfigException(Exception):

    def __init__(self, parents, problem):
        self.parents = parents
        self.error = "/{0} {1}".format(
            '/'.join(parents),
            problem
        )
        super().__init__(self, self.error)


class ConfigValidator:

    def validate_config(config, spec, parents, strict):
        # Check type
        expected_type = type(spec)
        if expected_type == type:
            expected_type = spec
        config_type = type(config)
        if expected_type == tuple:
            if config_type in (list, dict):
                raise ConfigException(parents, "must be one of: [{0}], found: {1}".format(', '.join(["\"{0}\"".format(sv) for sv in spec]), config_type.__name__))
            if config not in spec:
                raise ConfigException(parents, "must be one of: [{0}], found: \"{1}\"".format(', '.join(["\"{0}\"".format(sv) for sv in spec]), config))
        elif expected_type != config_type:
            raise ConfigException(parents, "should be type {0}, found type {1}".format(expected_type.__name__, config_type.__name__))

        # Iterate through list
        if config_type == list:
            for i, config_list_item in enumerate(config):
                ConfigValidator.validate_config(config_list_item, spec[0], parents + [str(i)], strict)

        # Iterate through dict
        elif config_type == dict:
            for spec_item, spec_value in spec.items():
                name = spec_item[0]
                required = spec_item[1]

                # Check existence
                if type(required) == tuple:
                    min_number = required[0]
                    max_number = required[1]
                    required_items = required[2:]
                    found_items = 0
                    for required_alternative_item in required_items:
                        if required_alternative_item in config:
                            found_items += 1
                    if min_number is not None and max_number is not None and min_number == max_number and found_items != min_number:
                        raise ConfigException(parents + ["[{0}]".format('|'.join(sorted(list(required_items))))], "exactly {0} required, found {1}".format(min_number, found_items))
                    if min_number is not None and found_items < min_number:
                        raise ConfigException(parents + ["[{0}]".format('|'.join(sorted(list(required_items))))], "at least {0} required, found {1}".format(min_number, found_items))
                    if max_number is not None and found_items > max_number:
                        raise ConfigException(parents + ["[{0}]".format('|'.join(sorted(list(required_items))))], "at most {0} required, found {1}".format(max_number, found_items))

                elif name not in config and required:
                    raise ConfigException(parents + [name], 'is required')

                # Validate the item
                if name in config:
                    ConfigValidator.validate_config(config[name], spec_value, parents + [name], strict)

            # If strict is enabled, go through each item of config and ensure it's in spec
            if strict:
                for config_name in config.keys():
                    if len([s for s in spec if s[0] == config_name]) == 0:
                        raise ConfigException(parents + [config_name], 'is not recognised')


class Config():

    config_file = PosixPath('/etc/btrfs-snapshot-manager/config.yml')

    config_spec = {
        ('subvolumes', False): [
            {
                ('path', True): str,
                ('snapshots-path', False): str,
                ('retention', True): {
                    ('hourly', (1, None, 'hourly', 'daily', 'weekly', 'monthly')): int,
                    ('daily', False): int,
                    ('weekly', False): int,
                    ('monthly', False): int,
                },
                ('backup', False): [
                    {
                        ('type', True): ('btrfs', 'rsync'),
                        ('last_sync_file', False): str,
                        ('local', (1, 1, 'local', 'remote')): {
                            ('path', True): str,
                        },
                        ('remote', False): {
                            ('host', True): str,
                            ('user', False): str,
                            ('ssh-options', False): str,
                            ('path', True): str,
                        },
                        ('retention', True): {
                            ('hourly', (1, None, 'hourly', 'daily', 'weekly', 'monthly')): int,
                            ('daily', False): int,
                            ('weekly', False): int,
                            ('monthly', False): int,
                            ('minimum', False): int,
                        },
                    },
                ],
                ('systemd-boot', False): [
                    {
                        ('entry', True): str,
                        ('retention', True): {
                            ('hourly', (1, None, 'hourly', 'daily', 'weekly', 'monthly')): int,
                            ('daily', False): int,
                            ('weekly', False): int,
                            ('monthly', False): int,
                        },
                    },
                ],
            },
        ],
        ('systemd-boot', False): {
            ('boot-path', False): str,
            ('init-files', False): [
                str,
            ],
        },
    }

    def __init__(self, snapshot_manager):
        self.snapshot_manager = snapshot_manager
        self.load_config()
        self.load_retention()
        self.load_backups()
        self.load_systemdboot()

    def load_config(self):
        if not self.config_file.is_file():
            self.raw_config = {}
        else:
            with open(self.config_file, 'r') as fh:
                config = yaml.load(fh, Loader=yaml.CLoader)
            if config is None:
                self.raw_config = {}
            else:
                self.raw_config = config
        ConfigValidator.validate_config(self.raw_config, self.config_spec, [], True)

    def get_subvolume_config(self):
        config = {}
        if 'subvolumes' in self.raw_config:
            for subvol_config in self.raw_config['subvolumes']:
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
                self.subvolumes[subvol].set_snapshot_dir(subvol_config['snapshots-path'])

            subvol_retention = {}
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
            if 'backup' in subvol_config:
                for backup_config in subvol_config['backup']:

                    backup_type = backup_config['type']

                    if 'local' in backup_config:
                        path = backup_config['local']['path']

                        if backup_type == 'btrfs':
                            backup = LocalBtrfsBackup(subvol_instance, path)
                        elif backup_type == 'rsync':
                            backup = LocalRsyncBackup(subvol_instance, path)

                    else:
                        host = backup_config['remote']['host']

                        path = backup_config['remote']['path']

                        user = None
                        if 'user' in backup_config['remote']:
                            user = backup_config['remote']['user']

                        ssh_options = None
                        if 'ssh-options' in backup_config['remote']:
                            ssh_options = backup_config['remote']['ssh-options']

                        if backup_type == 'btrfs':
                            backup = RemoteBtrfsBackup(subvol_instance, host, user, ssh_options, path)
                        elif backup_type == 'rsync':
                            backup = RemoteRsyncBackup(subvol_instance, host, user, ssh_options, path)

                    for period in PERIODS:
                        if period.name in backup_config['retention']:
                            backup.retention[period] = int(backup_config['retention'][period.name])
                    if 'minimum' in backup_config['retention']:
                        backup.retention_minimum = int(backup_config['retention']['minimum'])
                    if 'last_sync_file' in backup_config:
                        backup.last_sync_file = backup_config['last_sync_file']

                    self.backups[subvol].append(backup)

    def load_systemdboot(self):
        self.systemdboot_manager = None

        if 'systemd-boot' in self.raw_config:
            systemdboot_config = self.raw_config['systemd-boot']
            systemdboot_manager = SystemdBootManager()
            self.systemdboot_manager = systemdboot_manager
            if 'boot-path' in systemdboot_config:
                systemdboot_manager.set_boot_path(systemdboot_config['boot-path'])
            if 'init-files' in systemdboot_config:
                systemdboot_manager.set_init_file_list(systemdboot_config['init-files'])

        config = self.get_subvolume_config()
        for subvol, subvol_config in config.items():
            subvol_instance = self.subvolumes[subvol]

            if 'systemd-boot' in subvol_config:
                if self.systemdboot_manager is None:
                    systemdboot_manager = SystemdBootManager()
                    self.systemdboot_manager = systemdboot_manager

                systemdboot_config = subvol_config['systemd-boot']

                subvol_instance.systemdboot_manager = systemdboot_manager

                for systemdboot_config_entry in systemdboot_config:

                    entry = systemdboot_config_entry['entry']

                    retention = {}
                    for period in PERIODS:
                        if period.name in systemdboot_config_entry['retention']:
                            retention[period] = int(systemdboot_config_entry['retention'][period.name])

                    systemdbootentry = SystemdBootEntryManager(self.systemdboot_manager, subvol_instance, entry, retention)

                    if 'boot-path' in systemdboot_config:
                        systemdbootentry.set_boot_path(systemdboot_config['boot-path'])

                    self.systemdboot_manager.entry_managers.append(systemdbootentry)
