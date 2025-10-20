#!/usr/bin/env python3
"""
Estrattore Lodi Mattutine - Script Pulito e Organizzato
"""
import requests
import re
import json
from datetime import datetime
import sys
import os


# ============================================================================
# UTILITÀ
# ============================================================================

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

    # Convrti <br> in newline
    text = re.sub(r'<br\s*/?>', '\n', text)

    # Rimuovi altri tag HTML
    text = re.sub(r'<[^>]+>', '', text)

    # Mappa entità HTML
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

    # Rimuovi caratteri di controllo
    text = text.replace('\u0001', '').replace('\x00', '')

    # Normalizza spazi ma preserva newline
    lines = text.split('\n')
    lines = [re.sub(r'\s+', ' ', line).strip() for line in lines]
    lines = [line for line in lines if line]

    return '\n'.join(lines)


# ============================================================================
# ESTRAZIONE SALMODIA
# ============================================================================

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
    """Estrae testo salmo (dopo SALMO/CANTICO)"""
    lines = text.split('\n')

    # Trova inizio dopo titolo
    start_idx = -1
    for i, line in enumerate(lines):
        if line.startswith('SALMO') or line.startswith('CANTICO'):
            start_idx = i + 1
            break

    if start_idx == -1:
        return ""

    # Raccogli testo fino a antifona finale o Gloria
    testo = []
    for i in range(start_idx, len(lines)):
        line = lines[i].strip()

        if ' ant.' in line or line.startswith('Gloria'):
            break

        if line and not line.startswith('Alla fine'):
            testo.append(line)

    return '\n'.join(testo)


# ============================================================================
# ESTRAZIONE PRINCIPALI
# ============================================================================

def estrai_lodi(data_liturgia):
    """Estrae tutte le Lodi Mattutine"""
    url = f"https://www.chiesacattolica.it/la-liturgia-delle-ore/?data-liturgia={data_liturgia}&ora=lodi-mattutine"

    try:
        response = requests.get(url, timeout=30)
        response.encoding = 'utf-8'
        html = response.text
    except Exception as e:
        print(f"Errore fetch: {e}")
        return None

    # Struttura dati
    lodi = {
        "data": data_liturgia,
        "data_formattata": formato_data(data_liturgia),
        "url": url,
        "introduzione": "",
        "inno": "",
        "salmodia": [],
        "lettura_breve": {"riferimento": "", "testo": ""},
        "responsorio_breve": "",
        "cantico_evangelico": {"testo": "", "dossologia": ""},
        "invocazioni": {"introduzione": "", "lista": []},
        "orazione": "",
        "conclusione": ""
    }

    # === INTRODUZIONE ===
    intro_match = re.search(r'V\..*?(?=INNO)', html, re.DOTALL)
    if intro_match:
        lodi["introduzione"] = pulisci_testo(intro_match.group(0))

    # === INNO ===
    inno_match = re.search(r'INNO(.*?)(?=1 ant\.)', html, re.DOTALL)
    if inno_match:
        lodi["inno"] = pulisci_testo(inno_match.group(1))

    # === SALMODIA (3 salmi) ===
    salmo1_match = re.search(r'1 ant\.(.*?)(?=2 ant\.)', html, re.DOTALL)
    if salmo1_match:
        s1 = pulisci_testo(salmo1_match.group(1))
        lodi["salmodia"].append({
            "numero": 1,
            "antifona_inizio": estrai_antifona(s1),
            "titolo": estrai_titolo(s1),
            "testo": estrai_testo_salmo(s1)
        })

    salmo2_match = re.search(r'2 ant\.(.*?)(?=3 ant\.)', html, re.DOTALL)
    if salmo2_match:
        s2 = pulisci_testo(salmo2_match.group(1))
        lodi["salmodia"].append({
            "numero": 2,
            "antifona_inizio": estrai_antifona(s2),
            "titolo": estrai_titolo(s2),
            "testo": estrai_testo_salmo(s2)
        })

    salmo3_match = re.search(r'3 ant\.(.*?)(?=LETTURA BREVE)', html, re.DOTALL)
    if salmo3_match:
        s3 = pulisci_testo(salmo3_match.group(1))
        lodi["salmodia"].append({
            "numero": 3,
            "antifona_inizio": estrai_antifona(s3),
            "titolo": estrai_titolo(s3),
            "testo": estrai_testo_salmo(s3)
        })

    # === LETTURA BREVE ===
    lettura_match = re.search(r'LETTURA BREVE\s*(.*?)\s*(?=RESPONSORIO BREVE)', html, re.DOTALL)
    if lettura_match:
        lettura = pulisci_testo(lettura_match.group(1))
        lines = lettura.split('\n')
        if lines:
            lodi["lettura_breve"]["riferimento"] = lines[0]
            lodi["lettura_breve"]["testo"] = '\n'.join(lines[1:])

    # === RESPONSORIO BREVE ===
    resp_match = re.search(r'RESPONSORIO BREVE(.*?)(?=Ant\. al Ben\.|CANTICO DI ZACCARIA)', html, re.DOTALL)
    if resp_match:
        resp = pulisci_testo(resp_match.group(1))
        lines = [l for l in resp.split('\n') if l.strip() and l.strip() not in ['R.', 'V.']]
        lodi["responsorio_breve"] = '\n'.join(lines)

    # === CANTICO DI ZACCARIA ===
    cant_match = re.search(r'CANTICO DI ZACCARIA(.*?)(?=INVOCAZIONI)', html, re.DOTALL)
    if cant_match:
        cant = pulisci_testo(cant_match.group(1))

        gloria_idx = cant.find("Gloria al Padre")
        if gloria_idx > 0:
            testo = cant[:gloria_idx].strip()
            doss = cant[gloria_idx:].strip()

            lines = [l for l in testo.split('\n')
                     if l and l not in ['Ant. al Ben.', 'Il Messia e il suo Precursore', 'Lc 1, 68-79']]
            lodi["cantico_evangelico"]["testo"] = '\n'.join(lines)
            lodi["cantico_evangelico"]["dossologia"] = doss

    # === INVOCAZIONI ===
    inv_match = re.search(r'INVOCAZIONI(.*?)(?=Padre nostro)', html, re.DOTALL)
    if inv_match:
        inv = pulisci_testo(inv_match.group(1))

        # Dividi il testo in linee
        lines = [l.strip() for l in inv.split('\n') if l.strip()]

        if not lines:
            return lodi

        # Cerca il ritornello finale dell'introduzione
        # Può essere "Signore, tu sei la vita e la salvezza nostra."
        # o "Donaci il tuo Spirito, Signore."
        ritornello_idx = -1

        for i, line in enumerate(lines):
            if ("Signore, tu sei la vita e la salvezza nostra" in line or
                    "Donaci il tuo Spirito, Signore" in line):
                ritornello_idx = i
                break

        # Se trovato, introduzione è da 0 a ritornello_idx (incluso)
        if ritornello_idx >= 0:
            intro_lines = lines[:ritornello_idx + 1]
            invocazioni_lines = lines[ritornello_idx + 1:]
        else:
            # Se non trova ritornello, prendi le prime righe come intro
            intro_lines = lines
            invocazioni_lines = []

        # Introduzione
        lodi["invocazioni"]["introduzione"] = '\n'.join(intro_lines)

        # Dividi le invocazioni per ".\n" (punto e newline)
        inv_text = '\n'.join(invocazioni_lines)
        if inv_text.strip():
            parts = re.split(r'\.\s*\n', inv_text)

            for part in parts:
                p = part.strip()
                if p and "ORAZIONE" not in p:
                    # Dividi titolo (prima di "-") e testo (dopo "-")
                    if '\n-\n' in p:
                        titolo, testo = p.split('\n-\n', 1)
                        lodi["invocazioni"]["lista"].append({
                            "titolo": titolo.strip(),
                            "testo": testo.strip()
                        })
                    elif '-' in p:
                        titolo, testo = p.split('-', 1)
                        lodi["invocazioni"]["lista"].append({
                            "titolo": titolo.strip(),
                            "testo": testo.strip()
                        })

    # === ORAZIONE ===
    oraz_match = re.search(r'ORAZIONE(.*?)(?=Il Signore ci benedica)', html, re.DOTALL)
    if oraz_match:
        lodi["orazione"] = pulisci_testo(oraz_match.group(1)).strip()

    # === CONCLUSIONE ===
    conc_match = re.search(r'(Il Signore ci benedica.*?Amen\.)', html, re.DOTALL)
    if conc_match:
        lodi["conclusione"] = pulisci_testo(conc_match.group(1))

    return lodi


# ============================================================================
# MAIN
# ============================================================================

def main():
    sys.argv.append("20251019")
    sys.argv.append("20251020")
    if len(sys.argv) < 2:
        print("Uso: python script.py YYYYMMDD [YYYYMMDD ...]")
        return

    os.makedirs("json", exist_ok=True)

    for data in sys.argv[1:]:
        print(f"\nESTRAZIONE: {formato_data(data)}")
        print("-" * 60)

        lodi = estrai_lodi(data)

        if lodi:
            output_file = f"json/lodi_mattutine_{data}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(lodi, f, ensure_ascii=False, indent=2)

            print(f"Salvato: {output_file}")
            print(f"Salmodia: {len(lodi['salmodia'])} salmi")
            print(f"Lettura breve: {lodi['lettura_breve']['riferimento']}")
            print(f"Invocazioni: {len(lodi['invocazioni']['lista'])} items")
        else:
            print("Errore nell'estrazione")


if __name__ == "__main__":
    main()