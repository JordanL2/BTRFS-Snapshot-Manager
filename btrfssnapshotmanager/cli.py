#!/usr/bin/python3

from btrfssnapshotmanager.manager import *

import argparse
import sys


dateformat_human =  '%a %d %b %Y %H:%M:%S'


def main():
    parser = argparse.ArgumentParser(prog='btrfs-snapshot-manager')
    subparsers = parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # backup
    backup_parser = subparsers.add_parser('backup', help='backup-related commands')
    backup_subparsers = backup_parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # backup list
    backup_list_parser = backup_subparsers.add_parser('list', help='show all configured backups')
    backup_list_parser.add_argument('path', nargs='?', help='path to subvolume')
    backup_list_parser.set_defaults(func=backup_list)

    # backup run
    backup_run_parser = backup_subparsers.add_parser('run', help='run backups')
    backup_run_parser.add_argument('path', nargs='?', help='path to subvolume')
    backup_run_parser.add_argument('--id', nargs='*', help='only run backups with these ids')
    backup_run_parser.set_defaults(func=backup_run)

    # schedule
    schedule_parser = subparsers.add_parser('schedule', help='schedule-related commands')
    schedule_subparsers = schedule_parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # schedule run
    schedule_run_parser = schedule_subparsers.add_parser('run', help='execute scheduled snapshots')
    schedule_run_parser.add_argument('path', nargs='*', help='path to subvolume')
    schedule_run_parser.set_defaults(func=schedule_run)

    # schedule list
    schedule_list_parser = schedule_subparsers.add_parser('list', help='list snapshot schedules')
    schedule_list_parser.add_argument('path', nargs='?', help='path to subvolume')
    schedule_list_parser.set_defaults(func=schedule_list)

    # snapshot
    snapshot_parser = subparsers.add_parser('snapshot', help='snapshot-related commands')
    snapshot_subparsers = snapshot_parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # snapshot create
    snapshot_create_parser = snapshot_subparsers.add_parser('create', help='create snapshot')
    snapshot_create_parser.add_argument('path', help='path to subvolume')
    snapshot_create_parser.set_defaults(func=snapshot_create)

    # snapshot delete
    snapshot_delete_parser = snapshot_subparsers.add_parser('delete', help='delete snapshot')
    snapshot_delete_parser.add_argument('path', help='path to subvolume')
    snapshot_delete_parser.add_argument('name', help='snapshot name to delete')
    snapshot_delete_parser.set_defaults(func=snapshot_delete)

    # snapshot init
    snapshot_init_parser = snapshot_subparsers.add_parser('init', help='initialise this subvolume for snapshots')
    snapshot_init_parser.add_argument('path', help='path to subvolume')
    snapshot_init_parser.set_defaults(func=snapshot_init)

    # snapshot list
    snapshot_list_parser = snapshot_subparsers.add_parser('list', help='list snapshots')
    snapshot_list_parser.add_argument('path', help='path to subvolume')
    snapshot_list_parser.add_argument('--details', required=False, default=False, action='store_true', help='output detailed list')
    snapshot_list_parser.add_argument('--period', nargs='*', help='only list snapshots for this period')
    snapshot_list_parser.set_defaults(func=snapshot_list)

    # systemdboot
    systemdboot_parser = subparsers.add_parser('systemdboot', help='systemdboot-related commands')
    systemdboot_subparsers = systemdboot_parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # systemdboot create
    systemdboot_create_parser = systemdboot_subparsers.add_parser('create', help='create a systemd-boot entry for a given snapshot')
    systemdboot_create_parser.add_argument('snapshot', help='name of snapshot to make boot entry for')
    systemdboot_create_parser.set_defaults(func=systemdboot_create)

    # systemdboot delete
    systemdboot_delete_parser = systemdboot_subparsers.add_parser('delete', help='delete a systemd-boot entry')
    systemdboot_delete_parser.add_argument('entry', help='name of boot entry file to delete')
    systemdboot_delete_parser.set_defaults(func=systemdboot_delete)

    # systemdboot list
    systemdboot_list_parser = systemdboot_subparsers.add_parser('list', help='list all systemd-boot snapshot boot entries')
    systemdboot_list_parser.set_defaults(func=systemdboot_list)

    # systemdboot show
    systemdboot_show_parser = systemdboot_subparsers.add_parser('show', help='show configured systemd-boot integration')
    systemdboot_show_parser.set_defaults(func=systemdboot_show)

    args = parser.parse_args()
    try:
        args.func(args)
    except SnapshotException as e:
        fail(e.error)


# Backups

def backup_list(args):
    path = args.path
    snapshot_manager = SnapshotManager()

    if path is not None and path not in snapshot_manager.managers:
        fail("Config not found for subvolume", path)

    table = []
    for subvol, manager in snapshot_manager.managers.items():
        if path is None or subvol == path:
            if len(manager.backups) > 0:
                if len(table) > 0:
                    table.append(None)
                table.append([subvol, 'LOCATION', 'MECHANISM', *[p.name.upper() for p in PERIODS]])
                for i, backup in enumerate(manager.backups):
                    row = [i]
                    row.append(backup.location())
                    row.append(backup.mechanism)

                    for p in PERIODS:
                        if p in backup.retention:
                            row.append(backup.retention[p])
                        else:
                            row.append('')

                    table.append(row)

    output_table(table)

def backup_run(args):
    path = args.path
    ids = args.id
    if ids is not None:
        ids = [int(i) for i in ids]
    snapshot_manager = SnapshotManager()

    if path is not None and path not in snapshot_manager.managers:
        fail("Config not found for subvolume", path)

    empty_line = False
    for subvol, manager in snapshot_manager.managers.items():
        if path is None or subvol == path:
            if len(manager.backups) > 0:
                if empty_line:
                    info()
                manager.backup(ids=ids)
                empty_line = True

# Schedule

def schedule_run(args):
    paths = args.path
    snapshot_manager = SnapshotManager()
    if paths is not None:
        for path in paths:
            if path not in snapshot_manager.managers:
                fail("Config not found for subvolume", path)

    snapshot_manager.execute(subvols=paths)

def schedule_list(args):
    path = args.path
    snapshot_manager = SnapshotManager()
    if path is not None and path not in snapshot_manager.managers:
        fail("Config not found for subvolume", path)

    table = []
    for subvol, manager in snapshot_manager.managers.items():
        if path is None or subvol == path:
            if len(manager.retention_config) > 0:
                if len(table) > 0:
                    table.append(None)
                table.append([subvol, 'LAST RUN', 'NEXT RUN'])
                for period in sorted(manager.retention_config.keys(), key=lambda p: p.seconds):
                    row = []
                    row.append(period.name)

                    last_run = manager.last_run(period)
                    if last_run is None:
                        last_run = 'Never'
                    else:
                        last_run = last_run.strftime(dateformat_human)
                    row.append(last_run)

                    next_run = manager.next_run(period)
                    if next_run is None:
                        next_run = 'Immediately'
                    else:
                        next_run = next_run.strftime(dateformat_human)
                    row.append(next_run)

                    table.append(row)

    output_table(table)


# Snapshots

def snapshot_create(args):
    path = args.path
    subvol = get_subvol(path)
    snapshot = subvol.create_snapshot()
    out("Created snapshot", snapshot.name, "in subvolume", path)

def snapshot_delete(args):
    path = args.path
    name = args.name
    subvol = get_subvol(path)
    snapshot = subvol.find_snapshot(name)
    if snapshot is None:
        fail("Could not find snapshot", name, "in subvolume", path)
    snapshot.delete()
    out("Deleted snapshot", name, "from subvolume", path)

def snapshot_init(args):
    path = args.path
    subvol = get_subvol(path)
    subvol.init_snapshots()
    out("Initialised subvolume", path, "for snapshots")

def snapshot_list(args):
    path = args.path
    details = args.details
    periods = args.period
    if periods is not None:
        for p in periods:
            if p != 'none' and p not in PERIOD_NAME_MAP:
                fail("No such period:", p)
        periods = [(PERIOD_NAME_MAP[p] if p != 'none' else None) for p in periods]

    subvol = get_subvol(path)
    if not subvol.has_snapshots():
        fail("Subvolume", path, "is not initialised for snapshots")

    snapshots = subvol.search_snapshots(periods=periods)
    if details:
        table = [['NAME', 'DATE', 'PERIODS']]
        for snapshot in snapshots:
            table.append([snapshot.name, snapshot.date.strftime(dateformat_human), ', '.join([p.name for p in snapshot.get_periods()])])
        output_table(table)
    else:
        for snapshot in snapshots:
            out(snapshot.name)


# Systemd-Boot

def systemdboot_create(args):
    snapshot_name = args.snapshot
    snapshot_manager = SnapshotManager()
    systemdboot = get_systemdboot(snapshot_manager)
    if systemdboot is None:
        fail("No subvolumes configured for systemd-boot integration")

    snapshot = systemdboot.subvol.find_snapshot(snapshot_name)
    if snapshot is None:
        fail("Snapshot {0} not found in subvolume {1}".format(snapshot_name, systemdboot.subvol.name))

    systemdboot.create_entry(snapshot)

def systemdboot_delete(args):
    entry_name = args.entry
    snapshot_manager = SnapshotManager()
    systemdboot = get_systemdboot(snapshot_manager)
    if systemdboot is None:
        fail("No subvolumes configured for systemd-boot integration")

    systemdboot.delete_entry(entry_name)
    out("Deleted systemd-boot entry {0}".format(entry_name))

def systemdboot_list(args):
    snapshot_manager = SnapshotManager()
    systemdboot = get_systemdboot(snapshot_manager)
    if systemdboot is not None:
        table = [['ENTRY', 'SNAPSHOT', 'DATE', 'PERIODS']]

        for entry, snapshot in systemdboot.entries.items():
            if snapshot is not None:
                table.append([
                    entry,
                    snapshot.name,
                    snapshot.date.strftime(dateformat_human),
                    ', '.join([p.name for p in snapshot.get_periods()]),
                ])
            else:
                table.append([
                    entry,
                    'NOT FOUND',
                    '',
                    '',
                ])

        output_table(table)

def systemdboot_show(args):
    snapshot_manager = SnapshotManager()
    systemdboot = get_systemdboot(snapshot_manager)
    if systemdboot is not None:
        table = []
        table.append(['SUBVOLUME', systemdboot.subvol.name])
        table.append(['BOOT PATH', systemdboot.boot_path])
        table.append(['ENTRY', systemdboot.entry])
        for p in PERIODS:
            if p in systemdboot.retention:
                table.append([p.name.upper(), systemdboot.retention[p]])
        output_table(table)


# General

def get_subvol(path):
    snapshot_manager = SnapshotManager()
    if path in snapshot_manager.managers:
        return snapshot_manager.managers[path].subvol
    return Subvolume(path)

def get_systemdboot(snapshot_manager):
    for subvol, manager in snapshot_manager.managers.items():
        if manager.systemdboot is not None:
            return manager.systemdboot
    return None

def out(*messages):
    print(' '.join([str(m) for m in messages]), flush=True)

def err(*messages):
    print(' '.join([str(m) for m in messages]), flush=True, file=sys.stderr)

def fail(*messages):
    err(*messages)
    sys.exit(1)

def output_table(table):
    if len(table) == 0:
        return
    max_width = []
    for i in range(0, len(table[0])):
        max_width.append(max([(len(str(r[i])) if r is not None else 0) for r in table]))
    for r in table:
        if r is None:
            out()
        else:
            out(' | '.join([
                format(str(c), "<{0}".format(max_width[i])) for i, c in enumerate(r)
            ]))


if __name__ == '__main__':
    main()
