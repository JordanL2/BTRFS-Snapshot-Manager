#!/usr/bin/python3

from btrfssnapshotmanager.config import *
from btrfssnapshotmanager.snapshots import *


class Backup():

    def __init__(self, subvol, retention):
        self.subvol = Subvolume(subvol)
        self.retention = retention

    def backup(self):
        # Get list of source snapshots that should be on the target
        source_snapshots = set()
        for period in self.retention:
            period_snapshots = self.subvol.search_snapshots(periods=[period])
            if len(period_snapshots) > self.retention[period]:
                period_snapshots = period_snapshots[len(period_snapshots) - self.retention[period]:]
            for s in period_snapshots:
                source_snapshots.add(s)
        source_snapshots = sorted(list(source_snapshots), key=lambda s: s.name)
        source_snapshot_names = [s.name for s in source_snapshots]

        # Get list of snapshots that exist on the target
        target_snapshot_names = self.get_target_snapshot_names()

        # Delete target snapshots not needed any more
        for target_snapshot_name in target_snapshot_names:
            if target_snapshot_name not in source_snapshot_names:
                self.delete_target(target_snapshot_name)

        # Upload source snapshots not found on target
        for i, source_snapshot in enumerate(source_snapshots):
            if source_snapshot.name not in target_snapshot_names:
                if i > 0:
                    self.transfer_source_delta(source_snapshots[i - 1], source_snapshot)
                else:
                    self.transfer_source(source_snapshot)

    def get_target_snapshot_names(self):
        raise Exception("Method must be overridden")

    def transfer_source(self, source):
        raise Exception("Method must be overridden")

    def transfer_source_delta(self, previous_source, source):
        raise Exception("Method must be overridden")

    def delete_target(self, target_name):
        raise Exception("Method must be overridden")


class LocalBackup(Backup):

    transport = 'local'

    def __init__(self, subvol, retention, path):
        self.path = path
        super().__init__(subvol, retention)

    def location(self):
        return self.path

    def get_target_snapshot_names(self):
        info("Fetching list of snapshots on target " + self.location())
        #TODO
        return []

    def delete_target(self, target_name):
        info("Deleting snapshot {0} on target {1}".format(target_name, self.location()))
        #TODO

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

    def get_target_snapshot_names(self):
        info("Fetching list of snapshots on target " + self.location())
        #TODO
        return []

    def delete_target(self, target_name):
        info("Deleting snapshot {0} on target {1}".format(target_name, self.location()))
        #TODO


class LocalBtrfsBackup(LocalBackup):

    mechanism = 'btrfs'

    def transfer_source(self, source):
        info("Transferring via btrfs snapshot {0} to target {1}".format(source.name, self.location()))
        #TODO

    def transfer_source_delta(self, previous_source, source):
        info("Transferring via btrfs snapshot {0} (as delta from {1}) to target {2}".format(source.name, previous_source.name, self.location()))
        #TODO


class RemoteBtrfsBackup(RemoteBackup):

    mechanism = 'btrfs'

    def transfer_source(self, source):
        info("Transferring via btrfs snapshot {0} to target {1}".format(source.name, self.location()))
        #TODO

    def transfer_source_delta(self, previous_source, source):
        info("Transferring via btrfs snapshot {0} (as delta from {1}) to target {2}".format(source.name, previous_source.name, self.location()))
        #TODO


class LocalRsyncBackup(LocalBackup):

    mechanism = 'rsync'

    def transfer_source(self, source):
        info("Transferring via rsync snapshot {0} to target {1}".format(source.name, self.location()))
        #TODO

    def transfer_source_delta(self, previous_source, source):
        info("Transferring via rsync snapshot {0} (as delta from {1}) to target {2}".format(source.name, previous_source.name, self.location()))
        #TODO


class RemoteRsyncBackup(RemoteBackup):

    mechanism = 'rsync'

    def transfer_source(self, source):
        info("Transferring via rsync snapshot {0} to target {1}".format(source.name, self.location()))
        #TODO

    def transfer_source_delta(self, previous_source, source):
        info("Transferring via rsync snapshot {0} (as delta from {1}) to target {2}".format(source.name, previous_source.name, self.location()))
        #TODO
