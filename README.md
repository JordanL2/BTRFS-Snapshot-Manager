# BTRFS-Snapshot-Manager

## TODO

* Minimum allowed time between snapshot - we don't want to run if the last run was literally a minute ago - configurable

* Snapshot systemdboot /boot dir

```
when taking snapshot:
	if systemd boot enabled for the given subvol:
		ensure /boot/snapshots exists
		if a snapshot dir exists:
			get the most recent one
			use diff to compare all top level files in /boot with contents of snapshot
		if either there are no snapshots, or a difference was found with the last snapshot:
			make new snapshot dir with current date/time name
			copy all top level files in /boot into it

when deleting snapshot:
	if systemd boot enabled for the given subvol:
		check each dir in /boot/snapshots:
			if no snapshots are using it:
				delete the dir

when making snapshot boot entry:
	get most recent dir in /boot/snapshots with date <= date of snapshot
	use this for paths to linux kernel / initrd images
```
