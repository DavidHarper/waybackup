# waybackup

Waybackup is an incremental backup solution for Linux.

## Usage

The main program is **waybackup.py** which takes three mandatory POSIX-style arguments:

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
backup.

If the version in the *source* directory is newer, or there is no corresponding
file in the *reference* directory, then *waybackup* will copy the version in the
*source* directory to the *target* directory; otherwise, it will create a hard link
from the version in the *reference* directory.

**waybackup** will also adjust the ownership and permissions of each file and directory
that it copies or links to the *target* directory to match those in the *source* directory.

You are advised to run **waybackup** as **root** when backing up files and directories
belonging to multiple users and groups. It will exit immediately upon encountering a
file or directory that it cannot open, or upon failing to change the ownership or
permissions during the backup process.

## Optional arguments

--verbose

This causes **waybackup** to write full details of the processing of every file and
directory to standard output.

--dry-run

This causes **waybackup** to scan the *source* and *reference* directories, comparing
files, but it does not write anything to the *target* directory.

## Telling waybackup to ignore sub-directories

When **waybackup** begins processing each directory in the *source* directory tree, it
looks for a file named **.waybackup.ignore** and reads its contents. Each line in this
file, if it exists, specifies a sub-directory **of that directory** which should be ignored.
For example, if **waybackup** is processing a directory named *projects/python3* and this
directory contains a **.waybackup.ignore** file with the single line

`tmp`

then **waybackup** will skip the directory *projects/python3/tmp* and all sub-directories
of that directory.

You can specify ignore lists at *any* point in the directory structure, so to tell
**waybackup** to ignore *projects/python3/tmp*, you have three options. One has already
been described. Equivalently, you could put the line

`python3/tmp`

in the **.waybackup.ignore** file in the *projects* directory, or the line

`projects/python3/tmp`

in the **.waybackup.ignore** file in the top-level *source* directory specified by the
**--srcdir** argument.

Note that wildcards are not allowed in any **.waybackup.ignore** file. Directory names must
match exactly.

## Using a MySQL database to record waybackup runs

The script **waybackup-db.py** extends the basic operation of **waybackup.py** by
logging the results of each backup run to a MySQL database. The database connection
parameters must be specified via environment variables:

- WAYBACKUP_HOST
- WAYBACKUP_PORT
- WAYBACKUP_DATABASE
- WAYBACKUP_USERNAME
- WAYBACKUP_PASSWORD
- WAYBACKUP_DRIVER

This script uses **SQLAlchemy** and **PyMySQL**, although other MySQL drivers should
work, provided that they are compatible with **SQLAlchemy**.

The database schema can be created using the SQL script named **waybackup-db.sql**.

For convenience, a wrapper Bash script named **waybackup-wrapper.sh** can be used to
automatically select the correct Python script to use, depending on whether the required
environment variables are set.

## License

This software is distributed under the GNU General Public License version 3. Please
read the file named **LICENSE**.

## DISCLAIMER

THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
APPLICABLE LAW.  EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY
OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM
IS WITH YOU.  SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
ALL NECESSARY SERVICING, REPAIR OR CORRECTION.
