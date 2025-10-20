#!/usr/bin/env python3
"""
Estrattore Lodi Mattutine - APPROCCIO REGEX PULITO
"""
import requests
import re
import json
from datetime import datetime
import sys
import os


def pulisci_testo(text):
    """Rimuove TUTTI i tag HTML, caratteri speciali e spazi extra"""
    if not text:
        return ""

    # Rimuovi tag HTML
    text = re.sub(r'<[^>]+>', '', text)

    # Rimuovi entità HTML
    entities = {
        '&rsquo;': "'", '&lsquo;': "'", '&ldquo;': '"', '&rdquo;': '"',
        '&ndash;': '-', '&mdash;': '—', '&nbsp;': ' ',
        '&eacute;': 'é', '&egrave;': 'è', '&ecirc;': 'ê',
        '&aacute;': 'á', '&agrave;': 'à', '&acirc;': 'â',
        '&iacute;': 'í', '&igrave;': 'ì', '&ocirc;': 'ô',
        '&oacute;': 'ó', '&ograve;': 'ò', '&ouml;': 'ö',
        '&uacute;': 'ú', '&ugrave;': 'ù', '&uuml;': 'ü',
        '&ccedil;': 'ç', '&dagger;': '†', '&laquo;': '«', '&raquo;': '»',
        '&#39;': "'", '&#8212;': '—',
    }
    for old, new in entities.items():
        text = text.replace(old, new)

    # Rimuovi caratteri di controllo e spazi sporchi
    text = text.replace('\u0001', '')  # Carattere di controllo
    text = text.replace('\x00', '')

    # Normalizza spazi
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s*\n\s*', '\n', text)

    return text.strip()


def extract_section(html, start_marker, end_marker):
    """Estrae una sezione tra due marcatori"""
    try:
        start = html.find(start_marker)
        if start == -1:
            return ""
        start += len(start_marker)
        end = html.find(end_marker, start)
        if end == -1:
            end = len(html)
        return html[start:end]
    except:
        return ""


def formato_data(date_string):
    try:
        dt = datetime.strptime(date_string, "%Y%m%d")
        giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
        return f"{giorni[dt.weekday()]} {dt.day} {mesi[dt.month - 1]} {dt.year}"
    except:
        return date_string


def extract_lodi(data_liturgia):
    url = f"https://www.chiesacattolica.it/la-liturgia-delle-ore/?data-liturgia={data_liturgia}&ora=lodi-mattutine"

    try:
        response = requests.get(url, timeout=30)
        response.encoding = 'utf-8'
        html = response.text
    except Exception as e:
        print(f"❌ Errore: {e}")
        return None

    # Estrai sezioni usando regex con DOTALL
    def get_section(pattern):
        match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
        return clean_html_entities(match.group(1)) if match else ""

    lodi = {
        "data": data_liturgia,
        "data_formattata": formato_data(data_liturgia),
        "url": url,
        "introduzione": "",
        "inno": "",
        "salmodia": [],
        "lettura_breve": {"riferimento": "", "testo": ""},
        "responsorio_breve": "",
        "cantico_evangelico": {"antifona_inizio": "", "testo": "", "dossologia": "", "antifona_fine": ""},
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

    # === SALMODIA - Estrai esattamente 3 salmi ===
    # Salmo 1: da "1 ant." a "2 ant."
    salmo1_match = re.search(r'1 ant\.(.*?)(?=2 ant\.)', html, re.DOTALL)
    if salmo1_match:
        s1_text = pulisci_testo(salmo1_match.group(1))
        lodi["salmodia"].append({
            "numero": 1,
            "antifona_inizio": estrai_antifona(s1_text),
            "titolo": estrai_titolo(s1_text),
            "testo": estrai_testo_salmo(s1_text),
            "antifona_fine": ""
        })

    # Salmo 2: da "2 ant." a "3 ant."
    salmo2_match = re.search(r'2 ant\.(.*?)(?=3 ant\.)', html, re.DOTALL)
    if salmo2_match:
        s2_text = pulisci_testo(salmo2_match.group(1))
        lodi["salmodia"].append({
            "numero": 2,
            "antifona_inizio": estrai_antifona(s2_text),
            "titolo": estrai_titolo(s2_text),
            "testo": estrai_testo_salmo(s2_text),
            "antifona_fine": ""
        })

    # Salmo 3: da "3 ant." a "LETTURA BREVE"
    salmo3_match = re.search(r'3 ant\.(.*?)(?=LETTURA BREVE)', html, re.DOTALL)
    if salmo3_match:
        s3_text = pulisci_testo(salmo3_match.group(1))
        lodi["salmodia"].append({
            "numero": 3,
            "antifona_inizio": estrai_antifona(s3_text),
            "titolo": estrai_titolo(s3_text),
            "testo": estrai_testo_salmo(s3_text),
            "antifona_fine": ""
        })

    # === LETTURA BREVE ===
    lettura_match = re.search(r'LETTURA BREVE\s*(.*?)\s*(?=RESPONSORIO BREVE)', html, re.DOTALL)
    if lettura_match:
        lettura_text = pulisci_testo(lettura_match.group(1))
        lines = [l.strip() for l in lettura_text.split('\n') if l.strip()]
        if lines:
            lodi["lettura_breve"]["riferimento"] = lines[0]
            lodi["lettura_breve"]["testo"] = "\n".join(lines[1:])

    # === RESPONSORIO BREVE ===
    resp_match = re.search(r'RESPONSORIO BREVE(.*?)(?=Ant\. al Ben\.|CANTICO DI ZACCARIA)', html, re.DOTALL)
    if resp_match:
        resp_text = pulisci_testo(resp_match.group(1))
        resp_lines = [l.strip() for l in resp_text.split('\n') if l.strip() and l.strip() not in ['R.', 'V.']]
        lodi["responsorio_breve"] = "\n".join(resp_lines)

    # === CANTICO DI ZACCARIA ===
    cant_match = re.search(r'CANTICO DI ZACCARIA(.*?)(?=INVOCAZIONI)', html, re.DOTALL)
    if cant_match:
        cant_text = pulisci_testo(cant_match.group(1))

        # Dividi per "Gloria al Padre"
        gloria_idx = cant_text.find("Gloria al Padre")
        if gloria_idx > 0:
            testo = cant_text[:gloria_idx].strip()
            doss = cant_text[gloria_idx:].strip()

            # Pulisci testo
            testo_lines = [l.strip() for l in testo.split('\n')
                           if l.strip() and l.strip() not in ['Ant. al Ben.', 'Il Messia e il suo Precursore',
                                                              'Lc 1, 68-79']]
            lodi["cantico_evangelico"]["testo"] = "\n".join(testo_lines)
            lodi["cantico_evangelico"]["dossologia"] = doss

    # === INVOCAZIONI ===
    inv_match = re.search(r'INVOCAZIONI(.*?)(?=Padre nostro)', html, re.DOTALL)
    if inv_match:
        inv_text = pulisci_testo(inv_match.group(1))

        # Split per "–"
        parts = inv_text.split('–')
        if parts:
            intro = parts[0].strip()
            lodi["invocazioni"]["introduzione"] = intro

            # Resto sono invocazioni
            for part in parts[1:]:
                inv = part.strip()
                if inv and "ORAZIONE" not in inv:
                    lodi["invocazioni"]["lista"].append(inv)

    # === ORAZIONE ===
    oraz_match = re.search(r'ORAZIONE(.*?)(?=Il Signore ci benedica)', html, re.DOTALL)
    if oraz_match:
        oraz_text = pulisci_testo(oraz_match.group(1))
        lodi["orazione"] = oraz_text.strip()

    # === CONCLUSIONE ===
    conc_match = re.search(r'(Il Signore ci benedica.*?Amen\.)', html, re.DOTALL)
    if conc_match:
        lodi["conclusione"] = pulisci_testo(conc_match.group(1))

    return lodi


def estrai_antifona(text):
    """Estrae la prima antifona (prima di SALMO/CANTICO)"""
    match = re.search(r'^(.*?)(?=SALMO|CANTICO)', text, re.DOTALL)
    if match:
        lines = [l.strip() for l in match.group(1).split('\n') if l.strip()]
        return "\n".join(lines)
    return ""


def estrai_titolo(text):
    """Estrae il titolo (SALMO o CANTICO)"""
    match = re.search(r'(SALMO.*?|CANTICO.*?)(?=\n|$)', text)
    return match.group(1) if match else ""


def estrai_testo_salmo(text):
    """Estrae il testo del salmo (dopo il titolo)"""
    match = re.search(r'(?:SALMO|CANTICO).*?\n(.*)', text, re.DOTALL)
    if match:
        content = match.group(1)
        lines = [l.strip() for l in content.split('\n')
                 if l.strip() and not l.strip().startswith('Gloria') and not l.strip().startswith('Alla fine')]
        return "\n".join(lines)
    return ""


def main():
    sys.argv.append("20251019")
    sys.argv.append("20251020")
    if len(sys.argv) < 2:
        print("Uso: python script.py YYYYMMDD [YYYYMMDD ...]")
        return

    os.makedirs("../json", exist_ok=True)

    for data in sys.argv[1:]:
        print(f"\nESTRAZIONE LODI - {formato_data(data)}")
        print("=" * 60)

        lodi = extract_lodi(data)

        if lodi:
            output_file = f"json/lodi_mattutine_{data}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(lodi, f, ensure_ascii=False, indent=2)

            print(f"✓ Salvato: {output_file}")
            print(f"✓ Salmodia: {len(lodi['salmodia'])} salmi")
            print(f"✓ Lettura breve: {lodi['lettura_breve']['riferimento']}")
            print(f"✓ Invocazioni: {len(lodi['invocazioni']['lista'])} items")
        else:
            print("✗ Errore")


if __name__ == "__main__":
    main()