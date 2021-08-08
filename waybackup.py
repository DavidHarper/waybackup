#!/usr/bin/env python3

import sys, os, stat, hashlib
import argparse
from datetime import datetime
from enum import Enum

class WayBackupEvent(Enum):
    STARTED_BACKUP = 1
    ENTERED_DIRECTORY = 2
    SKIPPED_DIRECTORY = 3
    COPIED_FILE = 4
    COPIED_SYMLINK = 5
    COPIED_ATTRIBUTES = 6
    CREATED_LINK = 7
    EXITED_DIRECTORY = 8
    FINISHED_BACKUP = 9
    FOUND_IGNORE_FILE = 10
    ADDED_IGNORED_DIRECTORY = 11
    ABORTED_BACKUP = 12
    SKIPPED_FILE = 13

class WayBackup:
    IGNORE_FILE_NAME='.waybackup.ignore'

    def __init__(self, dryrun=False, verbose=False, callback=None):
        self.dryrun=dryrun
        self.verbose=verbose
        self.callback=callback

    def backup(self, srcdir, refdir, tgtdir):
        self.directories_processed=0
        self.directories_skipped=0
        self.files_skipped=0
        self.files_copied=0
        self.bytes_copied=0
        self.file_attributes_copied=0
        self.symlinks_copied=0
        self.links_created=0
        self.last_directory_entered=None
        self.errno=0
        self.strerror=None

        start_time=datetime.now()

        if self.callback is not None:
            self.callback(WayBackupEvent.STARTED_BACKUP,
                {
                    'start_time' : start_time,
                    'dryrun' : self.dryrun,
                    'verbose' : self.verbose,
                    'srcdir' : srcdir,
                    'refdir' : refdir,
                    'tgtdir' : tgtdir
                }
            )

        try:
            self.process_directory(srcdir, refdir, tgtdir)
        except OSError as error:
            self.errno=error.errno
            self.strerror=error.strerror

        finish_time=datetime.now()

        if self.callback is not None:
            results = {
                'start_time' : start_time,
                'finish_time' : finish_time,
                'dryrun' : self.dryrun,
                'verbose' : self.verbose,
                'srcdir' : srcdir,
                'refdir' : refdir,
                'tgtdir' : tgtdir,
                'elapsed_time' : finish_time-start_time,
                'directories_processed' : self.directories_processed ,
                'directories_skipped' : self.directories_skipped,
                'files_skipped' : self.files_skipped,
                'files_copied' : self.files_copied,
                'bytes_copied' : self.bytes_copied,
                'file_attributes_copied' : self.file_attributes_copied,
                'symlinks_copied' : self.symlinks_copied,
                'links_created' : self.links_created,
                'status' : 0
            }

            if self.errno!=0:
                results['status']=self.errno
                results['errno']=self.errno
                results['strerror']=self.strerror
                results['last_directory_entered']=self.last_directory_entered

            self.callback(WayBackupEvent.FINISHED_BACKUP, results)

        return self.errno

    def process_directory(self, srcdir, refdir, tgtdir, ignore=None):
        ignore=self.update_ignore_list(ignore, srcdir)

        if (ignore is not None) and (srcdir in ignore):
            self.directories_skipped=self.directories_skipped+1

            if self.verbose and self.callback is not None:
                self.callback(WayBackupEvent.SKIPPED_DIRECTORY, {'name' : srcdir})

            return None

        self.last_directory_entered=srcdir

        if self.verbose and self.callback is not None:
            self.callback(WayBackupEvent.ENTERED_DIRECTORY, {'name' : srcdir})

        if not self.dryrun:
            os.makedirs(tgtdir)

        for file in os.listdir(srcdir):
            srcpath = os.path.join(srcdir, file)
            refpath = os.path.join(refdir, file)
            tgtpath = os.path.join(tgtdir, file)

            if os.path.islink(srcpath) or os.path.isfile(srcpath):
                self.process_file(srcpath, refpath, tgtpath, ignore)
            elif os.path.isdir(srcpath):
                self.process_directory(srcpath, refpath, tgtpath, ignore)
            else:
                self.process_other_entity(srcpath, refpath, tgtpath)

        self.copy_file_attributes(srcdir, tgtdir)

        self.directories_processed = self.directories_processed + 1

        if self.verbose and self.callback is not None:
            self.callback(WayBackupEvent.EXITED_DIRECTORY, {'name' : srcdir})

    def update_ignore_list(self, ignore, srcdir):
        ignorefile=os.path.join(srcdir, self.IGNORE_FILE_NAME)

        if not os.path.isfile(ignorefile):
            return ignore

        ignorelist=[]

        if self.verbose and self.callback is not None:
            self.callback(WayBackupEvent.FOUND_IGNORE_FILE, {'name' : srcdir})

        with open(ignorefile, 'r') as f:
            for line in f:
                path=line.strip('\n')
                if not os.path.isabs(path):
                    abspath=os.path.join(srcdir,path)
                    ignorelist.append(abspath)
                    if self.verbose and self.callback is not None:
                        self.callback(WayBackupEvent.ADDED_IGNORED_DIRECTORY, {'name' : abspath})

        if len(ignorelist)==0:
            return ignore

        if ignore is None:
            return set(ignorelist)
        else:
            return ignore | set(ignorelist)

    def process_file(self, srcpath, refpath, tgtpath, ignore=None):
        if (ignore is not None) and (srcpath in ignore):
            self.files_skipped=self.files_skipped+1

            if self.verbose and self.callback is not None:
                self.callback(WayBackupEvent.SKIPPED_FILE, {'name' : srcpath})

            return

        if not os.path.exists(refpath) or not os.path.isfile(refpath):
            self.copy_file(srcpath, tgtpath)
            return

        srcstat = os.stat(srcpath)
        refstat = os.stat(refpath)

        if srcstat.st_mtime > refstat.st_mtime or srcstat.st_size != refstat.st_size:
            self.copy_file(srcpath, tgtpath)
            return

        if not self.dryrun:
            os.link(refpath, tgtpath)

        self.links_created = self.links_created + 1

        if self.verbose and self.callback is not None:
            self.callback(WayBackupEvent.CREATED_LINK, {'name' : srcpath})

        if (srcstat.st_ctime > refstat.st_ctime or
            srcstat.st_mode != refstat.st_mode or
            srcstat.st_uid != refstat.st_uid or
            srcstat.st_gid != refstat.st_gid):
            self.copy_file_attributes(srcpath, tgtpath)
            if self.verbose and self.callback is not None:
                self.callback(WayBackupEvent.COPIED_ATTRIBUTES, {'name' : srcpath})

    def process_other_entity(self, srcpath, refpath, tgtpath):
        return

    def calculate_md5_of_file(path):
        with open(path, "rb") as f:
            file_hash = hashlib.md5()
            while chunk := f.read(8192):
                file_hash.update(chunk)

        return file_hash.hexdigest()

    def copy_file_attributes(self, srcpath, tgtpath):
        if not self.dryrun:
            srcstat = os.stat(srcpath)
            os.chown(tgtpath, srcstat.st_uid, srcstat.st_gid)
            os.chmod(tgtpath, srcstat.st_mode)
            os.utime(tgtpath, ns=(srcstat.st_atime_ns,srcstat.st_mtime_ns))

        if os.path.isfile(tgtpath):
            self.file_attributes_copied = self.file_attributes_copied + 1

    def copy_file(self, srcpath, tgtpath, chunksize = 8192):
        if os.path.islink(srcpath):
            if not self.dryrun:
                os.symlink(os.readlink(srcpath), tgtpath)

            self.symlinks_copied = self.symlinks_copied + 1

            if self.verbose and self.callback is not None:
                self.callback(WayBackupEvent.COPIED_SYMLINK, {'name' : srcpath})

            return
        else:
            if not self.dryrun:
                with open(srcpath, "rb") as fsrc, open(tgtpath, "wb") as ftgt:
                    while chunk := fsrc.read(chunksize):
                        ftgt.write(chunk)

            self.copy_file_attributes(srcpath, tgtpath)

            srcstat = os.stat(srcpath)
            self.bytes_copied = self.bytes_copied + srcstat.st_size
            self.files_copied = self.files_copied + 1

            if self.verbose and self.callback is not None:
                self.callback(WayBackupEvent.COPIED_FILE, {'name' : srcpath, 'size' : srcstat.st_size})

def reporter(event_type, event_dict):
    print(event_type.name)
    if event_dict is not None:
        for key in event_dict:
            print('\t',key,' ==> ',str(event_dict[key]))
    print()

def get_device_number(path):
    while path!="/" and not os.path.exists(path):
        path=os.path.dirname(path)

    pathstat=os.stat(path)

    return pathstat.st_dev

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--verbose", help="increase output verbosity",
                    action="store_true")

    parser.add_argument("--dryrun", help="perform a trial run with no changes",
                    action="store_true")

    parser.add_argument("--srcdir", required=True, help="source directory root")
    parser.add_argument("--refdir", required=True, help="reference directory root")
    parser.add_argument("--tgtdir", required=True, help="target directory root")

    args = parser.parse_args()

    if os.path.exists(args.tgtdir) and not os.path.isdir(args.tgtdir):
        print("ERROR: Target " + args.tgtdir + " is not a directory ... bailing out!", file=sys.stderr)
        exit(2)

    if os.path.exists(args.tgtdir) and len(os.listdir(args.tgtdir)) > 0:
        print("ERROR: Target directory " + args.tgtdir + " is not empty ... bailing out!", file=sys.stderr)
        exit(3)

    refdev=get_device_number(args.refdir)
    tgtdev=get_device_number(args.tgtdir)

    if refdev!=tgtdev:
        print("ERROR: Reference directory MUST be on same device as target directory", file=sys.stderr)
        exit(5)

    backup=WayBackup(callback=reporter, verbose=args.verbose, dryrun=args.dryrun)

    rc=backup.backup(args.srcdir, args.refdir, args.tgtdir)

    exit(rc)
