#!/bin/bash

set -e -u
set -o pipefail

ROOT="$PWD"

source ./scripts/node_env.sh

cd modal-login

### Install Node, NVM, Yarn if needed.
setup_node_nvm

### Setup environment configuration
setup_environment

echo "Installing dependencies..."
yarn install --immutable

echo "Building server..."
yarn build
