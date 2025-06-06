#!/bin/bash

set -e

# ---------------------------------------------------------
# Test utility script for various operations
# ---------------------------------------------------------

echo "Running test utility script..."
function test_util() {
  local prompt="$1"
  local response="$2"

  echo "Prompt: $prompt"
  echo "Response: $response"

  # Simulate some processing
  sleep 1

  echo "Test utility script completed successfully."
}