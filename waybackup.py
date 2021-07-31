#!/usr/bin/env python3

import sys, os, stat, hashlib
from datetime import datetime

debug=os.getenv('DEBUG') != None

IGNORE_FILE_NAME='.waybackup.ignore'

directories_traversed = 0
directories_skipped=0
files_copied = 0
files_bytes_copied=0
file_attributes_copied = 0
symlinks_copied = 0
links_created = 0

def traverser(srcdir, refdir, tgtdir, ignore=None):
    global directories_traversed, directories_skipped

    if debug:
        print('\n### ENTER traverser(' + srcdir + ', ' + refdir + ', ' + tgtdir
        + ', ignore=' + str(ignore) + ')')

    if (ignore is not None) and (srcdir in ignore):
        directories_skipped = directories_skipped + 1
        if debug:
            print('# Skipping ' + srcdir + ' because it is in the ignore list.')
        return

    if debug:
        print("#! mkdir " + tgtdir)

    os.makedirs(tgtdir)

    ignore=update_ignore_list(ignore, srcdir)

    for file in os.listdir(srcdir):
        srcpath = os.path.join(srcdir, file)
        refpath = os.path.join(refdir, file)
        tgtpath = os.path.join(tgtdir, file)
        if os.path.islink(srcpath) or os.path.isfile(srcpath):
            process_file(srcpath, refpath, tgtpath)
        elif os.path.isdir(srcpath):
            traverser(srcpath, refpath, tgtpath, ignore)
        else:
            process_other_entity(srcpath, refpath, tgtpath)

    copy_file_attributes(srcdir, tgtdir)

    directories_traversed = directories_traversed + 1

def update_ignore_list(ignore, srcdir):
    ignorefile=os.path.join(srcdir, IGNORE_FILE_NAME)

    if not os.path.isfile(ignorefile):
        return ignore

    ignorelist=[]

    with open(ignorefile, 'r') as f:
        for line in f:
            abspath=os.path.join(srcdir,line.strip('\n'))
            ignorelist.append(abspath)

    if len(ignorelist)==0:
        return ignore


    print('# Adding to ignore list: ' + str(ignorelist))

    if ignore is None:
        return set(ignorelist)
    else:
        return ignore | set(ignorelist)

def process_file(srcpath, refpath, tgtpath):
    global links_created

    if debug:
        print("\n### ENTER process_file(" + srcpath + ", " + refpath  + ", " + tgtpath+ ")")

    if not os.path.exists(refpath):
        if debug:
            print("# refpath does not exist")
        copy_file(srcpath, tgtpath)
        return

    if not os.path.isfile(refpath):
        if debug:
            print("# refpath is not a regular file")
        copy_file(srcpath, tgtpath)
        return

    srcstat = os.stat(srcpath)
    refstat = os.stat(refpath)

    if srcstat.st_mtime > refstat.st_mtime:
        if debug:
            print("# mtime more recent")
        copy_file(srcpath, tgtpath)
        return

    if srcstat.st_size != refstat.st_size:
        if debug:
            print("# size mismatch")
        copy_file(srcpath, tgtpath)
        return

    if srcstat.st_ctime > refstat.st_ctime:
        if debug:
            print("# ctime more recent")
        link_and_set_attributes(srcpath, refpath, tgtpath)
        return

    if srcstat.st_mode != refstat.st_mode:
        if debug:
            print("# mode mismatch")
        link_and_set_attributes(srcpath, refpath, tgtpath)
        return

    if srcstat.st_uid != refstat.st_uid:
        if debug:
            print("# uid mismatch")
        link_and_set_attributes(srcpath, refpath, tgtpath)
        return

    if srcstat.st_gid != refstat.st_gid:
        if debug:
            print("# gid mismatch")
        link_and_set_attributes(srcpath, refpath, tgtpath)
        return

    if debug:
        print("# no change\n#! ln " + refpath + " " + tgtpath)

    os.link(refpath, tgtpath)

    links_created = links_created + 1

def process_other_entity(srcpath, refpath, tgtpath):
    return

def calculate_md5_of_file(path):
    with open(path, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    return file_hash.hexdigest()

def copy_file_attributes(srcpath, tgtpath):
    global file_attributes_copied

    if debug:
        print('#! copyattrs ' + srcpath + ' ' + tgtpath)
    srcstat = os.stat(srcpath)
    os.chown(tgtpath, srcstat.st_uid, srcstat.st_gid)
    os.chmod(tgtpath, srcstat.st_mode)
    os.utime(tgtpath, ns=(srcstat.st_atime_ns,srcstat.st_mtime_ns))

    if os.path.isfile(tgtpath):
        file_attributes_copied = file_attributes_copied + 1

def copy_file(srcpath, tgtpath, chunksize = 8192):
    global files_copied, symlinks_copied, files_bytes_copied

    if os.path.islink(srcpath):
        if debug:
            print("#! ln -s  " + os.readlink(srcpath) + ' ' + tgtpath)
        os.symlink(os.readlink(srcpath), tgtpath)
        symlinks_copied = symlinks_copied + 1
    else:
        if debug:
            print('#! cp -p ' + srcpath + ' ' + tgtpath)
        with open(srcpath, "rb") as fsrc, open(tgtpath, "wb") as ftgt:
            while chunk := fsrc.read(chunksize):
                ftgt.write(chunk)
                files_bytes_copied = files_bytes_copied + len(chunk)

        files_copied = files_copied + 1

        copy_file_attributes(srcpath, tgtpath)

def link_and_set_attributes(srcpath, refpath, tgtpath):
    if debug:
        print('#! ln ' + srcpath + ' ' + tgtpath)
    os.link(refpath, tgtpath)
    copy_file_attributes(srcpath, tgtpath)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: " + sys.argv[0] + " source-directory reference-directory target-directory")
        exit(1)
    else:
        srcdir = sys.argv[1]
        refdir = sys.argv[2]
        tgtdir = sys.argv[3]

    if os.path.exists(tgtdir) and not os.path.isdir(tgtdir):
        print("Target " + tgtdir + " is not a directory ... bailing out!")
        exit(2)

    if os.path.exists(tgtdir) and len(os.listdir(tgtdir)) > 0:
        print("Target directory " + tgtdir + " is not empty ... bailing out!")
        exit(3)

    dtStart=datetime.now()

    traverser(srcdir, refdir, tgtdir)

    dtFinish=datetime.now()

    elapsed='%.3f' % (dtFinish.timestamp()-dtStart.timestamp())

    filebytes="{:,}".format(files_bytes_copied)

    print("WAYBACKUP RUN FINISHED")
    print("Started at " + str(dtStart) + ", finished at " + str(dtFinish) + " (" + elapsed + " seconds)")
    print("Traversed " + str(directories_traversed) + " directories")
    print("Skipped " + str(directories_skipped) + " directories")
    print("Linked " + str(links_created) + " files")
    print("Copied " + str(files_copied) + " files (" + filebytes + " bytes)")
    print("Copied " + str(symlinks_copied) + " symlinks")
    print("Altered " + str(file_attributes_copied) + " sets of file attributes")
