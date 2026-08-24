#!/usr/bin/env bash
echo "==================================================================="
echo "            ✦ NexusAI Studio OS Master Launcher ✦                  "
echo "   Nexus Technologies Limited - CEO Mr. Hammadullah Khalid         "
echo "==================================================================="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 is not detected on your system."
    echo "[*] Please install Python 3 from https://www.python.org/downloads/"
    exit 1
fi

echo "[*] Step 1/3: Checking dependencies..."
python3 -m pip install -r requirements.txt --quiet

echo "[*] Step 2/3: Starting NexusAI server on port 8000..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > server_output.log 2>&1 &
SERVER_PID=$!

sleep 2

URL="https://nexusai-studio.serveousercontent.com"

echo "[*] Step 3/3: Opening browser & launching live public tunnel..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$URL" &
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open "$URL" 2>/dev/null &
fi

echo ""
echo "==================================================================="
echo "  🚀 NexusAI Studio OS is LIVE WORLDWIDE!"
echo "  🌐 Your Professional Public Link:"
echo "     $URL"
echo ""
echo "  [*] Keep this terminal open to keep your AI online."
echo "==================================================================="
echo ""

trap "kill $SERVER_PID 2>/dev/null; exit" SIGINT SIGTERM EXIT

while true; do
    ssh -o ServerAliveInterval=30 -o StrictHostKeyChecking=no -R nexusai-studio:80:localhost:8000 serveo.net
    sleep 3
done
