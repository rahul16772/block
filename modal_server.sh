#!/bin/bash

set -e -u
set -o pipefail

ROOT="$PWD"
DOCKER=${DOCKER:-""}

# This is an address good enough for testing.
export SMART_CONTRACT_ADDRESS="0xE2070109A0C1e8561274E59F024301a19581d45c"

# Function to setup Node.js and NVM
setup_node_nvm() {
    echo "Setting up Node.js and NVM..."

    if ! command -v node > /dev/null 2>&1; then
        echo "Node.js not found. Installing NVM and latest Node.js..."
        export NVM_DIR="$HOME/.nvm"
        if [ ! -d "$NVM_DIR" ]; then
            curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
        fi
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
        nvm install node
    else
        echo "Node.js is already installed: $(node -v)"
    fi

    if ! command -v yarn > /dev/null 2>&1; then
        # Detect Ubuntu (including WSL Ubuntu) and install Yarn accordingly
        if grep -qi "ubuntu" /etc/os-release 2> /dev/null || uname -r | grep -qi "microsoft"; then
            echo "Detected Ubuntu or WSL Ubuntu. Installing Yarn via apt..."
            curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
            echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
            sudo apt update && sudo apt install -y yarn
        else
            echo "Yarn not found. Installing Yarn globally with npm (no profile edits)…"
            # This lands in $NVM_DIR/versions/node/<ver>/bin which is already on PATH
            npm install -g --silent yarn
        fi
    fi
}

# Function to setup environment file
setup_environment() {
    echo "Setting up environment configuration..."

    ENV_FILE="$ROOT"/modal-login/.env
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS version
        sed -i '' "3s/.*/SMART_CONTRACT_ADDRESS=$SMART_CONTRACT_ADDRESS/" "$ENV_FILE"
    else
        # Linux version
        sed -i "3s/.*/SMART_CONTRACT_ADDRESS=$SMART_CONTRACT_ADDRESS/" "$ENV_FILE"
    fi

    echo "Environment file updated with SMART_CONTRACT_ADDRESS: $SMART_CONTRACT_ADDRESS"
}

mkdir -p "$ROOT/logs"

cd modal-login
rm -rf node_modules
echo "Running modal server from $PWD"

### Install Node, NVM, Yarn if needed.
setup_node_nvm

### Setup environment configuration
setup_environment

echo "Installing dependencies..."
yarn install --immutable

echo "Building server..."
yarn build

echo "Running server..."
yarn start >> "$ROOT/logs/yarn.log" 2>&1 & # Run in background and log output

SERVER_PID=$!  # Store the process ID
echo "Started server process: $SERVER_PID"
sleep 5

# Try to open the URL in the default browser
if [ -z "$DOCKER" ]; then
    if open http://localhost:3000 2> /dev/null; then
        echo ">> Successfully opened http://localhost:3000 in your default browser."
    else
        echo ">> Failed to open http://localhost:3000. Please open it manually."
    fi
else
    echo ">> Please open http://localhost:3000 in your host browser."
fi

cd ..

echo ">> Waiting for modal userData.json to be created..."
while [ ! -f "modal-login/temp-data/userData.json" ]; do
    sleep 5  # Wait for 5 seconds before checking again
done
echo "Found userData.json. Proceeding..."

export BA_ORG_ID=$(awk 'BEGIN { FS = "\"" } !/^[ \t]*[{}]/ { print $(NF - 1); exit }' modal-login/temp-data/userData.json)
export BA_ADDRESS_EOA=$(awk -F'"' '/"address"/ { print $4; exit }' modal-login/temp-data/userData.json)
export BA_ADDRESS_ACCOUNT=$(awk -F'"' '/"accountAddress"/ { print $4; exit }' modal-login/temp-data/userApiKey.json)

# TODO: Kill the sever running at port 3000 once the job finishes