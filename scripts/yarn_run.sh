#!/bin/bash

set -e -u
set -o pipefail

source .env

ROOT="$PWD"

cd modal-login

yarn start >> "$ROOT/logs/yarn.log" 2>&1