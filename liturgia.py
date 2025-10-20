#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Estrattore Liturgia del Giorno - Versione semplificata
"""
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import sys
import os
import time


def extract_liturgia_giorno(data):
    """Estrae la liturgia del giorno"""
    url = f"https://www.chiesacattolica.it/liturgia-del-giorno/?data-liturgia={data}"

    try:
        # Aggiungi delay e user agent
        time.sleep(1)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        r = requests.get(url, headers=headers, timeout=30)
        r.encoding = 'utf-8'
        r.raise_for_status()
    except Exception as e:
        print(f"Errore fetch: {e}")
        return None

    soup = BeautifulSoup(r.text, 'html.parser')

    # Rimuovi elementi inutili
    for el in soup(['script', 'style', 'nav', 'footer', 'header']):
        el.decompose()

    # Cerca il contenuto principale
    main = soup.find('main')
    if not main:
        main = soup.find('article')
    if not main:
        main = soup.body

    if not main:
        print("Nessun contenuto trovato")
        return None

    # Estrai tutto il testo
    text = main.get_text('\n', strip=True)
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    if len(lines) < 10:
        print(f"Troppo poche righe: {len(lines)}")
        return None

    sezioni = {}
    sezione_attuale = None
    contenuto = []

    sezioni_keys = [
        'PRIMA LETTURA',
        'SALMO RESPONSORIALE',
        'SECONDA LETTURA',
        'CANTO AL VANGELO',
        'ACCLAMAZIONE AL VANGELO',
        'VANGELO',
        'SULLE OFFERTE',
        'ANTIFONA ALLA COMUNIONE',
        'DOPO LA COMUNIONE'
    ]

    for line in lines:
        # Ferma se trovi testo non liturgico
        if 'Scarica' in line or 'Privacy' in line or 'Cookie' in line:
            break

        # Verifica se è intestazione sezione
        is_header = False
        for key in sezioni_keys:
            if line == key or line.upper() == key:
                # Salva sezione precedente
                if sezione_attuale and contenuto:
                    testo = '\n'.join(contenuto).strip()

                    # ANTIFONA ALLA COMUNIONE e DOPO LA COMUNIONE devono finire con "Per Cristo nostro Signore."
                    if sezione_attuale in ['ANTIFONA ALLA COMUNIONE', 'DOPO LA COMUNIONE']:
                        if 'Per Cristo nostro Signore.' in testo:
                            testo = testo[:testo.find('Per Cristo nostro Signore.') + len('Per Cristo nostro Signore.')]

                    sezioni[sezione_attuale] = testo

                sezione_attuale = key
                contenuto = []
                is_header = True
                break

        if not is_header and sezione_attuale:
            contenuto.append(line)

    # Salva ultima sezione
    if sezione_attuale and contenuto:
        testo = '\n'.join(contenuto).strip()

        # ANTIFONA ALLA COMUNIONE e DOPO LA COMUNIONE devono finire con "Per Cristo nostro Signore."
        if sezione_attuale in ['ANTIFONA ALLA COMUNIONE', 'DOPO LA COMUNIONE']:
            if 'Per Cristo nostro Signore.' in testo:
                testo = testo[:testo.find('Per Cristo nostro Signore.') + len('Per Cristo nostro Signore.')]

        sezioni[sezione_attuale] = testo

    return {
        'data': data,
        'url': url,
        'sezioni': sezioni
    }


def formato_data(data_str):
    """Formatta data"""
    try:
        dt = datetime.strptime(data_str, '%Y%m%d')
        giorni = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
        mesi = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
                'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']
        return f"{giorni[dt.weekday()]} {dt.day} {mesi[dt.month - 1]} {dt.year}"
    except:
        return data_str


def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    os.makedirs('json', exist_ok=True)

    for data in sys.argv[1:]:
        liturgia = extract_liturgia_giorno(data)

        if liturgia and liturgia['sezioni']:
            out = f"json/liturgia_{data}.json"
            with open(out, 'w', encoding='utf-8') as f:
                json.dump(liturgia, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()