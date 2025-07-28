#!/bin/bash

set -e -u
set -o pipefail

mkdir -p ~/.gradle
touch ~/.gradle/gradle.properties && echo "org.gradle.daemon=true" >> ~/.gradle/gradle.properties
