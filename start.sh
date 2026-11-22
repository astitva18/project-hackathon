#!/usr/bin/env sh
cd "$(dirname "$0")"
python3 -m pip install -r backend/requirements.txt
echo "Starting ResQLink on http://localhost:8000  (phones: use the QR code on the command centre)"
python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
