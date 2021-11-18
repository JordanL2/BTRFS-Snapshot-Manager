#!/usr/bin/python3

from btrfssnapshotmanager.snapshots import *


class Backup():

    def __init__(self, subvol, retention):
        self.subvol = Subvolume(subvol)
        self.retention = retention

    def backup(self):
        pass


class LocalBackup(Backup):

    transport = 'local'

    def __init__(self, subvol, retention, path):
        self.path = path
        super().__init__(subvol, retention)

    def location(self):
        return self.path


class RemoteBackup(Backup):

    transport = 'remote'

    def __init__(self, subvol, retention, host, user, ssh_options, path):
        self.host = host
        self.user = user
        self.ssh_options = ssh_options
        self.path = path
        super().__init__(subvol, retention)

    def location(self):
        return "{0}:{1}".format(self.host, self.path)


class LocalBtrfsBackup(LocalBackup):

    mechanism = 'btrfs'


class RemoteBtrfsBackup(RemoteBackup):

    mechanism = 'btrfs'


class LocalRsyncBackup(LocalBackup):

    mechanism = 'rsync'


class RemoteRsyncBackup(RemoteBackup):

    mechanism = 'rsync'
