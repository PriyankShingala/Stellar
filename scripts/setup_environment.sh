#!/bin/bash
echo "==================================================="
echo "  Stellar-AI / PRAYOG-AI Linux/macOS Setup Script"
echo "==================================================="
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
echo "Setup complete! Run deployment/run_app.sh to launch application."
