#!/bin/bash

# Start the Telegram bot in the background
echo "Starting Telegram bot..."
python telegram-bot/bot.py &

# Start the FastAPI server in the foreground
echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000