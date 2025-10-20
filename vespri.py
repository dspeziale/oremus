#!/usr/bin/env python3
"""
Estrattore Vespri - Liturgia delle Ore
Basato sulla stessa logica delle Lodi Mattutine
VERSIONE CORRETTA CON FIX PER MAGNIFICAT
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

    start_idx = -1
    for i, line in enumerate(lines):
        if line.startswith('SALMO') or line.startswith('CANTICO'):
            start_idx = i + 1
            break

    if start_idx == -1:
        return ""

    testo = []
    for i in range(start_idx, len(lines)):
        line = lines[i].strip()

        if ' ant.' in line or line.startswith('Gloria'):
            break

        if line and not line.startswith('Alla fine'):
            testo.append(line)

    return '\n'.join(testo)


# ============================================================================
# ESTRAZIONE CANTICO DELLA BEATA VERGINE (MAGNIFICAT) - VERSIONE CORRETTA
# ============================================================================

def estrai_cantico_magnificat(html):
    """
    Estrae CANTICO DELLA BEATA VERGINE con tutti i dettagli:
    - Riferimento biblico (Lc, Mt, ecc.)
    - Sottotitolo tematico
    - Testo del cantico
    - Dossologia finale
    """

    # Cattura da CANTICO DELLA BEATA VERGINE fino a INTERCESSIONI
    cant_match = re.search(
        r'CANTICO DELLA BEATA VERGINE(.*?)(?=INTERCESSIONI)',
        html,
        re.DOTALL
    )

    if not cant_match:
        return {
            "riferimento": "",
            "sottotitolo": "",
            "antifona": "",
            "testo": "",
            "dossologia": ""
        }

    cant_raw = cant_match.group(1)
    cant = pulisci_testo(cant_raw)

    lines = [l.strip() for l in cant.split('\n') if l.strip()]

    result = {
        "riferimento": "",
        "sottotitolo": "",
        "antifona": "",
        "testo": "",
        "dossologia": ""
    }

    if not lines:
        return result

    idx = 0

    # 1. Riferimento biblico (es: "Lc 1, 46-55")
    if idx < len(lines) and re.match(
            r'^(Lc|Mt|Mc|Gv|At|Rm|1Cor|2Cor|Gal|Ef|Fil|Col|1Ts|2Ts|1Tm|2Tm|Tt|Fm|Eb|Gc|1Pt|2Pt|1Gv|2Gv|3Gv|Gd|Ap)',
            lines[idx]):
        result["riferimento"] = lines[idx]
        idx += 1

    # 2. Sottotitolo tematico (es: "Esultanza dell'anima nel Signore")
    # Il sottotitolo non contiene * e non inizia con maiuscole tipo "L'anima"
    if idx < len(lines) and '*' not in lines[idx] and not lines[idx].startswith("L'"):
        result["sottotitolo"] = lines[idx]
        idx += 1

    # 3. Raccogli testo e dossologia
    testo_lines = []
    doss_lines = []
    in_dossologia = False

    for i in range(idx, len(lines)):
        line = lines[i]

        # Rileva inizio dossologia
        if "Gloria al Padre" in line:
            in_dossologia = True

        # Separa testo e dossologia
        if in_dossologia:
            doss_lines.append(line)
        else:
            # Salta le ripetizioni di antifona
            if "Ant. al Magn." not in line and "L'anima mia magnifica il Signore" not in line:
                if line:  # Non aggiungere linee vuote
                    testo_lines.append(line)
            elif "L'anima mia magnifica il Signore" in line and '*' in line:
                # Primo verso del cantico effettivo
                testo_lines.append(line)

    result["testo"] = '\n'.join(testo_lines)
    result["dossologia"] = '\n'.join(doss_lines)

    return result


# ============================================================================
# ESTRAZIONE INTERCESSIONI - VERSIONE MIGLIORATA
# ============================================================================

def estrai_intercessioni(html):
    """
    Estrae INTERCESSIONI con struttura corretta:
    - introduzione
    - lista di invocazioni con formato: titolo -- risposta
    """

    inv_match = re.search(r'INTERCESSIONI(.*?)(?=Padre nostro)', html, re.DOTALL)

    if not inv_match:
        return {"introduzione": "", "lista": []}

    inv_raw = inv_match.group(1)
    inv = pulisci_testo(inv_raw)

    lines = [l.strip() for l in inv.split('\n') if l.strip()]

    result = {"introduzione": "", "lista": []}

    if not lines:
        return result

    # Trova dove finisce l'introduzione
    intro_end = 0
    for i, line in enumerate(lines):
        if line.endswith(':'):
            intro_end = i
            break

    # Salva introduzione
    if intro_end > 0:
        result["introduzione"] = '\n'.join(lines[:intro_end + 1])
        lines = lines[intro_end + 1:]

    # Parse invocazioni - ogni invocazione è: titolo -- risposta
    current_inv = None
    invocazioni = []

    for line in lines:
        # Se è un separatore – significa che è una risposta
        if line.strip() == "–" or line.strip() == "-":
            continue

        # Se la linea contiene un'ipotesi di separatore interno
        if ' – ' in line or ' - ' in line:
            parts = re.split(r'\s+[–-]\s+', line)
            if len(parts) == 2:
                invocazioni.append({
                    "titolo": parts[0].strip(),
                    "risposta": parts[1].strip()
                })
            else:
                # Altrimenti è solo un titolo
                if current_inv is None:
                    current_inv = {"titolo": line, "risposta": ""}
        else:
            # Se non c'è separatore, è un titolo nuovo
            if current_inv is not None and current_inv["risposta"]:
                invocazioni.append(current_inv)
            current_inv = {"titolo": line, "risposta": ""}

    # Aggiungi l'ultima invocazione
    if current_inv is not None:
        invocazioni.append(current_inv)

    result["lista"] = invocazioni

    return result


# ============================================================================
# ESTRAZIONE PRINCIPALI
# ============================================================================

def estrai_vespri(data_liturgia):
    """Estrae tutti i Vespri - VERSIONE CORRETTA"""
    url = f"https://www.chiesacattolica.it/la-liturgia-delle-ore/?data-liturgia={data_liturgia}&ora=vespri"

    try:
        response = requests.get(url, timeout=30)
        response.encoding = 'utf-8'
        html = response.text
    except Exception as e:
        print(f"❌ Errore fetch: {e}")
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

    # === SALMODIA (3 salmi + 1 cantico per Vespri) ===
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

    # === CANTICO DELLA BEATA VERGINE (Magnificat) - VERSIONE CORRETTA ===
    cant_data = estrai_cantico_magnificat(html)
    vespri["cantico_evangelico"] = cant_data

    # === INTERCESSIONI - VERSIONE CORRETTA ===
    intercessioni_data = estrai_intercessioni(html)
    vespri["invocazioni"] = intercessioni_data

    # === ORAZIONE ===
    oraz_match = re.search(r'ORAZIONE(.*?)(?=Il Signore ci benedica)', html, re.DOTALL)
    if oraz_match:
        vespri["orazione"] = pulisci_testo(oraz_match.group(1)).strip()

    # === CONCLUSIONE ===
    conc_match = re.search(r'(Il Signore ci benedica.*?)(?=R\.)', html, re.DOTALL)
    if conc_match:
        vespri["conclusione"] = pulisci_testo(conc_match.group(1)).strip()

    return vespri


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Funzione principale"""
    sys.argv.append("20251019")
    sys.argv.append("20251020")

    # Se lanciato senza argomenti, usa date di esempio
    if len(sys.argv) < 2:
        sys.argv.extend(["20251019", "20251020"])

    if len(sys.argv) < 2:
        print("📖 Uso:")
        print("  python vespri.py YYYYMMDD")
        print("  python vespri.py YYYYMMDD YYYYMMDD")
        return

    os.makedirs("json", exist_ok=True)

    dates_to_process = sys.argv[1:]

    for data in dates_to_process:
        print(f"\n{'=' * 60}")
        print(f"ESTRAZIONE VESPRI: {formato_data(data)}")
        print(f"{'=' * 60}")

        vespri = estrai_vespri(data)

        if vespri:
            output_file = f"json/vespri_{data}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(vespri, f, ensure_ascii=False, indent=2)

            print(f"\n✅ Salvato: {output_file}")
            print(f"📊 Salmodia: {len(vespri['salmodia'])} salmi")
            print(f"📖 Lettura breve: {vespri['lettura_breve']['riferimento']}")
            print(f"🎶 Cantico: {vespri['cantico_evangelico']['sottotitolo']}")
            print(f"🙏 Intercessioni: {len(vespri['invocazioni']['lista'])} invocazioni")
        else:
            print(f"\n❌ Errore nell'estrazione")


if __name__ == "__main__":
    main()