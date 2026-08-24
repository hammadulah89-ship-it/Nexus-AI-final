#!/usr/bin/env bash
echo "==================================================="
echo "          NexusAI Studio OS Launcher               "
echo "==================================================="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 is not detected on your system."
    echo "[*] Please install Python 3 from https://www.python.org/downloads/"
    exit 1
fi

echo "[*] Installing required dependencies..."
python3 -m pip install -r requirements.txt --quiet

echo "[*] Starting NexusAI Studio OS on http://localhost:8000 ..."

# Open default browser based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    sleep 1 && open "http://localhost:8000" &
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sleep 1 && xdg-open "http://localhost:8000" 2>/dev/null &
fi

python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
