#!/bin/bash
# Start script for CodeVerse Discord Bot (portable)
echo "Starting CodeVerse Discord Bot..."
cd "$(dirname "$0")" || exit 1
python src/bot.py
