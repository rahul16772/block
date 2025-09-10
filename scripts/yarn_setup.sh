#!/bin/bash

set -e -u
set -o pipefail

ROOT="$PWD"
LOG_DIR="$ROOT/logs"
YARN_LOG="$LOG_DIR/yarn_setup.log"

# logs klasörü yoksa oluştur
mkdir -p "$LOG_DIR"

# Node ve environment scriptini yükle
source ./scripts/node_env.sh

cd modal-login

if [ ! -d .next ]; then
    ### Install Node, NVM, Yarn if needed.
    setup_node_nvm

    ### Setup environment configuration
    setup_environment

    ### Install dependencies
    echo "Installing dependencies..." | tee -a "$YARN_LOG"
    yarn install --immutable 2>&1 | tee -a "$YARN_LOG"

    ### Build server
    echo "Building server..." | tee -a "$YARN_LOG"
    yarn build 2>&1 | tee -a "$YARN_LOG"

fi
