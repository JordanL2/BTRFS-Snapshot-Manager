#!/usr/bin/python3

from btrfssnapshotmanager.snapshots import *


class Backup():

    def __init__(self, subvol, retention):
        self.subvol = Subvolume(subvol)
        self.retention = retention


class LocalBackup(Backup):

    transport = 'local'

    def __init__(self, subvol, retention, path):
        self.path = path
        super().__init__(subvol, retention)


class RemoteBackup(Backup):

    transport = 'remote'

    def __init__(self, subvol, retention, host, user, ssh_options, path):
        self.host = host
        self.user = user
        self.ssh_options = ssh_options
        self.path = path
        super().__init__(subvol, retention)


class LocalBtrfsBackup(LocalBackup):

    mechanism = 'btrfs'

    def backup(self):
        pass


class RemoteBtrfsBackup(RemoteBackup):

    mechanism = 'btrfs'

    def backup(self):
        pass


class LocalRsyncBackup(LocalBackup):

    mechanism = 'rsync'

    def backup(self):
        pass


class RemoteRsyncBackup(RemoteBackup):

    mechanism = 'rsync'

    def backup(self):
        pass
