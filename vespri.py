#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Estrattore Vespri - Liturgia delle Ore
Versione corretta con righe iniziali nei salmi
"""
import requests
import re
import json
from datetime import datetime
import sys
import os


def formato_data(date_string):
    """Formatta data da YYYYMMDD a italiano"""
    try:
        dt = datetime.strptime(date_string, "%Y%m%d")
        giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
        return f"{giorni[dt.weekday()]} {dt.day} {mesi[dt.month - 1]} {dt.year}"
    except:
        return date_string


def pulisci_testo(text):
    """Rimuove tag HTML e entità, preservando newline"""
    if not text:
        return ""

    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)

    entities = {
        '&rsquo;': "'", '&lsquo;': "'", '&ldash;': '-', '&ndash;': '-',
        '&mdash;': '—', '&nbsp;': ' ', '&eacute;': 'é', '&egrave;': 'è',
        '&ecirc;': 'ê', '&aacute;': 'á', '&agrave;': 'à', '&acirc;': 'â',
        '&iacute;': 'í', '&igrave;': 'ì', '&ocirc;': 'ô', '&oacute;': 'ó',
        '&ograve;': 'ò', '&ouml;': 'ö', '&uacute;': 'ú', '&ugrave;': 'ù',
        '&uuml;': 'ü', '&ccedil;': 'ç', '&dagger;': '†', '&laquo;': '«',
        '&raquo;': '»', '&#39;': "'", '&#8212;': '—', '&ldquo;': '"', '&rdquo;': '"',
    }

    for old, new in entities.items():
        text = text.replace(old, new)

    text = text.replace('\u0001', '').replace('\x00', '')

    lines = text.split('\n')
    lines = [re.sub(r'\s+', ' ', line).strip() for line in lines]
    lines = [line for line in lines if line]

    return '\n'.join(lines)


def estrai_antifona(text):
    """Estrae prima antifona (prima di SALMO/CANTICO)"""
    lines = text.split('\n')
    antifona = []

    for line in lines:
        if line.startswith('SALMO') or line.startswith('CANTICO'):
            break
        antifona.append(line.strip())

    return '\n'.join([l for l in antifona if l])


def estrai_titolo(text):
    """Estrae titolo (prima riga SALMO/CANTICO)"""
    lines = text.split('\n')

    for line in lines:
        if line.startswith('SALMO') or line.startswith('CANTICO'):
            return line.strip()

    return ""


def estrai_testo_salmo(text):
    """Estrae testo salmo (dopo SALMO/CANTICO) - inizia dopo il secondo newline"""
    lines = text.split('\n')

    start_idx = -1
    for i, line in enumerate(lines):
        if line.startswith('SALMO') or line.startswith('CANTICO'):
            start_idx = i + 1
            break

    if start_idx == -1:
        return ""

    # Mantieni la prima riga (numero/titolo salmo)
    first_line = lines[start_idx].strip() if start_idx < len(lines) else ""

    # Salta la seconda riga (sottotitolo/descrizione)
    # E inizia da quella dopo (terza riga)
    text_start_idx = start_idx + 2

    # Raccogli le righe dal testo vero e proprio
    testo = [first_line] if first_line else []

    for i in range(text_start_idx, len(lines)):
        line = lines[i].strip()

        if ' ant.' in line or line.startswith('Gloria'):
            break

        if line and not line.startswith('Alla fine'):
            testo.append(line)

    return '\n'.join(testo)


def estrai_vespri(data_liturgia):
    """Estrae tutti i Vespri"""
    url = f"https://www.chiesacattolica.it/la-liturgia-delle-ore/?data-liturgia={data_liturgia}&ora=vespri"

    try:
        response = requests.get(url, timeout=30)
        response.encoding = 'utf-8'
        html = response.text
    except Exception as e:
        print(f"Errore fetch: {e}")
        return None

    vespri = {
        "data": data_liturgia,
        "data_formattata": formato_data(data_liturgia),
        "url": url,
        "introduzione": "",
        "inno": "",
        "salmodia": [],
        "lettura_breve": {"riferimento": "", "testo": ""},
        "responsorio_breve": "",
        "cantico_evangelico": {
            "riferimento": "",
            "sottotitolo": "",
            "testo": "",
            "dossologia": ""
        },
        "invocazioni": {"introduzione": "", "lista": []},
        "orazione": "",
        "conclusione": ""
    }

    # === INTRODUZIONE ===
    intro_match = re.search(r'V\..*?(?=INNO)', html, re.DOTALL)
    if intro_match:
        vespri["introduzione"] = pulisci_testo(intro_match.group(0))

    # === INNO ===
    inno_match = re.search(r'INNO(.*?)(?=1 ant\.)', html, re.DOTALL)
    if inno_match:
        vespri["inno"] = pulisci_testo(inno_match.group(1))

    # === SALMODIA (3 salmi) ===
    for num in range(1, 4):
        next_marker = f"{num + 1} ant." if num < 3 else "LETTURA BREVE"
        salmo_match = re.search(rf'{num} ant\.(.*?)(?={next_marker})', html, re.DOTALL)
        if salmo_match:
            s_text = pulisci_testo(salmo_match.group(1))
            vespri["salmodia"].append({
                "numero": num,
                "antifona_inizio": estrai_antifona(s_text),
                "titolo": estrai_titolo(s_text),
                "testo": estrai_testo_salmo(s_text)
            })

    # === LETTURA BREVE ===
    lettura_match = re.search(r'LETTURA BREVE\s*(.*?)\s*(?=RESPONSORIO BREVE)', html, re.DOTALL)
    if lettura_match:
        lettura = pulisci_testo(lettura_match.group(1))
        lines = lettura.split('\n')
        if lines:
            vespri["lettura_breve"]["riferimento"] = lines[0]
            vespri["lettura_breve"]["testo"] = '\n'.join(lines[1:])

    # === RESPONSORIO BREVE ===
    resp_match = re.search(r'RESPONSORIO BREVE(.*?)(?=Ant\. al Magn\.)', html, re.DOTALL)
    if resp_match:
        resp = pulisci_testo(resp_match.group(1))
        lines = [l for l in resp.split('\n') if l.strip() and l.strip() not in ['R.', 'V.']]
        vespri["responsorio_breve"] = '\n'.join(lines)

    # === CANTICO DELLA BEATA VERGINE (Magnificat) ===
    cant_match = re.search(r'CANTICO DELLA BEATA VERGINE(.*?)(?=INTERCESSIONI)', html, re.DOTALL)
    if cant_match:
        cant = pulisci_testo(cant_match.group(1))

        gloria_idx = cant.find("Gloria al Padre")
        if gloria_idx > 0:
            testo = cant[:gloria_idx].strip()
            doss = cant[gloria_idx:].strip()

            lines = [l for l in testo.split('\n')
                     if l and l not in ['Ant. al Magn.', "L'anima mia magnifica il Signore"]]
            vespri["cantico_evangelico"]["testo"] = '\n'.join(lines)
            vespri["cantico_evangelico"]["dossologia"] = doss

    # === INTERCESSIONI ===
    inv_match = re.search(r'INTERCESSIONI(.*?)(?=Padre nostro)', html, re.DOTALL)
    if inv_match:
        inv = pulisci_testo(inv_match.group(1))

        lines = [l.strip() for l in inv.split('\n') if l.strip()]

        if lines:
            intro_end = 0
            for i, line in enumerate(lines):
                if line.endswith(':'):
                    intro_end = i
                    break

            if intro_end > 0:
                vespri["invocazioni"]["introduzione"] = '\n'.join(lines[:intro_end + 1])
                lines = lines[intro_end + 1:]

            invocazioni = []
            for line in lines:
                if ' – ' in line or ' - ' in line:
                    parts = re.split(r'\s+[–-]\s+', line)
                    if len(parts) == 2:
                        invocazioni.append({
                            "titolo": parts[0].strip(),
                            "risposta": parts[1].strip()
                        })
                else:
                    if line:
                        invocazioni.append({
                            "titolo": line,
                            "risposta": ""
                        })

            vespri["invocazioni"]["lista"] = invocazioni

    # === ORAZIONE ===
    oraz_match = re.search(r'ORAZIONE(.*?)(?=Il Signore ci benedica)', html, re.DOTALL)
    if oraz_match:
        vespri["orazione"] = pulisci_testo(oraz_match.group(1)).strip()

    # === CONCLUSIONE ===
    conc_match = re.search(r'(Il Signore ci benedica.*?Amen\.)', html, re.DOTALL)
    if conc_match:
        vespri["conclusione"] = pulisci_testo(conc_match.group(1))

    return vespri


def main():
    if len(sys.argv) < 2:
        print("Uso: python vespri.py YYYYMMDD [YYYYMMDD ...]")
        return

    os.makedirs("json", exist_ok=True)

    for data in sys.argv[1:]:
        print(f"\nESTRAZIONE: {formato_data(data)}")
        print("-" * 60)

        vespri = estrai_vespri(data)

        if vespri:
            output_file = f"json/vespri_{data}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(vespri, f, ensure_ascii=False, indent=2)

            print(f"Salvato: {output_file}")
            print(f"Salmodia: {len(vespri['salmodia'])} salmi")
            print(f"Lettura breve: {vespri['lettura_breve']['riferimento']}")
            print(f"Magnificat: {vespri['cantico_evangelico']['sottotitolo']}")
        else:
            print("Errore nell'estrazione")


if __name__ == "__main__":
    main()