#!/usr/bin/python3

from btrfssnapshotmanager.scheduler import *
from btrfssnapshotmanager.snapshots import *

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

    # schedule execute
    schedule_execute_parser = schedule_subparsers.add_parser('execute', help='execute snapshot schedules')
    schedule_execute_parser.set_defaults(func=schedule_execute)

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

    args = parser.parse_args()
    try:
        args.func(args)
    except SnapshotException as e:
        fail(e.error)


# Backups

def backup_list(args):
    path = args.path
    schedule_manager = ScheduleManager()

    if path is not None and path not in schedule_manager.schedulers:
        fail("Config not found for subvolume", path)

    table = []
    for subvol, scheduler in schedule_manager.schedulers.items():
        if path is None or subvol == path:
            if len(scheduler.backups) > 0:
                if len(table) > 0:
                    table.append(None)
                table.append([subvol, 'LOCATION', 'MECHANISM', *[p.name.upper() for p in PERIODS]])
                for i, backup in enumerate(scheduler.backups):
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
    schedule_manager = ScheduleManager()

    if path is not None and path not in schedule_manager.schedulers:
        fail("Config not found for subvolume", path)

    for subvol, scheduler in schedule_manager.schedulers.items():
        if path is None or subvol == path:
            if len(scheduler.backups) > 0:
                scheduler.backup(ids=ids)


# Schedule

def schedule_execute(args):
    schedule_manager = ScheduleManager()
    schedule_manager.execute()

def schedule_list(args):
    path = args.path
    schedule_manager = ScheduleManager()
    if path is not None and path not in schedule_manager.schedulers:
        fail("Config not found for subvolume", path)

    table = []
    for subvol, scheduler in schedule_manager.schedulers.items():
        if path is None or subvol == path:
            if len(scheduler.config) > 0:
                if len(table) > 0:
                    table.append(None)
                table.append([subvol, 'LAST RUN', 'NEXT RUN'])
                for period in sorted(scheduler.config.keys(), key=lambda p: p.seconds):
                    row = []
                    row.append(period.name)

                    last_run = scheduler.last_run(period)
                    if last_run is None:
                        last_run = 'Never'
                    else:
                        last_run = last_run.strftime(dateformat_human)
                    row.append(last_run)

                    next_run = scheduler.next_run(period)
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
    subvol = Subvolume(path)
    snapshot = subvol.create_snapshot()
    out("Created snapshot", snapshot.name, "in subvolume", path)

def snapshot_delete(args):
    path = args.path
    name = args.name
    subvol = Subvolume(path)
    snapshot = subvol.find_snapshot(name)
    if snapshot is None:
        fail("Could not find snapshot", name, "in subvolume", path)
    snapshot.delete()
    out("Deleted snapshot", name, "from subvolume", path)

def snapshot_init(args):
    path = args.path
    subvol = Subvolume(path)
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

    subvol = Subvolume(path)
    if subvol.snapshots is None:
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


# General

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
