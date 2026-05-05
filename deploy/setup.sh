#!/bin/bash
set -e

DEST=/opt/vvf-ferie-bot

echo "=== 1. Installa dipendenze di sistema ==="
sudo apt-get update -q
sudo apt-get install -y python3 python3-venv python3-pip

echo "=== 2. Copia i file del bot ==="
sudo mkdir -p "$DEST"
sudo rsync -a --exclude=venv --exclude=__pycache__ --exclude="*.db" \
    "$(dirname "$0")/../" "$DEST/"
sudo chown -R ubuntu:ubuntu "$DEST"

echo "=== 3. Crea il virtualenv e installa pacchetti ==="
cd "$DEST"
python3 -m venv venv
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q -r requirements.txt

echo "=== 4. Configura le variabili d'ambiente ==="
if [ ! -f "$DEST/.env" ]; then
    cp "$DEST/.env.example" "$DEST/.env"
    echo ""
    echo ">>> ATTENZIONE: compila $DEST/.env con i tuoi valori reali, poi riesegui:"
    echo "    sudo systemctl restart vvf-ferie"
    echo ""
fi

echo "=== 5. Installa e avvia il servizio systemd ==="
sudo cp "$DEST/deploy/vvf-ferie.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vvf-ferie
sudo systemctl restart vvf-ferie

echo ""
echo "=== FATTO ==="
echo "Stato: sudo systemctl status vvf-ferie"
echo "Log:   sudo journalctl -u vvf-ferie -f"
