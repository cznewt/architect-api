#!/bin/bash -e

## Overridable parameters

ENABLE_SALT_API=${ENABLE_SALT_API:-1}

SALT_API_PASSWORD=${SALT_API_PASSWORD:-}

## Functions

function log_info() {
    echo "[INFO    ] $*"
}

## Main

if [[ $# -lt 1 ]] || [[ "$1" == "--"* ]]; then

    if [[ $ENABLE_SALT_API -eq 1 ]]; then
        if [ -z $SALT_API_PASSWORD ]; then
            SALT_API_PASSWORD=$(pwgen -1 8)
            log_info "No SALT_API_PASSWORD provided, using auto-generated ${SALT_API_PASSWORD}"
        fi
        log_info "Setting password for user 'salt'"
        echo "salt:${SALT_API_PASSWORD}" | chpasswd

        log_info "Starting 'salt-api' service"
        /usr/bin/salt-api --log-file-level=quiet --log-level=info -d
    fi

    log_info "Starting 'salt-master' service"
    exec /usr/bin/salt-master --log-file-level=quiet --log-level=info "$@"
else
    exec "$@"
fi
