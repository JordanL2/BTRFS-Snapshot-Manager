#!/usr/bin/python3

from btrfssnapshotmanager.manager import *

import argparse


dateformat_human =  '%a %d %b %Y %H:%M:%S'


def main():
    if cmd('whoami') != 'root':
        fatal("Must run as root user")

    parser = argparse.ArgumentParser(prog='btrfs-snapshot-manager')
    parser.add_argument('--log-level', type=int, default=1, dest='loglevel', help='log level: 0=debug, 1=info, 2=warn 3=error 4=fatal')
    subparsers = parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # backup
    backup_parser = subparsers.add_parser('backup', help='snapshot backup commands')
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

    # backup target-list
    backup_targetlist_parser = backup_subparsers.add_parser('target-list', help='list snapshots backed up on target')
    backup_targetlist_parser.add_argument('path', nargs='?', help='path to subvolume')
    backup_targetlist_parser.add_argument('--id', nargs='*', help='only run backups with these ids')
    backup_targetlist_parser.set_defaults(func=backup_targetlist)

    # config
    config_parser = subparsers.add_parser('config', help='config commands')
    config_subparsers = config_parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # config check
    config_check_parser = config_subparsers.add_parser('check', help='validate config file')
    config_check_parser.set_defaults(func=config_check)

    # schedule
    schedule_parser = subparsers.add_parser('schedule', help='snapshot schedule commands')
    schedule_subparsers = schedule_parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # schedule cleanup
    schedule_cleanup_parser = schedule_subparsers.add_parser('cleanup', help='delete unrequired snapshots')
    schedule_cleanup_parser.add_argument('path', nargs='*', help='path to subvolume')
    schedule_cleanup_parser.set_defaults(func=schedule_cleanup)

    # schedule list
    schedule_list_parser = schedule_subparsers.add_parser('list', help='list snapshot schedules')
    schedule_list_parser.add_argument('path', nargs='?', help='path to subvolume')
    schedule_list_parser.set_defaults(func=schedule_list)

    # schedule run
    schedule_run_parser = schedule_subparsers.add_parser('run', help='execute scheduled snapshots')
    schedule_run_parser.add_argument('path', nargs='*', help='path to subvolume')
    schedule_run_parser.set_defaults(func=schedule_run)

    # snapshot
    snapshot_parser = subparsers.add_parser('snapshot', help='snapshot management commands')
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
    snapshot_list_parser.add_argument('path', nargs='?', help='path to subvolume')
    snapshot_list_parser.add_argument('--period', nargs='*', help='only list snapshots for this period')
    snapshot_list_parser.set_defaults(func=snapshot_list)

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
    systemdboot_snapshot_parser = systemdboot_subparsers.add_parser('snapshot', help='systemd-boot integration commands')
    systemdboot_snapshot_subparsers = systemdboot_snapshot_parser.add_subparsers(title='subcommands', help='action to perform', metavar='action', required=True)

    # systemdboot snapshot create
    systemdboot_snapshot_create_parser = systemdboot_snapshot_subparsers.add_parser('create', help='force creating a snapshot of boot init files')
    systemdboot_snapshot_create_parser.set_defaults(func=systemdboot_snapshot_create)

    # systemdboot snapshot create-needed
    systemdboot_snapshot_createneeded_parser = systemdboot_snapshot_subparsers.add_parser('create-needed', help='create a snapshot of boot init files if needed')
    systemdboot_snapshot_createneeded_parser.set_defaults(func=systemdboot_snapshot_createneeded)

    # systemdboot snapshots delete
    systemdboot_snapshot_delete_parser = systemdboot_snapshot_subparsers.add_parser('delete', help='delete snapshot of boot init files')
    systemdboot_snapshot_delete_parser.add_argument('name', help='name of boot snapshot to delete')
    systemdboot_snapshot_delete_parser.set_defaults(func=systemdboot_snapshot_delete)

    # systemdboot snapshots delete-unneeded
    systemdboot_snapshot_deleteunneeded_parser = systemdboot_snapshot_subparsers.add_parser('delete-unneeded', help='delete snapshots no longer needed')
    systemdboot_snapshot_deleteunneeded_parser.set_defaults(func=systemdboot_snapshot_deleteunneeded)

    # systemdboot snapshots list
    systemdboot_snapshot_list_parser = systemdboot_snapshot_subparsers.add_parser('list', help='list snapshots of boot init files')
    systemdboot_snapshot_list_parser.set_defaults(func=systemdboot_snapshot_list)

    args = parser.parse_args()
    try:
        args.func(args)
    except SnapshotException as e:
        fatal(e.error)
    except ConfigException as e:
        fatal("Config failed validation: " + e.error)


# Backups

def backup_list(args):
    global_args(args)
    path = args.path
    snapshot_manager = SnapshotManager()

    if path is not None and path not in snapshot_manager.managers:
        fatal("Config not found for subvolume", path)

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
    global_args(args)
    path = args.path
    ids = args.id
    if ids is not None:
        ids = [int(i) for i in ids]
    snapshot_manager = SnapshotManager()

    if path is not None and path not in snapshot_manager.managers:
        fatal("Config not found for subvolume", path)

    empty_line = False
    for subvol, manager in snapshot_manager.managers.items():
        if path is None or subvol == path:
            if len(manager.backups) > 0:
                if empty_line:
                    info()
                manager.backup(ids=ids)
                empty_line = True

def backup_targetlist(args):
    global_args(args)
    path = args.path
    ids = args.id
    if ids is not None:
        ids = [int(i) for i in ids]
    snapshot_manager = SnapshotManager()

    if path is not None and path not in snapshot_manager.managers:
        fatal("Config not found for subvolume", path)

    table = []
    for subvol, manager in snapshot_manager.managers.items():
        if path is None or subvol == path:
            if len(manager.backups) > 0:
                if len(table) > 0:
                    table.append(None)
                table.append([subvol, 'LOCATION', 'SNAPSHOT', 'DATE', 'PERIODS'])
                for i, backup in enumerate(manager.backups):
                    if ids is None or len(ids) == 0 or i in ids:
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

    output_table(table)


# Config

def config_check(args):
    global_args(args)
    snapshot_manager = SnapshotManager()

    info("Config is valid.")


# Schedule

def schedule_cleanup(args):
    global_args(args)
    paths = args.path
    snapshot_manager = SnapshotManager()
    if paths is not None:
        for path in paths:
            if path not in snapshot_manager.managers:
                fatal("Config not found for subvolume", path)

    snapshot_manager.cleanup(subvols=paths)

def schedule_list(args):
    global_args(args)
    path = args.path
    snapshot_manager = SnapshotManager()
    if path is not None and path not in snapshot_manager.managers:
        fatal("Config not found for subvolume", path)

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

def schedule_run(args):
    global_args(args)
    paths = args.path
    snapshot_manager = SnapshotManager()
    if paths is not None:
        for path in paths:
            if path not in snapshot_manager.managers:
                fatal("Config not found for subvolume", path)

    snapshot_manager.execute(subvols=paths)


# Snapshots

def snapshot_create(args):
    global_args(args)
    path = args.path
    subvol = get_subvol(path)
    snapshot = subvol.create_snapshot()
    info("Created snapshot", snapshot.name, "in subvolume", path)

def snapshot_delete(args):
    global_args(args)
    path = args.path
    name = args.name
    subvol = get_subvol(path)
    snapshot = subvol.find_snapshot(name)
    if snapshot is None:
        fatal("Could not find snapshot", name, "in subvolume", path)
    snapshot.delete()
    info("Deleted snapshot", name, "from subvolume", path)

def snapshot_init(args):
    global_args(args)
    path = args.path
    subvol = get_subvol(path)
    subvol.init_snapshots()
    info("Initialised subvolume", path, "for snapshots")

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

    table = []
    for subvol in subvols:
        if len(table) > 0:
            table.append(None)
        table.append([subvol.name, 'DATE', 'PERIODS'])

        if not subvol.has_snapshots():
            fatal("Subvolume", subvol.path, "is not initialised for snapshots")

        snapshots = subvol.search_snapshots(periods=periods)
        for snapshot in snapshots:
            table.append([snapshot.name, snapshot.date.strftime(dateformat_human), ', '.join([p.name for p in snapshot.get_periods()])])

    output_table(table)


# Systemd-Boot

def systemdboot_config(args):
    global_args(args)
    snapshot_manager = SnapshotManager()
    systemdboot_entry_managers = snapshot_manager.systemdboot_manager.entry_managers
    if systemdboot_entry_managers is not None:
        table = [['SUBVOLUME', 'BOOT PATH', 'ENTRY', *[p.name.upper() for p in PERIODS]]]
        for systemdboot_entry_manager in systemdboot_entry_managers:
            row = []
            row.append(systemdboot_entry_manager.subvol.name)
            row.append(systemdboot_entry_manager.boot_path)
            row.append(systemdboot_entry_manager.reference_entry)
            for p in PERIODS:
                if p in systemdboot_entry_manager.retention:
                    row.append(systemdboot_entry_manager.retention[p])
                else:
                    row.append('')
            table.append(row)
        output_table(table)

def systemdboot_create(args):
    global_args(args)
    entry_name = args.entry
    snapshot_name = args.snapshot
    snapshot_manager = SnapshotManager()
    systemdboot_entry_managers = snapshot_manager.systemdboot_manager.entry_managers
    if systemdboot_entry_managers is None:
        fatal("No subvolumes configured for systemd-boot integration")

    for systemdboot_entry_manager in systemdboot_entry_managers:
        if systemdboot_entry_manager.reference_entry == entry_name:
            snapshot = systemdboot_entry_manager.subvol.find_snapshot(snapshot_name)
            if snapshot is None:
                fatal("Snapshot {0} not found in subvolume {1}".format(snapshot_name, systemdboot_entry_manager.subvol.name))
            systemdboot_entry_manager.create_entry(snapshot)
            break
    else:
        fatal("Did not find systemd-boot entry {0}".format(entry_name))

def systemdboot_delete(args):
    global_args(args)
    entry_name = args.entry
    snapshot_manager = SnapshotManager()
    systemdboot_entry_managers = snapshot_manager.systemdboot_manager.entry_managers
    if systemdboot_entry_managers is None:
        fatal("No subvolumes configured for systemd-boot integration")

    for systemdboot_entry_manager in systemdboot_entry_managers:
        if entry_name in systemdboot_entry_manager.entries:
            systemdboot_entry_manager.delete_entry(entry_name)
            break
    else:
        fatal("Systemd-boot entry {0} not found".format(entry_name))
    info("Deleted systemd-boot entry {0}".format(entry_name))

def systemdboot_list(args):
    global_args(args)
    snapshot_manager = SnapshotManager()
    systemdboot_entry_managers = snapshot_manager.systemdboot_manager.entry_managers
    if systemdboot_entry_managers is not None:
        table = []
        for systemdboot_entry_manager in systemdboot_entry_managers:

            if len(table) > 0:
                table.append(None)
            table.append([systemdboot_entry_manager.reference_entry, 'SUBVOLUME', 'SNAPSHOT', 'DATE', 'PERIODS', 'BOOT SNAPSHOT'])

            for entry in systemdboot_entry_manager.entries:
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
                        systemdboot_entry_manager.subvol.name,
                        snapshot.name,
                        snapshot.date.strftime(dateformat_human),
                        ', '.join([p.name for p in snapshot.get_periods()]),
                        boot_snapshot_name,
                    ])
                else:
                    table.append([
                        systemdboot_entry_manager.reference_entry,
                        entry.name,
                        systemdboot_entry_manager.subvol.name,
                        'NOT FOUND',
                        '',
                        '',
                        boot_snapshot_name,
                    ])

        output_table(table)

def systemdboot_run(args):
    global_args(args)
    snapshot_manager = SnapshotManager()
    systemdboot_entry_managers = snapshot_manager.systemdboot_manager.entry_managers
    if systemdboot_entry_managers is None:
        fatal("No subvolumes configured for systemd-boot integration")

    info("Creating missing systemd-boot entries, and deleting ones no longer required")
    for systemdboot_entry_manager in systemdboot_entry_managers:
        systemdboot_entry_manager.run()

def systemdboot_snapshot_create(args):
    global_args(args)
    snapshot_manager = SnapshotManager()
    systemdboot_manager = snapshot_manager.systemdboot_manager
    boot_snapshot = systemdboot_manager.create_boot_snapshot()
    info("Created new boot snapshot: {0}".format(boot_snapshot.name))

def systemdboot_snapshot_createneeded(args):
    global_args(args)
    snapshot_manager = SnapshotManager()
    systemdboot_manager = snapshot_manager.systemdboot_manager
    systemdboot_manager.create_boot_snapshot_if_needed()

def systemdboot_snapshot_delete(args):
    global_args(args)
    name = args.name
    snapshot_manager = SnapshotManager()
    systemdboot_manager = snapshot_manager.systemdboot_manager
    systemdboot_manager.delete_boot_snapshot(name)
    info("Deleted boot snapshot {0}".format(name))

def systemdboot_snapshot_deleteunneeded(args):
    global_args(args)
    snapshot_manager = SnapshotManager()
    systemdboot_manager = snapshot_manager.systemdboot_manager
    systemdboot_manager.remove_unused_boot_snapshots()

def systemdboot_snapshot_list(args):
    global_args(args)
    snapshot_manager = SnapshotManager()
    systemdboot_manager = snapshot_manager.systemdboot_manager
    table = [[systemdboot_manager.boot_path, 'PATH', 'DATE']]
    for boot_snapshot in systemdboot_manager.boot_snapshots:
        table.append([boot_snapshot.name, boot_snapshot.path(), boot_snapshot.date.strftime(dateformat_human)])
    if len(table) > 1:
        output_table(table)

# Common

def global_args(args):
    LOG_CONFIG['level'] = args.loglevel

def get_subvol(path):
    snapshot_manager = SnapshotManager()
    if path in snapshot_manager.managers:
        return snapshot_manager.managers[path].subvol
    return Subvolume(path)

def out(*messages):
    print(' '.join([str(m) for m in messages]), flush=True)

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
