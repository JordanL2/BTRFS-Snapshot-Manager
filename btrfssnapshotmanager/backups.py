#!/usr/bin/python3

from btrfssnapshotmanager.snapshots import *


class Backup():

    def __init__(self, subvol):
        self.subvol = Subvolume(subvol)


class LocalBackup(Backup):

    transport = 'local'

    def __init__(self, subvol, path):
        self.path = path
        super().__init__(subvol)


class RemoteBackup(Backup):

    transport = 'remote'

    def __init__(self, subvol, host, user, ssh_options, path):
        self.host = host
        self.user = user
        self.ssh_options = ssh_options
        self.path = path
        super().__init__(subvol)


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
