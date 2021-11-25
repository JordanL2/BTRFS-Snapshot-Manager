#!/usr/bin/python3

from btrfssnapshotmanager.snapshots import *

from pathlib import PosixPath, PurePosixPath


class Backup():

    def __init__(self, subvol, retention):
        self.subvol = subvol
        self.retention = retention
        self.last_sync_file = None

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
        debug("Identified the following {0} snapshots that should be on target {1}:".format(self.subvol.name, self.location()))
        for s in source_snapshot_names:
            debug("-", s)

        # Get list of snapshots that exist on the target
        self.ensure_target_exists()
        target_snapshot_names = self.get_target_snapshot_names()
        debug("Found the following {0} snapshots that exist on target {1}:".format(self.subvol.name, self.location()))
        for s in target_snapshot_names:
            debug("-", s)

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

        # Declare successful sync
        if self.last_sync_file is not None:
            last_sync_file = PosixPath(self.subvol.snapshots_dir, self.last_sync_file)
            info("Touching file {0} to indicate successful backup sync between {1} and {2}".format(last_sync_file, self.subvol.name, self.location()))
            cmd("touch {0}".format(last_sync_file))

    def location(self):
        raise Exception("Method must be overridden")

    def ensure_target_exists(self):
        raise Exception("Method must be overridden")

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
        self.path = PosixPath(path)
        super().__init__(subvol, retention)

    def location(self):
        return str(self.path)

    def ensure_target_exists(self):
        if not self.path.is_dir():
            info("Target location doesn't exist, creating {0}".format(self.location()))
            self.path.mkdir(mode=0o700, parents=True)

    def get_target_snapshot_names(self):
        debug("Fetching list of snapshots on target {0}".format(self.location()))
        names = []
        for child in self.path.iterdir():
            if child.is_dir():
                snapshot_details = snapshot_name_parse(child.name)
                if snapshot_details is not None:
                    names.append(child.name)

        return names


class RemoteBackup(Backup):

    transport = 'remote'

    def __init__(self, subvol, retention, host, user, ssh_options, path):
        self.host = host
        self.user = user
        self.ssh_options = ssh_options
        self.path = PurePosixPath(path)
        self.cmd_attempts = 3
        self.cmd_fail_delay = 10
        super().__init__(subvol, retention)

    def location(self):
        return "{0}:{1}".format(self.host, self.path)

    def ensure_target_exists(self):
        exists = cmd("{0} \"if [[ -d '{1}' ]] ; then echo 'yes' ; fi\"".format(self._ssh_command(), self.path), attempts=self.cmd_attempts, fail_delay=self.cmd_fail_delay)
        if exists != 'yes':
            info("Target location doesn't exist, creating {0}".format(self.location()))
            cmd("{0} \"sudo mkdir -p {1}\"".format(self._ssh_command(), self.path), attempts=self.cmd_attempts, fail_delay=self.cmd_fail_delay)

    def get_target_snapshot_names(self):
        debug("Fetching list of snapshots on target " + self.location())
        out = cmd("{0} \"ls -1 {1}\"".format(self._ssh_command(), self.path), attempts=self.cmd_attempts, fail_delay=self.cmd_fail_delay)
        names = []
        remote_files = [n.strip() for n in out.split("\n") if n.strip() != '']
        for remote_file in remote_files:
            snapshot_details = snapshot_name_parse(remote_file)
            if snapshot_details is not None:
                names.append(remote_file)
        return names

    def _ssh_command(self):
        ssh_command = "ssh "
        if self.ssh_options is not None:
            ssh_command += self.ssh_options + " "
        if self.user is not None:
            ssh_command += self.user + "@"
        ssh_command += self.host
        return ssh_command


# Btrfs

class LocalBtrfsBackup(LocalBackup):

    mechanism = 'btrfs'

    def transfer_source(self, source):
        info("Transferring via btrfs snapshot {0} to target {1}".format(source.path, self.location()))
        cmd("btrfs send {0} | btrfs receive {1}".format(source.path, self.path, source.name))

    def transfer_source_delta(self, previous_source, source):
        info("Transferring via btrfs snapshot {0} (as delta from {1}) to target {2}".format(source.path, previous_source.path, self.location()))
        cmd("btrfs send -p {0} {1} | btrfs receive {2}".format(previous_source.path, source.path, self.path))

    def delete_target(self, target_name):
        info("Deleting via btrfs snapshot {0} on target {1}".format(target_name, self.location()))
        cmd("btrfs subvolume delete --commit-each {0}".format(PosixPath(self.path, target_name)))


class RemoteBtrfsBackup(RemoteBackup):

    mechanism = 'btrfs'

    def transfer_source(self, source):
        info("Transferring via btrfs snapshot {0} to target {1}".format(source.path, self.location()))
        cmd("btrfs send {0} | {1} \"sudo btrfs receive {2}\"".format(source.path, self._ssh_command(), self.path),
            attempts=self.cmd_attempts, fail_delay=self.cmd_fail_delay)

    def transfer_source_delta(self, previous_source, source):
        info("Transferring via btrfs snapshot {0} (as delta from {1}) to target {2}".format(source.path, previous_source.path, self.location()))
        cmd("btrfs send -p {0} {1} | {2} \"sudo btrfs receive {3}\"".format(previous_source.path, source.path, self._ssh_command(), self.path),
            attempts=self.cmd_attempts, fail_delay=self.cmd_fail_delay)

    def delete_target(self, target_name):
        info("Deleting via btrfs snapshot {0} on target {1}".format(target_name, self.location()))
        cmd("{0} \"sudo btrfs subvolume delete {1}/{2}\"".format(self._ssh_command(), self.path, target_name),
            attempts=self.cmd_attempts, fail_delay=self.cmd_fail_delay)


# Rsync

class RsyncBackup():

    def temp_path(self):
        return PosixPath(self.path, '.tmp')

    def temp_location(self):
        raise Exception("Method must be overridden")


class LocalRsyncBackup(LocalBackup, RsyncBackup):

    mechanism = 'rsync'

    def temp_location(self):
        return self.temp_path()

    def ensure_target_exists(self):
        super().ensure_target_exists()
        if not self.temp_path().is_dir():
            info("Target temp location doesn't exist, creating {0}".format(self.temp_path()))
            self.temp_path().mkdir(mode=0o700, parents=True)

    def transfer_source(self, source):
        info("Transferring via rsync snapshot {0} to target temp {1}".format(source.path, self.temp_location()))
        cmd("rsync -a --delete {0} {1}/".format(source.path, self.temp_path()))
        self.move_target_snapshot_from_temp(source)

    def transfer_source_delta(self, previous_source, source):
        info("Transferring via rsync snapshot {0} (as delta from {1}) to target temp {2}".format(source.path, previous_source.path, self.temp_location()))
        cmd("rsync -a --delete --link-dest={4}/{2}/ {0}/ {1}/{3}".format(source.path, self.temp_path(), previous_source.name, source.name, self.path))
        self.move_target_snapshot_from_temp(source)

    def delete_target(self, target_name):
        info("Deleting via rsync snapshot {0} on target {1}".format(target_name, self.location()))
        cmd("rm -rf {0}".format(PosixPath(self.path, target_name)))

    def move_target_snapshot_from_temp(self, source):
        move_from = PosixPath(self.temp_path(), source.name)
        move_to = PosixPath(self.path, source.name)
        info("Moving via rsync target snapshot {0} to {1}".format(move_from, move_to))
        cmd("mv {0} {1}".format(move_from, move_to))


class RemoteRsyncBackup(RemoteBackup, RsyncBackup):

    mechanism = 'rsync'

    def temp_location(self):
        return "{0}:{1}".format(self.host, self.temp_path())

    def ensure_target_exists(self):
        super().ensure_target_exists()
        exists = cmd("{0} \"if [[ -d '{1}' ]] ; then echo 'yes' ; fi\"".format(self._ssh_command(), self.temp_path()), attempts=self.cmd_attempts, fail_delay=self.cmd_fail_delay)
        if exists != 'yes':
            info("Target temp location doesn't exist, creating {0}".format(self.temp_location()))
            cmd("{0} \"sudo mkdir -p {1}\"".format(self._ssh_command(), self.temp_path()), attempts=self.cmd_attempts, fail_delay=self.cmd_fail_delay)

    def transfer_source(self, source):
        info("Transferring via rsync snapshot {0} to target temp {1}".format(source.path, self.temp_location()))
        cmd("rsync -a --delete --rsync-path=\"sudo rsync\" -e \"ssh {0} -l {1}\" {3} {2}:{4}/".format(
                self.ssh_options, self.user, self.host, source.path, self.temp_path()),
            attempts=self.cmd_attempts, fail_delay=self.cmd_fail_delay)
        self.move_target_snapshot_from_temp(source)

    def transfer_source_delta(self, previous_source, source):
        info("Transferring via rsync snapshot {0} (as delta from {1}) to target temp {2}".format(source.path, previous_source.path, self.temp_location()))
        cmd("rsync -a --delete --link-dest={7}/{6}/ --rsync-path=\"sudo rsync\" -e \"ssh {0} -l {1}\" {3}/ {2}:{5}/{4}/".format(
                self.ssh_options, self.user, self.host, source.path, source.name, self.temp_path(), previous_source.name, self.path),
            attempts=self.cmd_attempts, fail_delay=self.cmd_fail_delay)
        self.move_target_snapshot_from_temp(source)

    def delete_target(self, target_name):
        info("Deleting via rsync snapshot {0} on target {1}".format(target_name, self.location()))
        cmd("{0} \"sudo rm -rf {1}/{2}\"".format(self._ssh_command(), self.path, target_name),
            attempts=self.cmd_attempts, fail_delay=self.cmd_fail_delay)

    def move_target_snapshot_from_temp(self, source):
        move_from = PosixPath(self.temp_path(), source.name)
        move_to = PosixPath(self.path, source.name)
        info("Moving via rsync target snapshot {0} to {1}".format(move_from, move_to))
        cmd("{0} \"sudo mv {1} {2}\"".format(self._ssh_command(), move_from, move_to))
