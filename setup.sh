#!/bin/bash

set -e -u
set -o pipefail

OS="$(uname -r)"
WORKDIR="$PWD"

echo "Running on $OS"

BLOCKASSIST_TMP="$(mktemp -d /tmp/blockassist-XXXXXX)"
echo "Made temporary directory $BLOCKASSIST_TMP"
cd "$BLOCKASSIST_TMP"

if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Opening JDK installer"

    curl https://cdn.azul.com/zulu/bin/zulu8.25.0.1-jdk8.0.152-macosx_x64.dmg -o zulu8.25.0.1-jdk8.0.152-macosx_x64.dmg
    open zulu8.25.0.1-jdk8.0.152-macosx_x64.dmg
    echo "Wait for JDK to complete installation before continuing. Press Enter when it is installed."
    read -p "Press enter to continue"

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Installing JDK to /opt"

    curl https://cdn.azul.com/zulu/bin/zulu8.25.0.1-ca-jdk8.0.152-linux_x64.tar.gz -o zulu8.25.0.1-ca-jdk8.0.152-linux_x64.tar.gz
    sudo tar -xf zulu8.25.0.1-ca-jdk8.0.152-linux_x64.tar.gz -C /opt
    echo "export JAVA_PATH=/opt/zulu8.25.0.1-jdk8.0.152-linux_x64" >>$HOME/.bashrc
    echo "export PATH=\$JAVA_PATH/bin:\$PATH" >>$HOME/.bashrc

fi

echo "JDK is installed"
