#!/usr/bin/python3

from btrfssnapshotmanager.manager import *

import argparse
import csv
import json


dateformat_human =  '%a %d %b %Y %H:%M:%S'
output_format = 'table'


def main():
    if cmd('whoami') != 'root':
        fatal("Must run as root user")

    parser = argparse.ArgumentParser(prog='btrfs-snapshot-manager')
    parser.add_argument('--log-level', type=int, default=2, dest='loglevel', help='log level: 0=debug, 1=info, 2=warn 3=error 4=fatal')
    parser.add_argument('--csv', action='store_true', default=False, dest='csv', help='output tables in CSV format')
    parser.add_argument('--json', action='store_true', default=False, dest='json', help='output tables in JSON format')
    subparsers = parser.add_subparsers(title='subcommands', metavar='action', help='action to perform')

    # backup
    backup_parser = subparsers.add_parser('backup', help='snapshot backup commands')
    backup_subparsers = backup_parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # backup config
    backup_config_parser = backup_subparsers.add_parser('config', help='show all configured backups')
    backup_config_parser.add_argument('path', nargs='?', help='path to subvolume')
    backup_config_parser.set_defaults(func=backup_config)

    # backup list
    backup_list_parser = backup_subparsers.add_parser('list', help='list snapshots backups')
    backup_list_parser.add_argument('path', nargs='*', help='path to subvolume')
    backup_list_parser.add_argument('--id', nargs='*', type=int, help='only run backups with these ids')
    backup_list_parser.set_defaults(func=backup_list)

    # backup run
    backup_run_parser = backup_subparsers.add_parser('run', help='run backups')
    backup_run_parser.add_argument('path', nargs='*', help='path to subvolume')
    backup_run_parser.add_argument('--id', nargs='*', type=int, help='only run backups with these ids')
    backup_run_parser.set_defaults(func=backup_run)

    # config
    config_parser = subparsers.add_parser('config', help='config commands')
    config_subparsers = config_parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # config check
    config_check_parser = config_subparsers.add_parser('check', help='validate config file')
    config_check_parser.set_defaults(func=config_check)

    # snapshot
    snapshot_parser = subparsers.add_parser('snapshot', help='snapshot management commands')
    snapshot_subparsers = snapshot_parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # snapshot cleanup
    snapshot_cleanup_parser = snapshot_subparsers.add_parser('cleanup', help='delete unrequired snapshots')
    snapshot_cleanup_parser.add_argument('path', nargs='*', help='path to subvolume')
    snapshot_cleanup_parser.set_defaults(func=snapshot_cleanup)

    # snapshot config
    snapshot_config_parser = snapshot_subparsers.add_parser('config', help='list snapshot config')
    snapshot_config_parser.add_argument('path', nargs='?', help='path to subvolume')
    snapshot_config_parser.set_defaults(func=snapshot_config)

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
    snapshot_list_parser.add_argument('path', nargs='?', help='path to subvolume')
    snapshot_list_parser.add_argument('--period', nargs='*', help='only list snapshots for this period')
    snapshot_list_parser.set_defaults(func=snapshot_list)

    # snapshot run
    snapshot_run_parser = snapshot_subparsers.add_parser('run', help='execute scheduled snapshots')
    snapshot_run_parser.add_argument('path', nargs='*', help='path to subvolume')
    snapshot_run_parser.set_defaults(func=snapshot_run)

    # systemdboot
    systemdboot_parser = subparsers.add_parser('systemdboot', help='systemd-boot integration commands')
    systemdboot_subparsers = systemdboot_parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # systemdboot config
    systemdboot_config_parser = systemdboot_subparsers.add_parser('config', help='show configured systemd-boot integration')
    systemdboot_config_parser.set_defaults(func=systemdboot_config)

    # systemdboot create
    systemdboot_create_parser = systemdboot_subparsers.add_parser('create', help='create a systemd-boot entry for a given snapshot')
    systemdboot_create_parser.add_argument('entry', help='name of systemd-boot reference entry to make boot entry for')
    systemdboot_create_parser.add_argument('snapshot', help='name of snapshot to make boot entry for')
    systemdboot_create_parser.set_defaults(func=systemdboot_create)

    # systemdboot delete
    systemdboot_delete_parser = systemdboot_subparsers.add_parser('delete', help='delete a systemd-boot entry')
    systemdboot_delete_parser.add_argument('entry', help='name of boot entry file to delete')
    systemdboot_delete_parser.set_defaults(func=systemdboot_delete)

    # systemdboot list
    systemdboot_list_parser = systemdboot_subparsers.add_parser('list', help='list all systemd-boot snapshot boot entries')
    systemdboot_list_parser.set_defaults(func=systemdboot_list)

    # systemdboot run
    systemdboot_run_parser = systemdboot_subparsers.add_parser('run', help='create and delete systemd-boot entries as required by config')
    systemdboot_run_parser.set_defaults(func=systemdboot_run)

    # systemdboot snapshot
    systemdboot_snapshot_parser = systemdboot_subparsers.add_parser('snapshot', help='systemd-boot boot snapshot commands')
    systemdboot_snapshot_subparsers = systemdboot_snapshot_parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # systemdboot snapshot create
    systemdboot_snapshot_create_parser = systemdboot_snapshot_subparsers.add_parser('create', help='force creating a snapshot of boot init files')
    systemdboot_snapshot_create_parser.set_defaults(func=systemdboot_snapshot_create)

    # systemdboot snapshot create-needed
    systemdboot_snapshot_createneeded_parser = systemdboot_snapshot_subparsers.add_parser('create-needed', help='create a snapshot of boot init files if needed')
    systemdboot_snapshot_createneeded_parser.set_defaults(func=systemdboot_snapshot_createneeded)

    # systemdboot snapshot delete
    systemdboot_snapshot_delete_parser = systemdboot_snapshot_subparsers.add_parser('delete', help='delete snapshot of boot init files')
    systemdboot_snapshot_delete_parser.add_argument('name', help='name of boot snapshot to delete')
    systemdboot_snapshot_delete_parser.set_defaults(func=systemdboot_snapshot_delete)

    # systemdboot snapshot delete-unneeded
    systemdboot_snapshot_deleteunneeded_parser = systemdboot_snapshot_subparsers.add_parser('delete-unneeded', help='delete snapshots no longer needed')
    systemdboot_snapshot_deleteunneeded_parser.set_defaults(func=systemdboot_snapshot_deleteunneeded)

    # systemdboot snapshot list
    systemdboot_snapshot_list_parser = systemdboot_snapshot_subparsers.add_parser('list', help='list snapshots of boot init files')
    systemdboot_snapshot_list_parser.set_defaults(func=systemdboot_snapshot_list)

    args = parser.parse_args()
    if not hasattr(args, 'func'):
        parser.print_help()
    else:
        try:
            args.func(args)
        except SnapshotException as e:
            fatal(e.error)
        except ConfigException as e:
            fatal("Config failed validation: " + e.error)


# Backups

def backup_config(args):
    global_args(args)
    path = args.path
    snapshot_manager = SnapshotManager()

    if path is not None and path not in snapshot_manager.managers:
        fatal("Config not found for subvolume", path)

    header = ['ID', 'LOCATION', 'MECHANISM', *[p.name.upper() for p in PERIODS] + ['MINIMUM']]
    labels = []
    tables = []
    for subvol, manager in snapshot_manager.managers.items():
        if path is None or subvol == path:
            if len(manager.backups) > 0:
                table = []
                for i, backup in enumerate(manager.backups):
                    row = [i]
                    row.append(backup.location())
                    row.append(backup.mechanism)

                    for p in PERIODS:
                        if p in backup.retention:
                            row.append(backup.retention[p])
                        else:
                            row.append('')
                    row.append(backup.retention_minimum)

                    table.append(row)
                labels.append([['SUBVOL', subvol]])
                tables.append(table)

    output_tables(header, labels, tables)

def backup_list(args):
    global_args(args)
    paths = args.path
    ids = args.id

    snapshot_manager = SnapshotManager()

    for path in paths:
        if path not in snapshot_manager.managers:
            fatal("Config not found for subvolume", path)

    if ids is not None and len(ids) > 0 and len(paths) != 1:
        fatal("Can only specify backup IDs to run when running a single backup")

    managers_to_run = snapshot_manager.managers
    if len(paths) > 0:
        managers_to_run = dict([(s, m) for s, m in managers_to_run.items() if s in paths and len(m.backups) > 0])

    tables = []
    labels = []
    header = ['ID', 'LOCATION', 'SNAPSHOT', 'DATE', 'PERIODS']
    for subvol, manager in managers_to_run.items():
        backups = manager.get_backups(ids)
        table = []
        for i, backup in sorted(backups.items(), key=lambda b: b[0]):
            target_snapshot_names = backup.get_target_snapshot_names()
            for target_snapshot_name in sorted(target_snapshot_names):
                snapshot_details = snapshot_name_parse(target_snapshot_name)
                table.append([
                    i,
                    backup.location(),
                    target_snapshot_name,
                    snapshot_details['date'].strftime(dateformat_human),
                    ', '.join([p.name for p in snapshot_details['periods']]),
                ])
        labels.append([['SUBVOL', subvol]])
        tables.append(table)

    output_tables(header, labels, tables)

def backup_run(args):
    global_args(args)
    paths = args.path
    ids = args.id

    snapshot_manager = SnapshotManager()

    for path in paths:
        if path not in snapshot_manager.managers:
            fatal("Config not found for subvolume", path)

    if ids is not None and len(ids) > 0 and len(paths) != 1:
        fatal("Can only specify backup IDs to run when running a single backup")

    snapshot_manager.backup(paths, ids)


# Config

def config_check(args):
    global_args(args)
    snapshot_manager = SnapshotManager()

    info("Config is valid.")


# Snapshots

def snapshot_cleanup(args):
    global_args(args)
    paths = args.path
    snapshot_manager = SnapshotManager()
    if paths is not None:
        for path in paths:
            if path not in snapshot_manager.managers:
                fatal("Config not found for subvolume", path)

    snapshot_manager.cleanup(subvols=paths)

def snapshot_config(args):
    global_args(args)
    path = args.path
    snapshot_manager = SnapshotManager()
    if path is not None and path not in snapshot_manager.managers:
        fatal("Config not found for subvolume", path)

    header = ['PERIOD', 'KEEP', 'LAST RUN', 'NEXT RUN']
    labels = []
    tables = []
    for subvol, manager in snapshot_manager.managers.items():
        if path is None or subvol == path:
            if len(manager.retention_config) > 0:
                table = []
                for period in sorted(manager.retention_config.keys(), key=lambda p: p.seconds):
                    row = []
                    row.append(period.name)

                    row.append(manager.retention_config[period])

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
                labels.append([['SUBVOL', subvol]])
                tables.append(table)

    output_tables(header, labels, tables)

def snapshot_create(args):
    global_args(args)
    path = args.path
    subvol = get_subvol(path)
    snapshot = subvol.create_snapshot()

def snapshot_delete(args):
    global_args(args)
    path = args.path
    name = args.name
    subvol = get_subvol(path)
    snapshot = subvol.find_snapshot(name)
    if snapshot is None:
        fatal("Could not find snapshot", name, "in subvolume", path)
    snapshot.delete()

def snapshot_init(args):
    global_args(args)
    path = args.path
    subvol = get_subvol(path)
    subvol.init_snapshots()

def snapshot_list(args):
    global_args(args)
    path = args.path

    periods = args.period
    if periods is not None:
        for p in periods:
            if p != 'none' and p not in PERIOD_NAME_MAP:
                fatal("No such period:", p)
        periods = [(PERIOD_NAME_MAP[p] if p != 'none' else None) for p in periods]

    snapshot_manager = SnapshotManager()
    if path is None:
        subvols = [m.subvol for m in snapshot_manager.managers.values()]
    else:
        subvols = [get_subvol(path)]

    header = ['SNAPSHOT', 'DATE', 'PERIODS']
    labels = []
    tables = []
    for subvol in subvols:
        table = []

        if not subvol.has_snapshots():
            fatal("Subvolume", subvol.path, "is not initialised for snapshots")

        snapshots = subvol.search_snapshots(periods=periods)
        for snapshot in snapshots:
            table.append([snapshot.name, snapshot.date.strftime(dateformat_human), ', '.join([p.name for p in snapshot.get_periods()])])
        labels.append([['SUBVOL', subvol.name]])
        tables.append(table)

    output_tables(header, labels, tables)

def snapshot_run(args):
    global_args(args)
    paths = args.path
    snapshot_manager = SnapshotManager()
    if paths is not None:
        for path in paths:
            if path not in snapshot_manager.managers:
                fatal("Config not found for subvolume", path)

    snapshot_manager.execute(subvols=paths)


# Systemd-Boot

def systemdboot_config(args):
    global_args(args)
    snapshot_manager = SnapshotManager()
    systemdboot_manager = snapshot_manager.systemdboot_manager
    if systemdboot_manager is None:
        raise SnapshotException("No systemd-boot config enabled.")

    entry_managers = systemdboot_manager.entry_managers
    if entry_managers is not None:
        table = []
        for entry_manager in entry_managers:
            row = []
            row.append(entry_manager.reference_entry)
            row.append(entry_manager.subvol.name)
            for p in PERIODS:
                if p in entry_manager.retention:
                    row.append(entry_manager.retention[p])
                else:
                    row.append('')
            table.append(row)
        header = ['ENTRY', 'SUBVOLUME', *[p.name.upper() for p in PERIODS]]
        tables = [table]
        output_tables(header, [[]], tables)

def systemdboot_create(args):
    global_args(args)
    entry_name = args.entry
    snapshot_name = args.snapshot
    snapshot_manager = SnapshotManager()
    systemdboot_manager = snapshot_manager.systemdboot_manager
    if systemdboot_manager is None:
        raise SnapshotException("No systemd-boot config enabled.")

    entry_managers = snapshot_manager.systemdboot_manager.entry_managers
    if entry_managers is None:
        fatal("No subvolumes configured for systemd-boot integration")

    for entry_manager in entry_managers:
        if entry_manager.reference_entry == entry_name:
            snapshot = entry_manager.subvol.find_snapshot(snapshot_name)
            if snapshot is None:
                fatal("Snapshot {0} not found in subvolume {1}".format(snapshot_name, entry_manager.subvol.name))
            entry_manager.create_entry(snapshot)
            break
    else:
        fatal("Did not find systemd-boot entry {0}".format(entry_name))

def systemdboot_delete(args):
    global_args(args)
    entry_name = args.entry
    snapshot_manager = SnapshotManager()
    systemdboot_manager = snapshot_manager.systemdboot_manager
    if systemdboot_manager is None:
        raise SnapshotException("No systemd-boot config enabled.")

    entry_managers = snapshot_manager.systemdboot_manager.entry_managers
    if entry_managers is None:
        fatal("No subvolumes configured for systemd-boot integration")

    for entry_manager in entry_managers:
        if entry_name in [e.name for e in entry_manager.entries]:
            entry_manager.delete_entry(entry_name)
            break
    else:
        fatal("Systemd-boot entry {0} not found".format(entry_name))

def systemdboot_list(args):
    global_args(args)
    snapshot_manager = SnapshotManager()
    systemdboot_manager = snapshot_manager.systemdboot_manager
    if systemdboot_manager is None:
        raise SnapshotException("No systemd-boot config enabled.")

    entry_managers = snapshot_manager.systemdboot_manager.entry_managers
    if entry_managers is not None:
        header = ['SNAPSHOT ENTRY', 'SNAPSHOT', 'DATE', 'PERIODS', 'BOOT SNAPSHOT']
        labels = []
        tables = []
        for entry_manager in entry_managers:

            table = []

            for entry in entry_manager.entries:
                snapshot = entry.snapshot
                boot_snapshot_name = 'None'
                boot_snapshot = entry.boot_snapshot
                if boot_snapshot is not None:
                    boot_snapshot_name = boot_snapshot.name
                    if not boot_snapshot.exists():
                        boot_snapshot_name += " [NOT FOUND]"
                if snapshot is not None:
                    table.append([
                        entry.name,
                        snapshot.name,
                        snapshot.date.strftime(dateformat_human),
                        ', '.join([p.name for p in snapshot.get_periods()]),
                        boot_snapshot_name,
                    ])
                else:
                    table.append([
                        entry_manager.reference_entry,
                        entry.name,
                        'NOT FOUND',
                        '',
                        '',
                        boot_snapshot_name,
                    ])
            labels.append([
                ['REFERENCE ENTRY', entry_manager.reference_entry],
                ['SUBVOLUME', entry_manager.subvol.name],
            ])
            tables.append(table)

        output_tables(header, labels, tables)

def systemdboot_run(args):
    global_args(args)
    snapshot_manager = SnapshotManager()
    systemdboot_manager = snapshot_manager.systemdboot_manager
    if systemdboot_manager is None:
        raise SnapshotException("No systemd-boot config enabled.")

    entry_managers = snapshot_manager.systemdboot_manager.entry_managers
    if entry_managers is None:
        fatal("No subvolumes configured for systemd-boot integration")

    for entry_manager in entry_managers:
        entry_manager.run()

def systemdboot_snapshot_create(args):
    global_args(args)
    snapshot_manager = SnapshotManager()
    systemdboot_manager = snapshot_manager.systemdboot_manager
    if systemdboot_manager is None:
        raise SnapshotException("No systemd-boot config enabled.")

    boot_snapshot = systemdboot_manager.create_boot_snapshot()

def systemdboot_snapshot_createneeded(args):
    global_args(args)
    snapshot_manager = SnapshotManager()
    systemdboot_manager = snapshot_manager.systemdboot_manager
    if systemdboot_manager is None:
        raise SnapshotException("No systemd-boot config enabled.")

    systemdboot_manager.create_boot_snapshot_if_needed()

def systemdboot_snapshot_delete(args):
    global_args(args)
    name = args.name
    snapshot_manager = SnapshotManager()
    systemdboot_manager = snapshot_manager.systemdboot_manager
    if systemdboot_manager is None:
        raise SnapshotException("No systemd-boot config enabled.")

    systemdboot_manager.delete_boot_snapshot(name)

def systemdboot_snapshot_deleteunneeded(args):
    global_args(args)
    snapshot_manager = SnapshotManager()
    systemdboot_manager = snapshot_manager.systemdboot_manager
    if systemdboot_manager is None:
        raise SnapshotException("No systemd-boot config enabled.")

    systemdboot_manager.remove_unused_boot_snapshots()

def systemdboot_snapshot_list(args):
    global_args(args)
    snapshot_manager = SnapshotManager()
    systemdboot_manager = snapshot_manager.systemdboot_manager
    if systemdboot_manager is None:
        raise SnapshotException("No systemd-boot config enabled.")

    table = []
    for boot_snapshot in systemdboot_manager.boot_snapshots:
        table.append([boot_snapshot.name, str(boot_snapshot.path()), boot_snapshot.date.strftime(dateformat_human)])
    if len(table) > 0:
        tables = [table]
        output_tables(['BOOT SNAPSHOT', 'PATH', 'DATE'], [[]], tables)

# Common

def global_args(args):
    LOG_CONFIG['level'] = args.loglevel
    global output_format
    if args.csv:
        output_format = 'csv'
    elif args.json:
        output_format = 'json'

def get_subvol(path):
    snapshot_manager = SnapshotManager()
    if path in snapshot_manager.managers:
        return snapshot_manager.managers[path].subvol
    return Subvolume(path)

def out(*messages):
    print(' '.join([str(m) for m in messages]), flush=True)

def output_tables(header, labels, tables):
    if output_format == 'csv':
        _output_csv(header, labels, tables)

    elif output_format == 'json':
        _output_json(header, labels, tables)

    else:
        _output_human(header, labels, tables)

def _output_csv(header, labels, tables):
        csvwriter = csv.writer(sys.stdout)

        if len(tables) > 0:
            header = [l[0] for l in labels[0]] + header
            for t, table in enumerate(tables):
                table_values = [l[1] for l in labels[t]]
                for i, row in enumerate(table.copy()):
                    table[i] = table_values + row

        csvwriter.writerow(header)
        for i, table in enumerate(tables):
            csvwriter.writerows(table)

def _output_json(header, labels, tables):
    jsn = {}

    for t, table in enumerate(tables):
        jsn_table = []
        if len(labels[t]) > 1:
            jsn_table = {
                'attributes': dict([(l[0], l[1]) for l in labels[t][1:]]),
                'table': []
            }

        for row in table:
            this_table = dict([(header[i], row[i]) for i in range(0, len(header))])
            if type(jsn_table) == dict:
                jsn_table['table'].append(this_table)
            else:
                jsn_table.append(this_table)

        if len(labels[t]) > 0:
            jsn[labels[t][0][1]] = jsn_table
        elif len(tables) > 1:
            raise Exception("Can't have more than one table if no labels")
        else:
            if type(jsn_table) == dict:
                jsn = jsn_table['table']
            else:
                jsn = jsn_table

    out(json.dumps(jsn, indent=4))

def _output_human(header, labels, tables):
        for i, table in enumerate(tables):
            if i > 0:
                out()
            if len(labels[i]) > 0:
                label_width = max([len(l[0]) for l in labels[i]])
                label_line = "-" * (label_width + 2 + max([len(l[1]) for l in labels[i]]))
                print(label_line)
                for label in labels[i]:
                    print("{}: {}".format(format(label[0], ">{0}".format(label_width)), label[1]))
                print(label_line)
            _output_table(header, table)

def _output_table(header, table):
    if len(table) == 0:
        return
    max_width = []
    for i in range(0, len(header)):
        max_width.append(max([(len(str(r[i])) if r is not None else 0) for r in table] + [len(header[i])]))
    out(' | '.join([
            format(str(c), "<{0}".format(max_width[i])) for i, c in enumerate(header)
        ]))
    for r in table:
        out(' | '.join([
            format(str(c), "<{0}".format(max_width[i])) for i, c in enumerate(r)
        ]))


if __name__ == '__main__':
    main()
