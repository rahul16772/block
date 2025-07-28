#!/bin/bash

set -e -u
set -o pipefail

# Test if file exists, if so, source .env
if [[ -f "$PWD"/.env ]]; then
    source "$PWD"/.env
fi

ROOT="$PWD"

cd modal-login

yarn start >> "$ROOT/logs/yarn.log" 2>&1