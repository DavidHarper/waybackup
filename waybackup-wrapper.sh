#!/bin/bash

bailout () {
    message="${1}"

    echo "WayBackup ERROR: ${message} ... bailing out!"

    exit 2
}

if [ $# -lt 2 ]
then
    echo "Usage: $0 waybackup-target directory [directory ...]"
    exit 1
fi

TARGET_BASE="$1"
shift

SCRIPT_HOME=`dirname $0`

WAYBACKUP="${SCRIPT_HOME}/waybackup.py"

if [ ! -f "${WAYBACKUP}" ]
then
    bailout "Python3 script ${WAYBACKUP} does not exist"
fi

if [ ! -d "${TARGET_BASE}" ]
then
    bailout "Target base directory ${TARGET_BASE} does not exist"
fi

LATEST_SYMLINK="${TARGET_BASE}/latest"

if [ ! -L "${LATEST_SYMLINK}" ]
then
    bailout "Target directory ${TARGET_BASE} has no latest symlink"
fi

LATEST_DIR=`readlink -f ${LATEST_SYMLINK}`

if [ ! -d "${LATEST_DIR}" ]
then
    bailout "Latest directory ${LATEST_DIR} does not exist"
fi

TIMESTAMP=`date +%Y-%m-%d_%H-%M-%S`

TARGET_DIR="${TARGET_BASE}/${TIMESTAMP}"

if [ -e "${TARGET_DIR}" ]
then
    bailout "Target directory ${TARGET_DIR} already exists"
fi

for SRCDIR in "$@"
do
    echo "WayBackup RUNNING: ${SRCDIR} ${LATEST_DIR}/${SRCDIR} ${TARGET_DIR}/${SRCDIR}"

    python3 "${WAYBACKUP}" "${SRCDIR}" "${LATEST_DIR}/${SRCDIR}" "${TARGET_DIR}/${SRCDIR}"

    RC=$?

    if [ $RC -ne 0 ]
    then
        /bin/rm -rf "${TARGET_DIR}"

        bailout "An error occurred during the backup procedure"
    fi

    echo ''
done

/bin/rm -f "${LATEST_SYMLINK}"

ln -s "${TIMESTAMP}" "${LATEST_SYMLINK}"

echo "WayBackup SUCCESS: latest backup is in ${TARGET_DIR}"

exit 0
