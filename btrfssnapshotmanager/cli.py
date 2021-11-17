#!/usr/bin/python3

from btrfssnapshotmanager.config import *
from btrfssnapshotmanager.snapshots import *

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(prog='btrfs-snapshot-manager')
    subparsers = parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # schedule
    schedule_parser = subparsers.add_parser('schedule', help='schedule-related commands')
    schedule_subparsers = schedule_parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # schedule list
    schedule_list_parser = schedule_subparsers.add_parser('list', help='list snapshot schedules')
    schedule_list_parser.add_argument('--path', help='path to subvolume')
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
    snapshot_list_parser.set_defaults(func=snapshot_list)

    args = parser.parse_args()
    try:
        args.func(args)
    except SnapshotException as e:
        fail(e.error)


# Schedule

def schedule_list(args):
    path = args.path
    config = Config()
    schedules = config.schedules
    if path is not None and path not in schedules:
        fail("Schedule not found for subvolume", path)
    for subvol, schedule in schedules.items():
        if path is None or subvol == path:
            out(subvol)
            for period in sorted(schedule.keys(), key=lambda p: p.seconds):
                out("  {0} {1}".format(
                    format(period.name, "<{0}".format(periods_max_name_length)),
                    schedule[period]))
            out()


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
    subvol = Subvolume(path)
    if subvol.snapshots is None:
        fail("Subvolume", path, "is not initialised for snapshots")
    if details:
        maxlen = max([len(s.name) for s in subvol.snapshots])
        for snapshot in subvol.snapshots:
            out("{0} | {1} | {2}".format(
                format(snapshot.name, "<{0}".format(maxlen)),
                snapshot.date.strftime('%a %d %b %Y %H:%M:%S'),
                ', '.join([p.name for p in snapshot.tags.periods()])
            ))
    else:
        for snapshot in subvol.snapshots:
            out(snapshot.name)


# General

def out(*messages):
    print(' '.join([str(m) for m in messages]), flush=True)

def err(*messages):
    print(' '.join([str(m) for m in messages]), flush=True, file=sys.stderr)

def fail(*messages):
    err(*messages)
    sys.exit(1)


if __name__ == '__main__':
    main()
