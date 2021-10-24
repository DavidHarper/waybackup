# waybackup

Waybackup is an incremental backup solution for Linux. The main program
is **waybackup.py** which takes three mandatory POSIX-style arguments:

--srcdir **SRCDIR**

This is the *source* directory, which is the directory that you want to
backup.  **waybackup** traverses this directory and all of its sub-directories.

--tgtdir **TGTDIR**

This is the target directory. It is the location where the new incremental backup
will be made. If it exists, then it must be empty. If it does not exist, **waybackup**
will create it.

--refdir **REFDIR**

This is the *reference* directory. Usually, it is the most recent previous backup
of the source directory made using **waybackup**, but it can be an empty directory,
in which case **waybackup** will make a full backup (sometimes called a level zero
backup) of the source directory. If the *reference* directory is not empty, then
*waybackup* will compare every file in it with the corresponding file in the *source*
backup. If the version in the *source* directory is newer, or there is no corresponding
file in the *reference* directory, then *waybackup* will copy the version in the
*source* directory to the *target* directory; otherwise, it will create a hard link
from the version in the *reference* directory.

## Optional arguments

--verbose

This causes **waybackup** to write full details of the processing of every file and
directory to standard output.

--dry-run

This causes **waybackup** to scan the *source* and *reference* directories, comparing
files, but it does not write anything to the *target* directory.
