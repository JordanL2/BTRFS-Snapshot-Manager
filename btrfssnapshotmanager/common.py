#!/usr/bin/python3

import subprocess


class CommandException(Exception):

    def __init__(self, command, code, error):
        self.command = command
        self.code = code
        self.error = error
        super().__init__(self, "Command `{}` returned code {} - {}".format(command, code, error))


class SnapshotException(Exception):

    def __init__(self, error):
        self.error = error
        super().__init__(self, error)


def cmd(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = result.stdout.decode('utf-8').rstrip("\n")
    stderr = result.stderr.decode('utf-8').rstrip("\n")
    if result.returncode != 0:
        raise CommandException(command, result.returncode, stderr)
    return stdout

def info(*messages):
    print(' '.join([str(m) for m in messages]), flush=True)
