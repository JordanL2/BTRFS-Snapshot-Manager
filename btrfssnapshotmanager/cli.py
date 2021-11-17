#!/usr/bin/python3

from btrfssnapshotmanager.snapshots import *

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(prog='btrfs-snapshot-manager')
    subparsers = parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # snapshots
    snapshots_parser = subparsers.add_parser('snapshots', help='snapshot-related commands')
    snapshots_subparsers = snapshots_parser.add_subparsers(required=True)

    # snapshots create
    snapshots_create_parser = snapshots_subparsers.add_parser('create', help='create snapshot')
    snapshots_create_parser.add_argument('path', help='path to subvolume')
    snapshots_create_parser.set_defaults(func=snapshots_create)

    # snapshots delete
    snapshots_delete_parser = snapshots_subparsers.add_parser('delete', help='delete snapshot')
    snapshots_delete_parser.add_argument('path', help='path to subvolume')
    snapshots_delete_parser.add_argument('name', help='snapshot name to delete')
    snapshots_delete_parser.set_defaults(func=snapshots_delete)

    # snapshots list
    snapshots_list_parser = snapshots_subparsers.add_parser('list', help='list snapshots')
    snapshots_list_parser.add_argument('path', help='path to subvolume')
    snapshots_list_parser.set_defaults(func=snapshots_list)

    args = parser.parse_args()
    args.func(args)


def snapshots_create(args):
    path = args.path
    subvol = Subvolume(path)
    snapshot = subvol.create_snapshot()
    out("Created snapshot", snapshot.name, "in subvolume", path)

def snapshots_delete(args):
    path = args.path
    name = args.name
    print("deleting snapshot", name, "in", path)

def snapshots_list(args):
    path = args.path
    subvol = Subvolume(path)
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
