#!/usr/bin/python3

from btrfssnapshotmanager.snapshots import *

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(prog='btrfs-snapshot-manager')
    subparsers = parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # snapshots
    snapshots_parser = subparsers.add_parser('snapshots', help='snapshot-related commands')
    snapshots_subparsers = snapshots_parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # snapshots create
    snapshots_create_parser = snapshots_subparsers.add_parser('create', help='create snapshot')
    snapshots_create_parser.add_argument('path', help='path to subvolume')
    snapshots_create_parser.set_defaults(func=snapshots_create)

    # snapshots delete
    snapshots_delete_parser = snapshots_subparsers.add_parser('delete', help='delete snapshot')
    snapshots_delete_parser.add_argument('path', help='path to subvolume')
    snapshots_delete_parser.add_argument('name', help='snapshot name to delete')
    snapshots_delete_parser.set_defaults(func=snapshots_delete)

    # snapshots init
    snapshots_init_parser = snapshots_subparsers.add_parser('init', help='initialise this subvolume for snapshots')
    snapshots_init_parser.add_argument('path', help='path to subvolume')
    snapshots_init_parser.set_defaults(func=snapshots_init)

    # snapshots list
    snapshots_list_parser = snapshots_subparsers.add_parser('list', help='list snapshots')
    snapshots_list_parser.add_argument('path', help='path to subvolume')
    snapshots_list_parser.add_argument('--details', required=False, default=False, action='store_true', help='output detailed list')
    snapshots_list_parser.set_defaults(func=snapshots_list)

    args = parser.parse_args()
    try:
        args.func(args)
    except SnapshotException as e:
        fail(e.error)


def snapshots_create(args):
    path = args.path
    subvol = Subvolume(path)
    snapshot = subvol.create_snapshot()
    out("Created snapshot", snapshot.name, "in subvolume", path)

def snapshots_delete(args):
    path = args.path
    name = args.name
    subvol = Subvolume(path)
    snapshot = subvol.find_snapshot(name)
    if snapshot is None:
        fail("Could not find snapshot", name, "in subvolume", path)
    snapshot.delete()
    out("Deleted snapshot", name, "from subvolume", path)

def snapshots_init(args):
    path = args.path
    subvol = Subvolume(path)
    subvol.init_snapshots()
    out("Initialised subvolume", path, "for snapshots")

def snapshots_list(args):
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


def out(*messages):
    print(' '.join([str(m) for m in messages]), flush=True)

def err(*messages):
    print(' '.join([str(m) for m in messages]), flush=True, file=sys.stderr)

def fail(*messages):
    err(*messages)
    sys.exit(1)


if __name__ == '__main__':
    main()
