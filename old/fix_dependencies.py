#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Dipendenze - Risolvi conflitti Flask/Click
Esegui: python fix_dependencies.py
"""
import sys
import subprocess


def run_command(cmd):
    """Esegue comando e ritorna True se successo"""
    print(f"⏳ Eseguendo: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Successo\n")
            return True
        else:
            print(f"❌ Errore: {result.stderr}\n")
            return False
    except Exception as e:
        print(f"❌ Errore: {e}\n")
        return False


def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║           FIX DIPENDENZE - Conflitti Flask/Click           ║
╚════════════════════════════════════════════════════════════╝
""")

    print("1️⃣  Disinstallo Flask e dipendenze...")
    run_command([sys.executable, "-m", "pip", "uninstall", "-y", "flask", "click", "werkzeug"])

    print("2️⃣  Pulisco cache pip...")
    run_command([sys.executable, "-m", "pip", "cache", "purge"])

    print("3️⃣  Installo versioni compatibili...")
    packages = [
        "click==8.1.7",
        "Werkzeug==3.0.1",
        "Flask==3.0.0",
        "requests==2.31.0",
        "beautifulsoup4==4.12.2"
    ]

    for pkg in packages:
        if not run_command([sys.executable, "-m", "pip", "install", "--no-cache-dir", pkg]):
            print(f"⚠️  Problema con {pkg}, continuando...")

    print("\n4️⃣  Verifico installazione...")
    try:
        import flask
        import click
        import requests
        from bs4 import BeautifulSoup

        print(f"✅ Flask: {flask.__version__}")
        print(f"✅ Click: {click.__version__}")
        print(f"✅ Requests: {requests.__version__}")
        print(f"✅ BeautifulSoup4: {BeautifulSoup}")
    except ImportError as e:
        print(f"❌ Errore import: {e}")
        return False

    print("""
╔════════════════════════════════════════════════════════════╗
║                   ✅ FIX COMPLETATO!                       ║
╚════════════════════════════════════════════════════════════╝

Adesso puoi avviare:
  python app.py

Se il problema persiste, prova:
  pip install --upgrade pip
  pip install --upgrade --force-reinstall Flask
""")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)