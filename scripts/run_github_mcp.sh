#!/bin/bash
# Unix script to launch GitHub MCP server
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

if [ -f "$ENV_FILE" ]; then
    GITHUB_TOKEN=$(grep -E "^GITHUB_PERSONAL_ACCESS_TOKEN=" "$ENV_FILE" | cut -d'=' -f2-)
    export GITHUB_TOKEN
fi

npx -y @modelcontextprotocol/server-github
