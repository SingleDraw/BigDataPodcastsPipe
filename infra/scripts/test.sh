#!/bin/bash
set -e

# ---------------------------------------------------------
# Get the absolute path of the directory containing this script
# and set the path to the utils directory
# ---------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UTILS_DIR="$SCRIPT_DIR/utils"
# ---------------------------------------------------------

PROMPT="This is a test prompt for the test utility script."

source "$UTILS_DIR/test-util.sh" "$PROMPT" "$PROMPT"

test_util "$PROMPT" "$PROMPT"