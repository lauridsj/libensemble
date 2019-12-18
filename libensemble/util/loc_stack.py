"""
libensemble utility class -- keeps a stack of directory locations.
"""

import os
import shutil
from glob import glob


class LocationStack:
    """Keep a stack of directory locations.
    """

    def __init__(self):
        """Initialize the location dictionary and directory stack."""
        self.dirs = {}
        self.stack = []

    def perform_op(self, link, file_path, relative_path_from_dest, dest_path):
        """ Perform copying or symlinking """
        if link:
            os.symlink(relative_path_from_dest, dest_path)
        else:
            if os.path.isdir(file_path):
                shutil.copytree(file_path, dest_path)
            else:
                shutil.copy(file_path, dest_path)

    def copy_or_symlink(self, srcdir, destdir, input_files, link):
        """ Inspired by https://stackoverflow.com/a/9793699.
        Determine filepaths, basenames, and components needed for copying
        """
        if not os.path.isdir(destdir):
            os.makedirs(destdir)
        for file_path in glob('{}/*'.format(srcdir)):

            src_base = os.path.basename(file_path)
            relative_path_from_dest = os.path.relpath(file_path, destdir)
            dest_path = os.path.join(destdir, src_base)

            if len(input_files) > 0:
                if src_base in input_files:
                    self.perform_op(link, file_path, relative_path_from_dest, dest_path)
            else:
                self.perform_op(link, file_path, relative_path_from_dest, dest_path)

    def register_loc(self, key, dirname, prefix=None, srcdir=None, input_files=[], link=False):
        """Register a new location in the dictionary.

        Parameters
        ----------

        key:
            The key used to identify the new location.

        dirname: string:
            Directory name

        prefix: string:
            Prefix to be used with the dirname.  If prefix is not None,
            only the base part of the dirname is used.

        srcdir: string:
            Name of a source directory to populate the new location.
            If srcdir is not None, the directory should not yet exist.
            srcdir is not relative to prefix.

        link: boolean:
            Create symlinks instead of copying files to new location.

        input_files: list:
            Currently only used with link option. Copy/symlink
            exactly these files
        """
        if prefix is not None:
            prefix = os.path.expanduser(prefix)
            dirname = os.path.join(prefix, os.path.basename(dirname))

        self.dirs[key] = dirname
        if srcdir is not None:
            assert ~os.path.isdir(dirname), \
                "Directory {} already exists".format(dirname)
            self.copy_or_symlink(srcdir, dirname, input_files, link)
        else:
            if dirname:
                os.mkdir(dirname)
        return dirname

    def push_loc(self, key):
        """Push a location from the dictionary."""
        self.push(self.dirs.get(key))

    def clean_locs(self):
        """Remove all directories listed in the dictionary."""
        for dirname in self.dirs.values():
            if dirname is not None and os.path.isdir(dirname):
                shutil.rmtree(dirname)

    def push(self, dirname):
        """Push the current location and change directories (if not None)."""
        if dirname is not None:
            self.stack.append(os.getcwd())
            os.chdir(dirname)
        else:
            self.stack.append(None)

    def pop(self):
        """Pop the current directory and change back."""
        dirname = self.stack.pop()
        if dirname is not None:
            os.chdir(dirname)

    class Saved:
        """Context object for use with a with statement"""
        def __init__(self, ls, dirname):
            self.ls = ls
            self.dirname = dirname

        def __enter__(self):
            self.ls.push(self.dirname)
            return self.ls

        def __exit__(self, etype, value, traceback):
            self.ls.pop()

    def loc(self, key):
        """Return a with context for pushing a location key"""
        return LocationStack.Saved(self, self.dirs.get(key))

    def dir(self, dirname):
        """Return a with context for pushing a directory"""
        return LocationStack.Saved(self, dirname)
