#!/usr/bin/env python3
"""
Estrattore Lodi Mattutine dalla Liturgia delle Ore
Versione corretta con fix encoding e sintassi
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
import re
import sqlite3

def clean_text(text):
    """Pulisce il testo da caratteri speciali e HTML entities"""
    if not text:
        return ""

    text = html.unescape(text)

    replacements = {
        'â€™': "'", 'â€"': "—", 'â€œ': '"', 'â€': '"',
        'Ã¨': 'è', 'Ã©': 'é', 'Ã¬': 'ì', 'Ã²': 'ò',
        'Ã¹': 'ù', 'Ã ': 'à', 'Ãˆ': 'È', '\u0001': '',
        'PoichÃ©': 'Poiché', 'piÃ¹': 'più', 'CosÃ¬': 'Così',
        'finchÃ©': 'finché', 'benedirÃ²': 'benedirò',
        'loderÃ ': 'loderà', 'sazierÃ²': 'sazierò'
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = unicodedata.normalize('NFC', text)
    text = ''.join(c for c in text if c in '\n\t' or not unicodedata.category(c).startswith('C'))

    return text.strip()

def init_database(db_path="lodi.db"):
    """Inizializza il database SQLite con le tabelle necessarie"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Tabella principale Lodi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lodi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT UNIQUE NOT NULL,
            data_formattata TEXT,
            url_fonte TEXT,
            celebrazione_santo TEXT,
            celebrazione_tipo TEXT,

            intro_versetto TEXT,
            intro_risposta TEXT,
            intro_dossologia TEXT,

            inno_italiano TEXT,
            inno_latino TEXT,

            lettura_breve_rif TEXT,
            lettura_breve_testo TEXT,

            responsorio_breve TEXT,

            cantico_antifona TEXT,
            cantico_testo TEXT,
            cantico_dossologia TEXT,

            invocazioni_intro TEXT,
            invocazioni_ritornello TEXT,

            orazione TEXT,

            conclusione_benedizione TEXT,
            conclusione_risposta TEXT,

            json_completo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabella Salmodia
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salmodia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lodi_data TEXT NOT NULL,
            numero INTEGER,
            antifona TEXT,
            titolo TEXT,
            sottotitolo TEXT,
            citazione TEXT,
            testo TEXT,
            dossologia TEXT,
            FOREIGN KEY (lodi_data) REFERENCES lodi(data)
        )
    ''')

    # Tabella Invocazioni - FIX: rimossa virgola dopo testo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invocazioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lodi_data TEXT NOT NULL,
            ordine INTEGER,
            testo TEXT,
            FOREIGN KEY (lodi_data) REFERENCES lodi(data)
        )
    ''')

    # Indici per performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_lodi_data ON lodi(data)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_salmodia_data ON salmodia(lodi_data)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_invocazioni_data ON invocazioni(lodi_data)')

    conn.commit()
    conn.close()
    print(f"✅ Database inizializzato: {db_path}")

def save_to_database(lodi, db_path="lodi.db"):
    """Salva i dati delle Lodi nel database SQLite"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Salva dati principali
        cursor.execute('''
            INSERT OR REPLACE INTO lodi (
                data, data_formattata, url_fonte,
                celebrazione_santo, celebrazione_tipo,
                intro_versetto, intro_risposta, intro_dossologia,
                inno_italiano, inno_latino,
                lettura_breve_rif, lettura_breve_testo,
                responsorio_breve,
                cantico_antifona, cantico_testo, cantico_dossologia,
                invocazioni_intro, invocazioni_ritornello,
                orazione,
                conclusione_benedizione, conclusione_risposta,
                json_completo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lodi["data"],
            lodi["data_formattata"],
            lodi["url_fonte"],
            lodi["celebrazione"]["santo"],
            lodi["celebrazione"]["tipo"],
            lodi["introduzione"]["versetto"],
            lodi["introduzione"]["risposta"],
            lodi["introduzione"]["dossologia"],
            json.dumps(lodi["inno"]["italiano"], ensure_ascii=False),
            json.dumps(lodi["inno"]["latino"], ensure_ascii=False),
            lodi["lettura_breve"]["riferimento"],
            lodi["lettura_breve"]["testo"],
            json.dumps(lodi["responsorio_breve"], ensure_ascii=False),
            lodi["cantico_evangelico"]["antifona"],
            json.dumps(lodi["cantico_evangelico"]["testo"], ensure_ascii=False),
            lodi["cantico_evangelico"]["dossologia"],
            lodi["invocazioni"]["introduzione"],
            lodi["invocazioni"]["ritornello"],
            lodi["orazione"],
            lodi["conclusione"]["benedizione"],
            lodi["conclusione"]["risposta"],
            json.dumps(lodi, ensure_ascii=False)
        ))

        # Elimina vecchie salmodie per questa data
        cursor.execute('DELETE FROM salmodia WHERE lodi_data = ?', (lodi["data"],))

        # Salva salmodia
        for salmo in lodi["salmodia"]:
            try:
                cursor.execute('''
                    INSERT INTO salmodia (
                        lodi_data, numero, antifona, titolo, sottotitolo, citazione, testo, dossologia
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    lodi["data"],
                    salmo["numero"],
                    salmo["antifona"],
                    salmo["titolo"],
                    salmo["sottotitolo"],
                    salmo["citazione"],
                    json.dumps(salmo["testo"], ensure_ascii=False),
                    salmo.get("dossologia", "")  # Usa .get() per evitare KeyError
                ))
            except Exception as e:
                print(f"\n⚠️ Errore salvataggio salmo {salmo['numero']}: {e}")
                print(f"Chiavi disponibili: {salmo.keys()}")

        # Elimina vecchie invocazioni per questa data
        cursor.execute('DELETE FROM invocazioni WHERE lodi_data = ?', (lodi["data"],))

        # Salva invocazioni
        for idx, invocazione in enumerate(lodi["invocazioni"]["lista"], 1):
            cursor.execute('''
                INSERT INTO invocazioni (lodi_data, ordine, testo)
                VALUES (?, ?, ?)
            ''', (lodi["data"], idx, invocazione))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"\n❌ Errore salvataggio DB: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def format_date(date_string):
    """Formatta la data da YYYYMMDD a formato italiano"""
    try:
        dt = datetime.strptime(date_string, "%Y%m%d")
        giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
        return f"{giorni[dt.weekday()]} {dt.day} {mesi[dt.month - 1]} {dt.year}"
    except:
        return date_string

def extract_celebrazione(orazione_text, invocazioni_text, antifone_text=""):
    """Estrae la celebrazione dal testo SOLO se non è stata trovata nel titolo"""
    combined_text = orazione_text + " " + invocazioni_text + " " + antifone_text

    # Lista di parole da ESCLUDERE - non sono nomi di santi
    esclusioni_comuni = [
        'Padre', 'Spirito', 'Chiesa', 'Maria Vergine', 'Giuseppe', 'Angeli',
        'Trinità', 'Croce', 'Cuore', 'Corpo', 'Sangue', 'Sacramento',
        'Eucaristia', 'Messa', 'Dono', 'Grazia', 'Carità', 'Unità',
        'Famiglia', 'Comunità', 'Fede', 'Speranza', 'Volontà', 'Parola',
        'Scrittura', 'Vangelo', 'Popolo', 'Vita', 'Morte', 'Pace',
        'Giustizia', 'Misericordia', 'Provvidenza', 'Sapienza'
    ]

    # FIX: rimosso pattern duplicato per "beato"
    patterns = [
        r'sant[ao]\s+([A-ZÀ-Ù][a-zà-ù]+(?:\s+[A-ZÀ-Ù][a-zà-ù]+){0,3})',
        r'beat[ao]\s+([A-ZÀ-Ù][a-zà-ù]+(?:\s+[A-ZÀ-Ù][a-zà-ù]+){0,3})'
    ]

    candidati = []
    for pattern in patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            santo_clean = match.strip()

            # Verifica che non sia nelle esclusioni
            is_valid = True
            for esclusione in esclusioni_comuni:
                if esclusione.lower() in santo_clean.lower():
                    is_valid = False
                    break

            # Verifica che non contenga parole chiave di celebrazioni non-santi
            parole_celebrazioni = ['resurrezione', 'pasqua', 'natale', 'pentecoste',
                                   'ascensione', 'annunciazione', 'presentazione']
            for parola in parole_celebrazioni:
                if parola in santo_clean.lower():
                    is_valid = False
                    break

            # Verifica che sia un nome proprio (almeno una maiuscola dopo la prima parola)
            words = santo_clean.split()
            if len(words) > 1 and not any(w[0].isupper() for w in words[1:]):
                is_valid = False

            if is_valid and santo_clean and len(santo_clean) > 3:
                candidati.append(santo_clean)

    # Se abbiamo trovato candidati, prendiamo il primo
    if candidati:
        candidati_unici = []
        for c in candidati:
            if c not in candidati_unici:
                candidati_unici.append(c)
        return candidati_unici[0], "Memoria"

    return "", ""

def extract_lodi(data_liturgia):
    """Estrae le Lodi Mattutine per la data specificata"""
    url = f"https://www.chiesacattolica.it/la-liturgia-delle-ore/?data-liturgia={data_liturgia}&ora=lodi-mattutine"

    try:
        # FIX: aggiunto header per encoding corretto
        headers = {
            'Accept-Charset': 'utf-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.encoding = 'utf-8'
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Errore: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')

    # Cerca celebrazione nel titolo della pagina o intestazione
    title_celebrazione = ""
    title_tipo = ""

    # 1. Prova a estrarre dal title HTML
    title_tag = soup.find('title')
    if title_tag:
        title_text = title_tag.get_text()
        if " - " in title_text:
            parts = title_text.split(" - ")
            for part in parts:
                part_upper = part.strip().upper()
                if "SOLENNITÀ" in part_upper:
                    title_tipo = "Solennità"
                    title_celebrazione = part.strip().replace("SOLENNITÀ DI", "").replace("SOLENNITÀ", "").strip()
                    break
                elif "FESTA" in part_upper:
                    title_tipo = "Festa"
                    title_celebrazione = part.strip().replace("FESTA DI", "").replace("FESTA", "").strip()
                    break
                elif "MEMORIA" in part_upper:
                    title_tipo = "Memoria"
                    title_celebrazione = part.strip().replace("MEMORIA DI", "").replace("MEMORIA", "").strip()
                    if " - " in title_celebrazione:
                        title_celebrazione = title_celebrazione.split(" - ")[0].strip()
                    break

    # 2. Se non trovato nel title, cerca nell'intestazione della pagina
    if not title_celebrazione:
        page_text_preview = soup.get_text(separator="\n")
        preview_lines = page_text_preview.split("\n")[:50]

        for line in preview_lines:
            line_clean = clean_text(line).strip()
            line_upper = line_clean.upper()

            if " - MEMORIA" in line_upper or " - SOLENNITÀ" in line_upper or " - FESTA" in line_upper:
                if " - SOLENNITÀ" in line_upper:
                    title_tipo = "Solennità"
                    title_celebrazione = line_clean.split(" - ")[0].strip()
                elif " - FESTA" in line_upper:
                    title_tipo = "Festa"
                    title_celebrazione = line_clean.split(" - ")[0].strip()
                elif " - MEMORIA" in line_upper:
                    title_tipo = "Memoria"
                    title_celebrazione = line_clean.split(" - ")[0].strip()
                break

    page_text = soup.get_text(separator="\n")
    lines = [clean_text(line) for line in page_text.split("\n") if clean_text(line)]

    # Struttura dati
    lodi = {
        "data": data_liturgia,
        "data_formattata": format_date(data_liturgia),
        "tipo": "Lodi Mattutine",
        "url_fonte": url,
        "celebrazione": {"santo": "", "tipo": ""},
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

    while i < len(lines):
        line = lines[i]

        # INTRODUZIONE
        if "O Dio, vieni a salvarmi" in line:
            lodi["introduzione"]["versetto"] = "O Dio, vieni a salvarmi"
            i += 1
            while i < len(lines) and "R." in lines[i]:
                i += 1
            if i < len(lines):
                lodi["introduzione"]["risposta"] = lines[i]
            # Dossologia fissa
            lodi["introduzione"]["dossologia"] = "Gloria al Padre e al Figlio *\ne allo Spirito Santo.\nCome era nel principio, e ora e sempre *\nnei secoli dei secoli. Amen."
            i += 1
            continue

        # INNO
        if line == "INNO":
            i += 1
            while i < len(lines):
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

        # SALMODIA
        if line.endswith("ant.") and line[0].isdigit():
            salmo_num = int(line[0])
            i += 1

            # Antifona
            antifona_lines = []
            while i < len(lines) and not ("SALMO" in lines[i] or "CANTICO" in lines[i]):
                antifona_lines.append(clean_text(lines[i]))
                i += 1

            # Titolo
            titolo = ""
            if i < len(lines) and ("SALMO" in lines[i] or "CANTICO" in lines[i]):
                titolo = clean_text(lines[i])
                i += 1

            # Sottotitolo
            sottotitolo_lines = []
            while i < len(lines) and not lines[i].startswith("("):
                sottotitolo_lines.append(clean_text(lines[i]))
                i += 1

            # Citazione
            citazione = ""
            if i < len(lines) and lines[i].startswith("("):
                cit_lines = []
                while i < len(lines):
                    cit_lines.append(clean_text(lines[i]))
                    if lines[i].endswith(")") or lines[i].endswith(")."):
                        i += 1
                        break
                    i += 1
                citazione = " ".join(cit_lines)

            # Testo
            testo_lines = []
            while i < len(lines):
                if lines[i] == f"{salmo_num} ant.":
                    break
                if salmo_num < 3 and lines[i] == f"{salmo_num + 1} ant.":
                    break
                if "LETTURA BREVE" in lines[i]:
                    break
                cleaned = clean_text(lines[i])
                if cleaned:
                    testo_lines.append(cleaned)
                i += 1

            lodi["salmodia"].append({
                "numero": salmo_num,
                "antifona": " ".join(antifona_lines),
                "titolo": titolo,
                "sottotitolo": " ".join(sottotitolo_lines),
                "citazione": citazione,
                "testo": testo_lines,
                "dossologia": "Gloria al Padre e al Figlio *\ne allo Spirito Santo.\nCome era nel principio, e ora e sempre *\nnei secoli dei secoli. Amen."
            })

            # Salta ripetizione antifona
            if i < len(lines) and lines[i] == f"{salmo_num} ant.":
                i += 1
                while i < len(lines) and not (lines[i] == f"{salmo_num + 1} ant." or "LETTURA" in lines[i]):
                    i += 1
            continue

        # LETTURA BREVE
        if line == "LETTURA BREVE":
            i += 1
            if i < len(lines):
                lodi["lettura_breve"]["riferimento"] = clean_text(lines[i])
                i += 1

            lettura_lines = []
            while i < len(lines) and "RESPONSORIO" not in lines[i]:
                lettura_lines.append(clean_text(lines[i]))
                i += 1
            lodi["lettura_breve"]["testo"] = "\n".join(lettura_lines)
            continue

        # RESPONSORIO BREVE
        if line == "RESPONSORIO BREVE":
            i += 1
            resp_lines = []
            while i < len(lines) and not ("Ant" in lines[i] or "CANTICO" in lines[i]):
                cleaned = clean_text(lines[i])
                if cleaned:
                    resp_lines.append(cleaned)
                i += 1
            lodi["responsorio_breve"] = resp_lines
            continue

        # CANTICO EVANGELICO - Antifona
        if "Ant" in line and "Ben" in line:
            i += 1
            ant_lines = []
            while i < len(lines) and "CANTICO" not in lines[i]:
                cleaned = clean_text(lines[i])
                if cleaned:
                    ant_lines.append(cleaned)
                i += 1
            lodi["cantico_evangelico"]["antifona"] = "\n".join(ant_lines)
            continue

        # CANTICO DI ZACCARIA
        if "CANTICO DI ZACCARIA" in line:
            i += 1

            # Salta riferimento
            if i < len(lines) and lines[i].startswith("Lc"):
                i += 1

            # Salta sottotitolo
            if i < len(lines) and not lines[i].startswith("Benedetto"):
                i += 1

            # Raccogli testo
            benedictus_lines = []
            dossologia_lines = []
            in_dossologia = False

            while i < len(lines):
                if "Ant" in lines[i] and "Ben" in lines[i]:
                    break
                if "INVOCAZIONI" in lines[i]:
                    break

                if "Gloria al Padre" in lines[i]:
                    in_dossologia = True

                if in_dossologia:
                    dossologia_lines.append(clean_text(lines[i]))
                    if "Amen" in lines[i]:
                        i += 1
                        break
                else:
                    cleaned = clean_text(lines[i])
                    if cleaned:
                        benedictus_lines.append(cleaned)

                i += 1

            lodi["cantico_evangelico"]["testo"] = benedictus_lines
            lodi["cantico_evangelico"]["dossologia"] = "\n".join(dossologia_lines)

            # Salta ripetizione antifona
            if i < len(lines) and "Ant" in lines[i] and "Ben" in lines[i]:
                i += 1
                while i < len(lines) and "INVOCAZIONI" not in lines[i]:
                    i += 1
            continue

        # INVOCAZIONI
        if line == "INVOCAZIONI":
            i += 1

            # Raccogli tutto prima del primo "—"
            pre_invocazioni = []
            while i < len(lines) and lines[i] != "—" and "Padre nostro" not in lines[i]:
                if re.match(r'^(Cristo|Signore|Tu|Per|Verbo|O\s)', lines[i]):
                    if i + 2 < len(lines) and lines[i + 2] == "—":
                        break
                    if i + 1 < len(lines) and lines[i + 1] == "—":
                        break

                pre_invocazioni.append(clean_text(lines[i]))
                i += 1

            # Separa introduzione e ritornello
            intro_end = -1
            for idx, text in enumerate(pre_invocazioni):
                if text.endswith(':'):
                    intro_end = idx
                    break

            if intro_end >= 0:
                lodi["invocazioni"]["introduzione"] = "\n".join(pre_invocazioni[:intro_end + 1])
                lodi["invocazioni"]["ritornello"] = "\n".join(pre_invocazioni[intro_end + 1:])
            else:
                lodi["invocazioni"]["introduzione"] = "\n".join(pre_invocazioni)

            # FIX: migliorata logica raccolta invocazioni
            invocazioni_lista = []
            current_inv = []

            while i < len(lines) and "Padre nostro" not in lines[i]:
                if lines[i] == "—":
                    current_inv.append(lines[i])
                    # Salva invocazione completa quando incontri il separatore
                    if len(current_inv) > 1:
                        invocazioni_lista.append("\n".join(current_inv))
                        current_inv = []
                else:
                    cleaned = clean_text(lines[i])
                    if cleaned:
                        current_inv.append(cleaned)
                i += 1

            # Ultima invocazione
            if current_inv and len(current_inv) > 1:
                invocazioni_lista.append("\n".join(current_inv))

            lodi["invocazioni"]["lista"] = invocazioni_lista
            continue

        # ORAZIONE
        if line == "ORAZIONE":
            i += 1
            or_lines = []

            while i < len(lines):
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

        # CONCLUSIONE
        if "Il Signore ci benedica" in line:
            lodi["conclusione"]["benedizione"] = clean_text(line)
            i += 1
            while i < len(lines) and "R." in lines[i]:
                i += 1
            if i < len(lines):
                lodi["conclusione"]["risposta"] = clean_text(lines[i])
            break

        i += 1

    # Estrai celebrazione
    if title_celebrazione and title_tipo:
        lodi["celebrazione"]["santo"] = clean_text(title_celebrazione)
        lodi["celebrazione"]["tipo"] = title_tipo
    else:
        antifone_text = " ".join([s["antifona"] for s in lodi["salmodia"]])
        celebrazione, tipo = extract_celebrazione(
            lodi["orazione"],
            " ".join(lodi["invocazioni"]["lista"]),
            antifone_text
        )

        if celebrazione:
            lodi["celebrazione"]["santo"] = celebrazione
            lodi["celebrazione"]["tipo"] = tipo

    return lodi

def main():
    """Funzione principale"""

    sys.argv.append('20251001')
    sys.argv.append('20251231')

    if len(sys.argv) < 2:
        print("📖 Uso:")
        print("  python lodi3.py YYYYMMDD [--db-only]")
        print("  python lodi3.py YYYYMMDD YYYYMMDD [--db-only]")
        print("\nOpzioni:")
        print("  --db-only    Salva solo su database (no JSON)")
        return

    # Controlla opzioni
    db_only = "--db-only" in sys.argv
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]

    if len(args) < 1:
        print("❌ Specifica almeno una data")
        return

    data_inizio = args[0]
    db_path = "instance/lodi.db"

    # Inizializza database
    init_database(db_path)

    # Singola data
    if len(args) == 1:
        print(f"\n{'=' * 60}")
        print(f"ESTRAZIONE LODI MATTUTINE - {format_date(data_inizio)}")
        print(f"{'=' * 60}\n")

        lodi = extract_lodi(data_inizio)

        if lodi:
            saved_json = False
            saved_db = False

            # Salva su JSON (se non --db-only)
            if not db_only:
                try:
                    output_file = f"lodi_{data_inizio}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(lodi, f, ensure_ascii=False, indent=2)
                    size = os.path.getsize(output_file) / 1024
                    print(f"✅ JSON: {output_file} ({size:.2f} KB)")
                    saved_json = True
                except Exception as e:
                    print(f"❌ Errore JSON: {e}")

            # Salva su database
            print(f"💾 Salvataggio su database...", end=" ")
            if save_to_database(lodi, db_path):
                print(f"✅ OK")
                saved_db = True
            else:
                print(f"❌ ERRORE")

            # Mostra info estratte
            if lodi["celebrazione"]["santo"]:
                tipo_emoji = "🎉" if lodi["celebrazione"]["tipo"] == "Solennità" else "🕊️"
                print(f"{tipo_emoji} {lodi['celebrazione']['tipo']}: {lodi['celebrazione']['santo']}")
            print(f"📜 Invocazioni: {len(lodi['invocazioni']['lista'])}")
            print(f"📊 Salmodia: {len(lodi['salmodia'])} salmi/cantici")
        else:
            print("❌ Errore estrazione dati")

    # Range di date
    elif len(args) == 2:
        data_fine = args[1]

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

        if not db_only:
            os.makedirs(output_dir, exist_ok=True)

        print(f"\n{'=' * 60}")
        print(f"ESTRAZIONE RANGE: {format_date(data_inizio)} → {format_date(data_fine)}")
        print(f"Giorni: {num_giorni}")
        if not db_only:
            print(f"Directory JSON: {output_dir}/")
        print(f"Database: {db_path}")
        print(f"{'=' * 60}\n")

        successi = 0
        current_date = dt_inizio

        for i in range(num_giorni):
            data_str = current_date.strftime("%Y%m%d")
            print(f"[{i + 1}/{num_giorni}] {format_date(data_str)}...", end=" ")

            lodi = extract_lodi(data_str)

            if lodi:
                # Salva JSON
                if not db_only:
                    output_file = os.path.join(output_dir, f"lodi_{data_str}.json")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(lodi, f, ensure_ascii=False, indent=2)

                # Salva DB
                if save_to_database(lodi, db_path):
                    if db_only:
                        print(f"✅ DB OK")
                    else:
                        size = os.path.getsize(output_file) / 1024
                        print(f"✅ OK ({size:.2f} KB + DB)")
                    successi += 1
                else:
                    print("⚠️  JSON OK, DB errore")
                    successi += 1
            else:
                print("❌ ERRORE")

            current_date += timedelta(days=1)

            if i < num_giorni - 1:
                time.sleep(0.5)

        print(f"\n{'=' * 60}")
        print(f"✅ Completato: {successi}/{num_giorni} estrazioni riuscite")
        if not db_only:
            print(f"📁 JSON salvati in: {output_dir}/")
        print(f"💾 Database: {db_path}")
        print(f"{'=' * 60}\n")

if __name__ == "__main__":
    main()