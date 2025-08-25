#!/bin/bash

# custom echo function with red color and arrow
print() {
    echo -e "\033[32m---> $*\033[0m"
}
error() {
    echo -e "\033[31m---> $*\033[0m"
    exit 1
}
input () {
    echo -ne "\033[33m---> $*\033[0m"
}

# parse command line arguments
if [ $# -ne 2 ]; then
    error "Usage: $0 <BACKUP_DIRECTORY> <RESTIC_REPOSITORY>"
fi

BACKUP_DIRECTORY="$1"
RESTIC_REPOSITORY="$2"

# validate backup directory exists
if [ ! -d "$BACKUP_DIRECTORY" ]; then
    error "Backup directory '$BACKUP_DIRECTORY' does not exist"
fi

# check if running with sudo
if [ "$EUID" -ne 0 ]; then
    error "Running with sudo is advised, quitting"
fi

print "Backing up $BACKUP_DIRECTORY to $RESTIC_REPOSITORY"

# prompt for password
input "Enter restic repository password: "
read -s RESTIC_PASSWORD
echo

export RESTIC_REPOSITORY
export RESTIC_PASSWORD

# check restic repository validity
print "Checking restic repository"
restic cat config || error "Repository not found or not initialized, quitting"

# backup folder
print "Backing up $BACKUP_DIRECTORY"
restic backup "$BACKUP_DIRECTORY" -v || error "Error during backup, quitting"

# prune old snapshots
print "Pruning old snapshots"
restic forget --keep-last 30 --prune -v || error "Error during pruning, quitting"

# check integrity
print "Checking repository integrity"
restic check || error "Error during integrity check, quitting"
