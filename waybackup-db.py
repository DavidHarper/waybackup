#!/usr/bin/env python3

from waybackup import WayBackup, WayBackupEvent
from sqlalchemy import create_engine,Table,MetaData,insert,update
import os
import argparse

class WayBackupDatabaseRecorder:
    def __init__(self, prefix="WAYBACKUP_"):
        self.get_connection(prefix)

    def get_connection(self, prefix):
        db_driver=os.getenv(prefix+"DRIVER")
        db_username=os.getenv(prefix+"USERNAME")
        db_password=os.getenv(prefix+"PASSWORD")
        db_host=os.getenv(prefix+"HOST")
        db_port=os.getenv(prefix+"PORT", "3306")
        db_database=os.getenv(prefix+"DATABASE")

        url=db_driver+"://"+db_username+":"+db_password+"@"+db_host+":"+db_port+"/"+db_database

        self.engine=create_engine(url, future=True)

        metadata=MetaData()

        self.backup_history_table=Table('backup_history',metadata,autoload_with=self.engine)

        self.backup_copied_file_table=Table('backup_copied_file',metadata,autoload_with=self.engine)

    def started_backup(self, event_dict):
        if event_dict['dryrun']:
            dryrun='YES'
        else:
            dryrun='NO'

        stmt=insert(self.backup_history_table).values(
            started=event_dict['start_time'],
            dryrun=dryrun,
            srcdir=event_dict['srcdir'],
            refdir=event_dict['refdir'],
            tgtdir=event_dict['tgtdir'])

        compiled=stmt.compile()

        with self.engine.connect() as conn:
            result=conn.execute(stmt)
            self.backup_id=result.inserted_primary_key[0]
            conn.commit()

    def finished_backup(self, event_dict):
        stmt=(update(self.backup_history_table).
            where(self.backup_history_table.c.id==self.backup_id).
            values(finished=event_dict['finish_time'],
                   directories_processed=event_dict['directories_processed'],
                   directories_skipped=event_dict['directories_skipped'],
                   files_copied=event_dict['files_copied'],
                   bytes_copied=event_dict['bytes_copied'],
                   symlinks_copied=event_dict['symlinks_copied'],
                   links_created=event_dict['links_created'],
                   status=event_dict['status']))

        with self.engine.connect() as conn:
            conn.execute(stmt)
            conn.commit()

    def copied_file(self, event_dict):
        stmt=insert(self.backup_copied_file_table).values(
            backup_id=self.backup_id,
            srcpath=event_dict['name'],
            filesize=event_dict['size'])

        compiled=stmt.compile()

        with self.engine.connect() as conn:
            result=conn.execute(stmt)
            conn.commit()

recorder=WayBackupDatabaseRecorder()

def reporter(event_type, event_dict):
    if event_type==WayBackupEvent.STARTED_BACKUP:
        recorder.started_backup(event_dict)
    elif event_type==WayBackupEvent.FINISHED_BACKUP:
        recorder.finished_backup(event_dict)
    elif event_type==WayBackupEvent.COPIED_FILE:
        recorder.copied_file(event_dict)

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

    backup=WayBackup(callback=reporter, verbose=args.verbose, dryrun=args.dryrun)

    rc=backup.backup(args.srcdir, args.refdir, args.tgtdir)

    exit(rc)
