#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo "      MENING HUDUDIM 🇺🇿 — Telegram Bot Ishga Tushmoqda     "
echo "=========================================================="
echo "Bot tokeni va admin ID: .env faylidan o'qiladi"
echo "=========================================================="

"$DIR/venv/bin/python" bot.py
