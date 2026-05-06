#!/bin/bash
set -e
if [ -n "$GOOGLE_CREDENTIALS_JSON" ]; then
    echo "$GOOGLE_CREDENTIALS_JSON" > /tmp/credentials.json
fi
exec python bot.py
