#!/bin/bash
set -e

PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Create group with the requested GID
if ! getent group appgroup > /dev/null 2>&1; then
    groupadd -g "$PGID" appgroup
else
    groupmod -o -g "$PGID" appgroup
fi

# Create user with the requested UID
if ! getent passwd appuser > /dev/null 2>&1; then
    useradd -o -u "$PUID" -g "$PGID" -s /bin/bash -M appuser
else
    usermod -o -u "$PUID" -g "$PGID" appuser
fi

# Ensure the data directory is owned by the app user
chown -R appuser:appgroup /app/data

exec gosu appuser "$@"
