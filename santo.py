#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Estrattore del Santo del Giorno
Legge da https://www.chiesacattolica.it/santo-del-giorno/
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


def is_garbage_text(text):
    """Verifica se il testo è spazzatura (pulsanti social, link, ecc)"""
    garbage_keywords = [
        'condividi', 'invia', 'stampa', 'facebook', 'twitter', 'whatsapp',
        'telegram', 'linkedin', 'pinterest', 'reddit', 'condividere',
        'stampa pagina', 'scarica', 'download', 'leggi anche', 'vedi anche',
        'clicca qui', 'continua a leggere', 'approfondisci', 'per saperne',
        'newsletter', 'iscriviti', 'seguici', 'social media', 'share',
        'email', 'scritto da', 'autore:', 'fonte:', 'articolo correlato'
    ]

    text_lower = text.lower().strip()

    # Se il testo è troppo breve, probabilmente è spam
    if len(text_lower) < 10:
        return True

    # Se contiene parole chiave di spazzatura
    for keyword in garbage_keywords:
        if keyword in text_lower:
            return True

    # Se sembra un pulsante/link
    if text_lower.startswith('http') or text_lower.startswith('www'):
        return True

    return False


def extract_santo_giorno(data_liturgia):
    """Estrae tutti i dettagli dal Santo del Giorno"""
    url = f"https://www.chiesacattolica.it/santo-del-giorno/?data-liturgia={data_liturgia}"

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

    # Estrai titolo della pagina per il santo principale
    title_tag = soup.find('title')
    title_text = title_tag.get_text() if title_tag else ""

    santo_principale = ""
    if " - Chiesacattolica.it" in title_text:
        parts = title_text.replace(" - Chiesacattolica.it", "").split(" ", 4)
        if len(parts) >= 5:
            santo_principale = " ".join(parts[4:]).strip()

    # Estrai il contenuto principale
    page_text = soup.get_text(separator="\n")
    lines = [clean_text(line) for line in page_text.split("\n") if clean_text(line)]

    # Rimuovi linee di navigazione e metadata
    content_lines = []
    start_extracting = False

    for line in lines:
        # Salta i primi elementi di navigazione
        if "Santo del giorno" in line:
            start_extracting = True
            continue

        if start_extracting and line and not line.startswith("http"):
            # Escludere testi spazzatura
            if not is_garbage_text(line):
                content_lines.append(line)

    # Dividi per santi individuali (ogni santo inizia con una posizione geografica)
    santi = []
    current_santo = ""

    for line in content_lines:
        # Se la linea inizia con "A ", "Ad ", "Presso ", "Nel ", "Nella " etc - è un nuovo santo
        if re.match(r'^(A|Ad|Presso|Nel|Nella|Nell|Nell\'|Vicino|Nel|Nella)\s+', line):
            if current_santo and not is_garbage_text(current_santo):
                santi.append(current_santo.strip())
            current_santo = line
        else:
            if current_santo:
                current_santo += " " + line

    # Aggiungi l'ultimo santo
    if current_santo and not is_garbage_text(current_santo):
        santi.append(current_santo.strip())

    # Filtra santi che sono troppo corti o spam
    santi_filtrati = []
    for santo in santi:
        if len(santo) > 20 and not is_garbage_text(santo):
            santi_filtrati.append(santo)

    # Struttura dati
    santo = {
        "data": data_liturgia,
        "data_formattata": formato_data(data_liturgia),
        "url": url,
        "santo_principale": santo_principale,
        "santi_commemorati": santi_filtrati,
        "numero_santi": len(santi_filtrati),
        "testo_completo": " ".join(content_lines[:500])  # Primi 500 elementi
    }

    return santo


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
    sys.argv.append('20251020')

    if len(sys.argv) < 2:
        print("📖 Uso: python santo.py YYYYMMDD [YYYYMMDD ...]")
        print("Esempi:")
        print("  python santo.py 20251020")
        print("  python santo.py 20251020 20251021 20251022")
        return

    # Crea directory se non esiste
    os.makedirs("json", exist_ok=True)

    date_args = sys.argv[1:]

    for data in date_args:
        print(f"\n{'=' * 80}")
        print(f"ESTRAZIONE SANTO DEL GIORNO - {formato_data(data)}")
        print(f"{'=' * 80}\n")

        santo = extract_santo_giorno(data)

        if santo:
            # Salva JSON
            output_file = f"json/santo_{data}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(santo, f, ensure_ascii=False, indent=2)
            print(f"✅ File salvato: {output_file}\n")

            # Mostra informazioni estratte
            if santo["santo_principale"]:
                print(f"🎉 SANTO PRINCIPALE: {santo['santo_principale']}\n")

            print(f"📌 SANTI COMMEMORATI: {santo['numero_santi']}\n")

            for i, s in enumerate(santo["santi_commemorati"][:5], 1):
                preview = s[:120] + "..." if len(s) > 120 else s
                print(f"  {i}. {preview}\n")

            if santo['numero_santi'] > 5:
                print(f"  ... e altri {santo['numero_santi'] - 5} santi\n")

            print(f"{'=' * 80}")
            print(f"🔗 URL: {santo['url']}\n")
        else:
            print("❌ Errore nell'estrazione")


if __name__ == "__main__":
    main()