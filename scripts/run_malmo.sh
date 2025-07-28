#!/bin/bash

set -e -u
set -o pipefail

. blockassist-venv/bin/activate
python -m malmo.minecraft launch --num_instances 2 --goal_visibility True False > 'logs/malmo.log' 2>&1