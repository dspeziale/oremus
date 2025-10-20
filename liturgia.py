#!/usr/bin/env python3
"""
Estrattore completo della Liturgia del Giorno
Legge tutti i dettagli da https://www.chiesacattolica.it/liturgia-del-giorno/
"""
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import html
import unicodedata
import sys


def clean_text(text):
    """Pulisce il testo da caratteri speciali e HTML entities"""
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


def extract_liturgia_giorno(data_liturgia):
    """Estrae tutti i dettagli della Liturgia del Giorno"""
    url = f"https://www.chiesacattolica.it/liturgia-del-giorno/?data-liturgia={data_liturgia}"

    try:
        headers = {
            'Accept-Charset': 'utf-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.encoding = 'utf-8'
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Errore nel fetching: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')

    # Estrai tutto il testo
    page_text = soup.get_text(separator="\n")
    lines = [clean_text(line) for line in page_text.split("\n") if clean_text(line)]

    # Struttura dati
    liturgia = {
        "data": data_liturgia,
        "url": url,
        "sezioni": {}
    }

    # Estrai sezioni principali
    current_section = None
    current_content = []

    for line in lines:
        # Identifichi le sezioni principali
        if line.upper() in [
            "PRIMA LETTURA", "SALMO RESPONSORIALE", "SECONDA LETTURA",
            "CANTO AL VANGELO", "VANGELO", "OMELIA", "PREGHIERA DEI FEDELI",
            "ANTIFONA D'INGRESSO", "ANTIFONA ALLA COMUNIONE", "ANTIFONA DOPO LA COMUNIONE",
            "INTROITO", "GRADUALE", "ALLELUIA", "TRACCIA", "COMMENTO"
        ]:
            if current_section and current_content:
                liturgia["sezioni"][current_section] = "\n".join(current_content)
            current_section = line.upper()
            current_content = []
        elif current_section:
            current_content.append(line)

    # Salva ultima sezione
    if current_section and current_content:
        liturgia["sezioni"][current_section] = "\n".join(current_content)

    return liturgia


def formato_data(date_string):
    """Formatta la data da YYYYMMDD a formato italiano"""
    try:
        dt = datetime.strptime(date_string, "%Y%m%d")
        giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
        return f"{giorni[dt.weekday()]} {dt.day} {mesi[dt.month - 1]} {dt.year}"
    except:
        return date_string


def main():
    sys.argv.append('20251019')
    if len(sys.argv) < 2:
        print("📖 Uso: python script.py YYYYMMDD")
        print("Esempio: python script.py 20251019")
        return

    data = sys.argv[1]

    print(f"\n{'=' * 70}")
    print(f"ESTRAZIONE LITURGIA DEL GIORNO - {formato_data(data)}")
    print(f"{'=' * 70}\n")

    liturgia = extract_liturgia_giorno(data)

    if liturgia:
        # Salva JSON
        output_file = f"json/liturgia_{data}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(liturgia, f, ensure_ascii=False, indent=2)
        print(f"✅ File salvato: {output_file}")

        # Mostra anteprima
        print(f"\n📄 Sezioni trovate: {len(liturgia['sezioni'])}")
        for sezione in liturgia['sezioni']:
            content_preview = liturgia['sezioni'][sezione][:100].replace('\n', ' ')
            print(f"  • {sezione}: {content_preview}...")

        print(f"\n🔗 URL: {liturgia['url']}")
    else:
        print("❌ Errore nell'estrazione")


if __name__ == "__main__":
    main()