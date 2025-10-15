#!/usr/bin/env python3
"""
Script per estrarre le Lodi Mattutine dalla Liturgia delle Ore
Versione semplificata e ottimizzata
"""
import requests
from bs4 import BeautifulSoup
import json
import sys
from datetime import datetime, timedelta
import html
import unicodedata
import os
import time


def clean_text(text):
    """Pulisce il testo da caratteri speciali e HTML entities"""
    if not text:
        return ""

    text = html.unescape(text)

    replacements = {
        'â€™': "'", 'â€"': "—", 'â€œ': '"', 'â€': '"',
        'Ã¨': 'è', 'Ã©': 'é', 'Ã¬': 'ì', 'Ã²': 'ò',
        'Ã¹': 'ù', 'Ã ': 'à', 'Ãˆ': 'È', '\u0001': ''
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = unicodedata.normalize('NFC', text)
    text = ''.join(c for c in text if c in '\n\t' or not unicodedata.category(c).startswith('C'))

    return text.strip()


def format_date(date_string):
    """Formatta la data da YYYYMMDD a formato italiano leggibile"""
    try:
        dt = datetime.strptime(date_string, "%Y%m%d")
        giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
        return f"{giorni[dt.weekday()]} {dt.day} {mesi[dt.month - 1]} {dt.year}"
    except:
        return date_string


def extract_section(lines, start_idx, end_markers):
    """Estrae una sezione di testo fino a trovare uno dei marcatori di fine"""
    content = []
    i = start_idx

    while i < len(lines):
        line = lines[i]
        if any(marker in line for marker in end_markers):
            break
        cleaned = clean_text(line)
        if cleaned:
            content.append(cleaned)
        i += 1

    return content, i


def extract_lodi(data_liturgia):
    """Estrae le Lodi Mattutine per la data specificata"""
    url = f"https://www.chiesacattolica.it/la-liturgia-delle-ore/?data-liturgia={data_liturgia}&ora=lodi-mattutine"

    print(f"📡 Recupero dati da: {url}")

    try:
        response = requests.get(url, timeout=30)
        response.encoding = 'utf-8'
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Errore: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
    page_text = soup.get_text(separator="\n")
    lines = [clean_text(line) for line in page_text.split("\n") if clean_text(line)]

    # Struttura dati completa
    lodi = {
        "data": data_liturgia,
        "data_formattata": format_date(data_liturgia),
        "tipo": "Lodi Mattutine",
        "url_fonte": url,
        "introduzione": {"versetto": "", "risposta": "", "dossologia": ""},
        "inno": {"italiano": [], "latino": []},
        "salmodia": [],
        "lettura_breve": {"riferimento": "", "testo": ""},
        "responsorio_breve": [],
        "cantico_evangelico": {
            "nome": "Benedictus",
            "antifona": "",
            "testo": [],
            "dossologia": ""
        },
        "invocazioni": {"introduzione": "", "ritornello": "", "lista": []},
        "orazione": "",
        "conclusione": {"benedizione": "", "risposta": ""}
    }

    i = 0
    current_inno = "italiano"
    in_benedictus = False

    while i < len(lines):
        line = lines[i]

        # Introduzione
        if "O Dio, vieni a salvarmi" in line:
            lodi["introduzione"]["versetto"] = "O Dio, vieni a salvarmi"
            i += 1
            while i < len(lines) and "R." in lines[i]:
                i += 1
            if i < len(lines):
                lodi["introduzione"]["risposta"] = lines[i]
            i += 1
            continue

        # Inno
        if line == "INNO":
            i += 1
            while i < len(lines) and not line.startswith("1 ant"):
                if "Oppure:" in lines[i]:
                    current_inno = "latino"
                    i += 1
                    continue
                if lines[i].startswith("1 ant"):
                    break
                cleaned = clean_text(lines[i])
                if cleaned:
                    lodi["inno"][current_inno].append(cleaned)
                i += 1
            continue

        # Salmodia - Pattern per 1 ant, 2 ant, 3 ant
        if line.endswith("ant.") and line[0].isdigit():
            salmo_num = int(line[0])
            i += 1

            # Antifona
            antifona_lines, i = extract_section(lines, i, ["SALMO", "CANTICO"])

            # Titolo
            titolo = ""
            if i < len(lines) and ("SALMO" in lines[i] or "CANTICO" in lines[i]):
                titolo = lines[i]
                i += 1

            # Sottotitolo e citazione
            sottotitolo = []
            while i < len(lines) and not lines[i].startswith("("):
                sottotitolo.append(lines[i])
                i += 1

            citazione = ""
            if i < len(lines) and lines[i].startswith("("):
                cit_lines = []
                while i < len(lines) and not (lines[i].endswith(")") or lines[i].endswith(").")):
                    cit_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    cit_lines.append(lines[i])
                    i += 1
                citazione = " ".join(cit_lines)

            # Testo del salmo/cantico
            testo = []
            while i < len(lines) and not (lines[i] == f"{salmo_num} ant." or
                                          (salmo_num < 3 and lines[i] == f"{salmo_num + 1} ant.") or
                                          lines[i] == "LETTURA BREVE"):
                cleaned = clean_text(lines[i])
                if cleaned:
                    testo.append(cleaned)
                i += 1

            lodi["salmodia"].append({
                "numero": salmo_num,
                "antifona": " ".join(antifona_lines),
                "titolo": titolo,
                "sottotitolo": " ".join(sottotitolo),
                "citazione": citazione,
                "testo": testo
            })

            # Salta ripetizione antifona
            if i < len(lines) and lines[i] == f"{salmo_num} ant.":
                i += 1
                while i < len(lines) and not (lines[i] == f"{salmo_num + 1} ant." or
                                              lines[i] == "LETTURA BREVE"):
                    i += 1
            continue

        # Lettura Breve
        if line == "LETTURA BREVE":
            i += 1
            if i < len(lines):
                lodi["lettura_breve"]["riferimento"] = lines[i]
                i += 1
            testo_lines, i = extract_section(lines, i, ["RESPONSORIO"])
            lodi["lettura_breve"]["testo"] = "\n".join(testo_lines)
            continue

        # Responsorio Breve
        if line == "RESPONSORIO BREVE":
            i += 1
            resp_lines, i = extract_section(lines, i, ["Ant. al Ben", "CANTICO"])
            lodi["responsorio_breve"] = resp_lines
            continue

        # Cantico di Zaccaria
        if "Ant. al Ben" in line:
            i += 1
            ant_lines = []
            # L'antifona va solo fino a CANTICO DI ZACCARIA
            while i < len(lines) and "CANTICO" not in lines[i]:
                cleaned = clean_text(lines[i])
                if cleaned:
                    ant_lines.append(cleaned)
                i += 1
            lodi["cantico_evangelico"]["antifona"] = "\n".join(ant_lines)
            continue

        if "CANTICO DI ZACCARIA" in line:
            in_benedictus = True
            i += 1

            # Salta riferimento e sottotitolo
            if i < len(lines) and lines[i].startswith("Lc"):
                i += 1
            if i < len(lines) and not lines[i].startswith("Benedetto"):
                i += 1

            benedictus_lines = []
            dossologia_lines = []
            in_dossologia = False

            while i < len(lines):
                # Fine: quando troviamo "Ant. al Ben" ripetuta o INVOCAZIONI
                if "Ant. al Ben" in lines[i] or "INVOCAZIONI" in lines[i]:
                    in_benedictus = False
                    break

                # Inizio dossologia
                if "Gloria al Padre" in lines[i]:
                    in_dossologia = True

                if in_dossologia:
                    dossologia_lines.append(clean_text(lines[i]))
                    if "Amen" in lines[i]:
                        i += 1
                        in_dossologia = False
                        break
                else:
                    cleaned = clean_text(lines[i])
                    if cleaned:
                        benedictus_lines.append(cleaned)

                i += 1

            lodi["cantico_evangelico"]["testo"] = benedictus_lines
            lodi["cantico_evangelico"]["dossologia"] = "\n".join(dossologia_lines)

            # Salta ripetizione antifona
            if i < len(lines) and "Ant. al Ben" in lines[i]:
                i += 1
                while i < len(lines) and "INVOCAZIONI" not in lines[i]:
                    i += 1

            in_benedictus = False
            continue

        # INVOCAZIONI - ma solo se NON siamo nel Benedictus
        if line == "INVOCAZIONI" and not in_benedictus:
            i += 1

            # Introduzione (testo prima del primo ritornello)
            intro_lines = []
            while i < len(lines) and lines[i] != "—" and "Padre nostro" not in lines[i]:
                cleaned = clean_text(lines[i])
                if cleaned:
                    intro_lines.append(cleaned)
                i += 1
            lodi["invocazioni"]["introduzione"] = "\n".join(intro_lines)

            # Primo ritornello (dopo primo "—")
            if i < len(lines) and lines[i] == "—":
                i += 1
                rit_lines = []
                while i < len(lines) and lines[i] != "—" and "Padre nostro" not in lines[i]:
                    cleaned = clean_text(lines[i])
                    if cleaned:
                        rit_lines.append(cleaned)
                    i += 1
                lodi["invocazioni"]["ritornello"] = "\n".join(rit_lines)

            # Lista invocazioni (tutto tra i "—" fino a "Padre nostro")
            invocazioni_lista = []
            current_invocazione = []

            while i < len(lines) and "Padre nostro" not in lines[i]:
                if lines[i] == "—":
                    # Salva l'invocazione precedente se presente
                    if current_invocazione:
                        invocazioni_lista.append("\n".join(current_invocazione))
                        current_invocazione = []
                    i += 1
                else:
                    cleaned = clean_text(lines[i])
                    if cleaned:
                        current_invocazione.append(cleaned)
                    i += 1

            # Aggiungi l'ultima invocazione
            if current_invocazione:
                invocazioni_lista.append("\n".join(current_invocazione))

            lodi["invocazioni"]["lista"] = invocazioni_lista

            # Salta "Padre nostro"
            if i < len(lines) and "Padre nostro" in lines[i]:
                i += 1
            continue

        # Orazione
        if line == "ORAZIONE":
            i += 1
            or_lines = []
            # Raccogli tutto tra ORAZIONE e "R. Amen."
            while i < len(lines):
                # Controlla se abbiamo raggiunto "R. Amen." o varianti
                if lines[i].strip() == "R." and i + 1 < len(lines) and "Amen" in lines[i + 1]:
                    break
                if "R. Amen" in lines[i] or lines[i].strip() == "Amen.":
                    break
                if "Il Signore ci benedica" in lines[i]:
                    break

                cleaned = clean_text(lines[i])
                if cleaned:
                    or_lines.append(cleaned)
                i += 1

            lodi["orazione"] = " ".join(or_lines)
            continue

        # Conclusione
        if "Il Signore ci benedica" in line:
            lodi["conclusione"]["benedizione"] = line
            i += 1
            while i < len(lines) and "R." in lines[i]:
                i += 1
            if i < len(lines):
                lodi["conclusione"]["risposta"] = lines[i]
            break

        i += 1

    return lodi


def main():
    """Funzione principale"""
    sys.argv.append('20251001')
    sys.argv.append('20251031')

    if len(sys.argv) < 2:
        print("📖 Uso:")
        print("  python lodi_extractor.py YYYYMMDD")
        print("  python lodi_extractor.py YYYYMMDD YYYYMMDD  (range)")
        print("\n💡 Esempio:")
        print("  python lodi_extractor.py 20251015")
        print("  python lodi_extractor.py 20251015 20251031")
        return

    data_inizio = sys.argv[1]

    # Singola data
    if len(sys.argv) == 2:
        print(f"\n{'=' * 60}")
        print(f"ESTRAZIONE LODI MATTUTINE - {format_date(data_inizio)}")
        print(f"{'=' * 60}\n")

        lodi = extract_lodi(data_inizio)

        if lodi:
            output_file = f"lodi_{data_inizio}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(lodi, f, ensure_ascii=False, indent=2)

            size = os.path.getsize(output_file) / 1024
            print(f"\n✅ File creato: {output_file} ({size:.2f} KB)")
        else:
            print("\n❌ Errore nell'estrazione")

    # Range di date
    elif len(sys.argv) == 3:
        data_fine = sys.argv[2]

        try:
            dt_inizio = datetime.strptime(data_inizio, "%Y%m%d")
            dt_fine = datetime.strptime(data_fine, "%Y%m%d")
        except ValueError:
            print("❌ Formato data non valido. Usa YYYYMMDD")
            return

        if dt_inizio > dt_fine:
            print("❌ La data di inizio deve essere precedente alla data di fine")
            return

        num_giorni = (dt_fine - dt_inizio).days + 1
        output_dir = "lodi_json"
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n{'=' * 60}")
        print(f"ESTRAZIONE RANGE: {format_date(data_inizio)} → {format_date(data_fine)}")
        print(f"Giorni: {num_giorni} | Directory: {output_dir}/")
        print(f"{'=' * 60}\n")

        successi = 0
        current_date = dt_inizio

        for i in range(num_giorni):
            data_str = current_date.strftime("%Y%m%d")
            print(f"[{i + 1}/{num_giorni}] {format_date(data_str)}...", end=" ")

            lodi = extract_lodi(data_str)

            if lodi:
                output_file = os.path.join(output_dir, f"lodi_{data_str}.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(lodi, f, ensure_ascii=False, indent=2)
                size = os.path.getsize(output_file) / 1024
                print(f"✅ OK ({size:.2f} KB)")
                successi += 1
            else:
                print("❌ ERRORE")

            current_date += timedelta(days=1)

            if i < num_giorni - 1:
                time.sleep(0.5)

        print(f"\n{'=' * 60}")
        print(f"✅ Completato: {successi}/{num_giorni} estrazioni riuscite")
        print(f"📁 Files salvati in: {output_dir}/")
        print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()