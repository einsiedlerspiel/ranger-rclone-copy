from ranger.api.commands import Command
from ranger.core.loader import CommandLoader
from ranger.core.shared import FileManagerAware
from os.path import isfile
import csv

class rclone_targets(FileManagerAware):
    """Stores rclone_targets, writes them into a file in the ranger config
    directory, is initialized at startup below."""
    def __init__(self):
        self.targets_file = self.fm.confpath("rclone_targets")
        self.targets = list()

        if isfile(self.targets_file):
            with open(self.targets_file, "r", newline='') as csvfile:
                targets_reader = csv.reader(csvfile, delimiter=',')
                for row in targets_reader:
                    self.targets.append(row)


    def list_targets(self):
        """returns list of key target pairs"""
        return self.targets


    def list_keys(self):
        """returns list of only the keys of all targets"""
        keylist = list()
        for x in self.targets:
            keylist.append(x[0])
        return keylist


    def add(self, key, target):
        """adds key target pair to rclone_targets"""
        self.targets.append([key, target])


    def get(self, key):
        """returns target to a given key"""
        for row in self.targets:
            if key in row[0]:
                return(row[1])
        return key


    def remove(self, key):
        """removes key target pair for a given key from rclone_targets"""
        for row in self.targets:
            if row[0] == key:
                self.targets.remove(row)
                return True
        return False


    def update_file(self):
        """writes rclone_targets into file"""
        with open(self.targets_file,'w', newline='') as csvfile:
            targets_writer = csv.writer(csvfile, delimiter=',')
            targets_writer.writerows(self.targets)


# instantiate rclone_target
rclone_target = rclone_targets()

class remove_rclone_target(Command):

    def execute(self):
        key = self.arg(1)

        if rclone_target.remove(key):
            rclone_target.update_file()
            self.fm.notify('Rclone target removed')
        else:
            self.fm.notify('Rclone target does not exist', bad=True)


class add_rclone_target(Command):

    def execute(self):
        key = self.arg(1)
        target = self.arg(2)

        if key == target:
            self.fm.notify('Keyword and Target are identical', bad=True)
            return
        elif rclone_target.get(key) != key:
            self.fm.notify('Keyword already exists', bad=True)
            return
        else:
            rclone_target.add(key, target)
            rclone_target.update_file()
            self.fm.notify('Rclone target added')


class change_rclone_target(Command):

    def execute(self):
        key = self.arg(1)
        target = self.arg(2)

        if key == target:
            self.fm.notify('Keyword and Target are identical', bad=True)
            return
        else:
            rclone_target.remove(key)
            rclone_target.add(key, target)

            rclone_target.update_file()
            self.fm.notify('Rclone target changed')


class rclone_copy(Command):

    def execute(self):
        if not self.arg(1):
            self.fm.notify('Missing target argument', bad=True)
            return
        else:
            # we don't need to check id self.arg(1) is a valid key because if
            # it's not rclone_target.get() just returns it. So we can pass it
            # along to rclone.
            target = rclone_target.get(self.arg(1))

            if not self.fm.thisdir.get_selection():
                self.fm.notify('No files to copy', bad=True)
            else:
                for file in self.fm.thisdir.get_selection():
                    descr = "copying " + file.path + " to " + target
                    obj = CommandLoader(args=["rclone", "copy",
                                              "--no-traverse", file.path,
                                              target], descr=descr)
                    self.fm.loader.add(obj)


    def tab(self, tabnum):
        return ["rclone_copy " + target for target in rclone_target.list_keys()]
