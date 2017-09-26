# -*- coding: utf-8;
# mode: python; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4
# -*- vim:fenc=utf-8:ft=python:et:sw=4:ts=4:sts=4

# Copyright (c) 2008-2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2014 Manuel Vázquez Acosta <mva.led@gmail.com>
# Copyright (c) 2015-2016 Claudiu Popa <pcmanticore@gmail.com>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

"""Emacs and Flymake compatible Pylint.

This script is for integration with emacs and is compatible with flymake mode.

epylint walks out of python packages before invoking pylint. This avoids
reporting import errors that occur when a module within a package uses the
absolute import path to get another module within this package.

For example:
    - Suppose a package is structured as

        a/__init__.py
        a/b/x.py
        a/c/y.py

   - Then if y.py imports x as "from a.b import x" the following produces pylint
     errors

       cd a/c; pylint y.py

   - The following obviously doesn't

       pylint a/c/y.py

   - As this script will be invoked by emacs within the directory of the file
     we are checking we need to go out of it to avoid these false positives.


You may also use py_run to run pylint with desired options and get back (or not)
its output.
"""
from __future__ import print_function

import os
import os.path as osp
import sys
import shlex
from subprocess import Popen, PIPE

import six


def _get_env():
    '''Extracts the environment PYTHONPATH and appends the current sys.path to
    those.'''
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join(sys.path)
    return env

def lint(filename, options=None):
    """Pylint the given file.

    When run from emacs we will be in the directory of a file, and passed its
    filename.  If this file is part of a package and is trying to import other
    modules from within its own package or another package rooted in a directory
    below it, pylint will classify it as a failed import.

    To get around this, we traverse down the directory tree to find the root of
    the package this module is in.  We then invoke pylint from this directory.

    Finally, we must correct the filenames in the output generated by pylint so
    Emacs doesn't become confused (it will expect just the original filename,
    while pylint may extend it with extra directories if we've traversed down
    the tree)
    """
    # traverse downwards until we are out of a python package
    full_path = osp.abspath(filename)
    parent_path = osp.dirname(full_path)
    child_path = osp.basename(full_path)

    while parent_path != "/" and osp.exists(osp.join(parent_path, '__init__.py')):
        child_path = osp.join(osp.basename(parent_path), child_path)
        parent_path = osp.dirname(parent_path)

    # Start pylint
    # Ensure we use the python and pylint associated with the running epylint
    run_cmd = "import sys; from pylint.lint import Run; Run(sys.argv[1:])"
    options = options or ['--disable=C,R,I']
    cmd = [sys.executable, "-c", run_cmd] + [
        '--msg-template', '{path}:{line}: {category} ({msg_id}, {symbol}, {obj}) {msg}',
        '-r', 'n', child_path] + options
    process = Popen(cmd, stdout=PIPE, cwd=parent_path, env=_get_env(),
                    universal_newlines=True)

    for line in process.stdout:
        # remove pylintrc warning
        if line.startswith("No config file found"):
            continue

        # modify the file name thats output to reverse the path traversal we made
        parts = line.split(":")
        if parts and parts[0] == child_path:
            line = ":".join([filename] + parts[1:])
        print(line, end=' ')

    process.wait()
    return process.returncode


def py_run(command_options='', return_std=False, stdout=None, stderr=None):
    """Run pylint from python

    ``command_options`` is a string containing ``pylint`` command line options;
    ``return_std`` (boolean) indicates return of created standard output
    and error (see below);
    ``stdout`` and ``stderr`` are 'file-like' objects in which standard output
    could be written.

    Calling agent is responsible for stdout/err management (creation, close).
    Default standard output and error are those from sys,
    or standalone ones (``subprocess.PIPE``) are used
    if they are not set and ``return_std``.

    If ``return_std`` is set to ``True``, this function returns a 2-uple
    containing standard output and error related to created process,
    as follows: ``(stdout, stderr)``.

    A trivial usage could be as follows:
        >>> py_run( '--version')
        No config file found, using default configuration
        pylint 0.18.1,
            ...

    To silently run Pylint on a module, and get its standard output and error:
        >>> (pylint_stdout, pylint_stderr) = py_run( 'module_name.py', True)
    """
    # Create command line to call pylint
    epylint_part = [sys.executable, "-c", "from pylint import epylint;epylint.Run()"]
    options = shlex.split(command_options)
    cli = epylint_part + options

    # Providing standard output and/or error if not set
    if stdout is None:
        if return_std:
            stdout = PIPE
        else:
            stdout = sys.stdout
    if stderr is None:
        if return_std:
            stderr = PIPE
        else:
            stderr = sys.stderr
    # Call pylint in a subprocess
    process = Popen(cli, shell=False, stdout=stdout, stderr=stderr,
                    env=_get_env(), universal_newlines=True)
    proc_stdout, proc_stderr = process.communicate()
    # Return standard output and error
    if return_std:
        return six.moves.StringIO(proc_stdout), six.moves.StringIO(proc_stderr)
    return None


def Run():
    if len(sys.argv) == 1:
        print("Usage: %s <filename> [options]" % sys.argv[0])
        sys.exit(1)
    elif not osp.exists(sys.argv[1]):
        print("%s does not exist" % sys.argv[1])
        sys.exit(1)
    else:
        sys.exit(lint(sys.argv[1], sys.argv[2:]))


if __name__ == '__main__':
    Run()
