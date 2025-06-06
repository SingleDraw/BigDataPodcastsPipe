#!/bin/bash

# # paths is relative to gh workflow working directory
# UTILS_DIR="../scripts/utils"

# Get the absolute path of the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UTILS_DIR="$SCRIPT_DIR/utils"

PROMPT="This is a test prompt for the test utility script."

source "../scripts/utils/test-util.sh" "$PROMPT" "$PROMPT"

test_util "$PROMPT" "$PROMPT"