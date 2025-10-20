#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Estrattore Santo del Giorno
https://www.chiesacattolica.it/santo-del-giorno/
"""
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import html
import unicodedata
import sys
import re
import os


def clean_text(text):
    """Pulisce il testo"""
    if not text:
        return ""

    text = html.unescape(text)

    replacements = {
        'â€™': "'", 'â€"': "—", 'â€œ': '"', 'â€': '"',
        'Ã¨': 'è', 'Ã©': 'é', 'Ã¬': 'ì', 'Ã²': 'ò',
        'Ã¹': 'ù', 'Ã ': 'à', 'Ãˆ': 'È', '\u0001': '',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = unicodedata.normalize('NFC', text)
    text = ''.join(c for c in text if c in '\n\t' or not unicodedata.category(c).startswith('C'))

    return text.strip()


def extract_santo_giorno(data):
    """Estrae santo del giorno"""
    url = f"https://www.chiesacattolica.it/santo-del-giorno/?data-liturgia={data}"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.encoding = 'utf-8'
        response.raise_for_status()
    except Exception as e:
        print(f"Errore: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')

    # Estrai santo principale dal title
    title_tag = soup.find('title')
    title_text = title_tag.get_text() if title_tag else ""

    santo_principale = ""
    if " - Chiesacattolica.it" in title_text:
        parts = title_text.replace(" - Chiesacattolica.it", "").split(" ", 4)
        if len(parts) >= 5:
            santo_principale = " ".join(parts[4:]).strip()

    # Estrai contenuto
    page_text = soup.get_text(separator="\n")
    lines = [clean_text(line) for line in page_text.split("\n") if clean_text(line)]

    content_lines = []
    start_extracting = False

    for line in lines:
        if "Santo del giorno" in line:
            start_extracting = True
            continue

        if start_extracting and line and not line.startswith("http"):
            content_lines.append(line)

    # Estrai santi
    santi = []
    current_santo = ""

    # Patterns per inizio santo: posizione geografica o "A " prefixes
    location_pattern = r'^(A|Ad|Presso|Nel|Nella|Nell|Nell\'|Vicino|In|Presso|A Roma|A Gerusalemme)\s+'

    for line in content_lines:
        # Se la linea inizia con location pattern - è un nuovo santo
        if re.match(location_pattern, line, re.IGNORECASE):
            if current_santo:
                # Estrai nome santo e martirologio
                santo_entry = parse_santo(current_santo)
                santi.append(santo_entry)
            current_santo = line
        else:
            if current_santo:
                current_santo += " " + line

    # Aggiungi ultimo santo
    if current_santo:
        santo_entry = parse_santo(current_santo)
        santi.append(santo_entry)

    return {
        "data": data,
        "data_formattata": formato_data(data),
        "url": url,
        "santo_principale": santo_principale,
        "santi_commemorati": santi,
        "numero_santi": len(santi),
        "testo_completo": " ".join(content_lines)
    }


def parse_santo(text):
    """Estrae nome santo e martirologio dal testo"""
    text = text.strip()

    # Pattern: "A Roma, San Paolo della Croce, sacerdote"
    # Cerchiamo di separare il nome del santo dal resto

    # Prima, estrai il nome: cerca pattern "San/Santa NOME"
    name_match = re.search(r'(San|Santa|S\.)\s+([A-Za-z\s]+?)(?:,|\.|—|–|$)', text)

    if name_match:
        nome = name_match.group(0).replace(',', '').strip()
    else:
        nome = ""

    # Il martirologio è il resto del testo
    martirologio = text.strip()

    return {
        "nome": nome,
        "martirologio": martirologio
    }


def formato_data(date_string):
    """Formatta data"""
    try:
        dt = datetime.strptime(date_string, "%Y%m%d")
        giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
        return f"{giorni[dt.weekday()]} {dt.day} {mesi[dt.month - 1]} {dt.year}"
    except:
        return date_string


def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    os.makedirs("json", exist_ok=True)

    for data in sys.argv[1:]:
        santo = extract_santo_giorno(data)

        if santo:
            output_file = f"json/santo_{data}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(santo, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()