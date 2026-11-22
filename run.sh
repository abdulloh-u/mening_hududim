#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo "      MENING HUDUDIM 🇺🇿 — Veb-Platforma Ishga Tushmoqda   "
echo "=========================================================="
echo "Manzil: http://127.0.0.1:8000"
echo "Admin panel: http://127.0.0.1:8000/portal/"
echo "Django admin: http://127.0.0.1:8000/admin/"
echo "Super Adminlar: Abu va bosh_admin (parollar bir marta ko'rsatilgan)"
echo "=========================================================="

"$DIR/venv/bin/python" manage.py runserver 0.0.0.0:8000
