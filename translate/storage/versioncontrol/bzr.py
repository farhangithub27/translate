# -*- coding: utf-8 -*-
#
# Copyright 2004-2008,2012 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.


from translate.storage.versioncontrol import (GenericRevisionControlSystem,
                                              prepare_filelist, run_command,
                                              youngest_ancestor)


def is_available():
    """check if bzr is installed"""
    exitcode, output, error = run_command(["bzr", "version"])
    return exitcode == 0


_version = None


def get_version():
    """return a tuple of (major, minor) for the installed bazaar client"""
    global _version
    if _version:
        return _version

    import re
    command = ["bzr", "--version"]
    exitcode, output, error = run_command(command)
    if exitcode == 0:
        version_line = output.splitlines()[0]
        version_match = re.search(r"\d+\.\d+", version_line)
        if version_match:
            major, minor = version_match.group().split(".")
            if (major.isdigit() and minor.isdigit()):
                _version = (int(major), int(minor))
                return _version
    # if anything broke before, then we return the invalid version number
    return (0, 0)


class bzr(GenericRevisionControlSystem):
    """Class to manage items under revision control of bzr."""

    RCS_METADIR = ".bzr"
    SCAN_PARENTS = True

    def update(self, revision=None, needs_revert=True):
        """Does a clean update of the given path"""
        output_revert = ""
        if needs_revert:
            # bzr revert
            command = ["bzr", "revert", self.location_abs]
            exitcode, output_revert, error = run_command(command)
            if exitcode != 0:
                raise IOError("[BZR] revert of '%s' failed: %s" % (
                              self.location_abs, error))

        # bzr pull
        command = ["bzr", "pull"]
        exitcode, output_pull, error = run_command(command)
        if exitcode != 0:
            raise IOError("[BZR] pull of '%s' failed: %s" % (
                          self.location_abs, error))
        return output_revert + output_pull

    def add(self, files, message=None, author=None):
        """Add and commit files."""
        files = prepare_filelist(files)
        command = ["bzr", "add"] + files
        exitcode, output, error = run_command(command)
        if exitcode != 0:
            raise IOError("[BZR] add in '%s' failed: %s" % (
                          self.location_abs, error))

        # go down as deep as possible in the tree to avoid accidental commits
        # TODO: explicitly commit files by name
        ancestor = youngest_ancestor(files)
        return output + type(self)(ancestor).commit(message, author)

    def commit(self, message=None, author=None):
        """Commits the file and supplies the given commit message if present"""
        # bzr commit
        command = ["bzr", "commit"]
        if message:
            command.extend(["-m", message])
        # the "--author" argument is supported since bzr v0.91rc1
        if author and (get_version() >= (0, 91)):
            command.extend(["--author", author])
        # the filename is the last argument
        command.append(self.location_abs)
        exitcode, output_commit, error = run_command(command)
        if exitcode != 0:
            raise IOError("[BZR] commit of '%s' failed: %s" % (
                          self.location_abs, error))
        # bzr push
        command = ["bzr", "push"]
        exitcode, output_push, error = run_command(command)
        if exitcode != 0:
            raise IOError("[BZR] push of '%s' failed: %s" % (
                          self.location_abs, error))
        return output_commit + output_push

    def getcleanfile(self, revision=None):
        """Get a clean version of a file from the bzr repository"""
        # bzr cat
        command = ["bzr", "cat", self.location_abs]
        exitcode, output, error = run_command(command)
        if exitcode != 0:
            raise IOError("[BZR] cat failed for '%s': %s" % (
                          self.location_abs, error))
        return output
