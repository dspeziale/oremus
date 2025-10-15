import requests
from bs4 import BeautifulSoup


def estrai_lodi_complete(html_content):
    """
    Estrae TUTTA la liturgia delle Lodi Mattutine in modo completo e strutturato
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    lodi = {
        'data': '',
        'titolo': '',
        'celebrazione': '',
        'versetto_iniziale': '',
        'gloria': '',
        'nota': '',
        'inno': '',
        'salmi': [],
        'lettura_breve': {
            'riferimento': '',
            'testo': ''
        },
        'responsorio_breve': '',
        'benedictus': {
            'antifona': '',
            'cantico': ''
        },
        'invocazioni': '',
        'padre_nostro': True,
        'orazione': '',
        'benedizione_finale': ''
    }

    # ==================== INTESTAZIONE ====================
    # Data
    data_elem = soup.find('span', class_='cci-data-estesa-liturgia')
    if data_elem:
        lodi['data'] = data_elem.get_text(strip=True)

    # Titolo
    titolo_elem = soup.find('h1', class_='cci_content_page_current_title')
    if titolo_elem:
        lodi['titolo'] = titolo_elem.get_text(strip=True)

    # Celebrazione (Santo del giorno, memoria, ecc.)
    celebrazione_elem = soup.find('div', class_='cci-opere-giorni-liturgia')
    if celebrazione_elem:
        lodi['celebrazione'] = celebrazione_elem.get_text(strip=True)

    # ==================== VERSETTO INIZIALE ====================
    versetti = soup.find_all('div', class_='lo_versetto')
    if len(versetti) >= 2:
        # Primo versetto: "O Dio, vieni a salvarmi..."
        lodi['versetto_iniziale'] = versetti[0].get_text('\n', strip=True)
        # Secondo versetto: Gloria al Padre...
        lodi['gloria'] = versetti[1].get_text('\n', strip=True)

    # Nota
    nota_elem = soup.find('div', class_='lo_nota')
    if nota_elem:
        lodi['nota'] = nota_elem.get_text(strip=True)

    # ==================== INNO ====================
    titolo_inno = soup.find('div', class_='lo_titolo', string='INNO')
    if titolo_inno:
        inno_parts = []
        current = titolo_inno.next_sibling

        while current:
            if hasattr(current, 'name'):
                if current.name == 'div' and current.get('class') and 'lo_titolo' in current.get('class'):
                    # Se troviamo "Oppure:", continuiamo a raccogliere
                    if 'Oppure:' in current.get_text():
                        inno_parts.append('\n' + current.get_text(strip=True) + '\n')
                        current = current.next_sibling
                        continue
                    else:
                        break

                if current.name == 'br':
                    inno_parts.append('\n')
                elif current.string:
                    inno_parts.append(current.string)
            elif isinstance(current, str):
                text = current.strip()
                if text:
                    inno_parts.append(text)

            current = current.next_sibling

        lodi['inno'] = ''.join(inno_parts).strip()

    # ==================== SALMI E CANTICI ====================
    # Trova tutti i titoli dei salmi/cantici
    contenuto_liturgia = soup.find('div', class_='cci-liturgia-ore')
    if contenuto_liturgia:
        elementi = contenuto_liturgia.find_all(['div'])

        i = 0
        while i < len(elementi):
            elem = elementi[i]

            # Cerca titoli di SALMO o CANTICO
            if elem.get('class') and 'lo_titolo' in elem.get('class'):
                titolo_text = elem.get_text(strip=True)

                if 'SALMO' in titolo_text or 'CANTICO' in titolo_text:
                    salmo = {
                        'numero': len(lodi['salmi']) + 1,
                        'titolo': titolo_text,
                        'antifona_iniziale': '',
                        'sottotitolo': '',
                        'testo': [],
                        'antifona_finale': ''
                    }

                    # Cerca antifona prima del salmo
                    j = i - 1
                    while j >= 0:
                        prev_elem = elementi[j]
                        if prev_elem.get('class') and 'lo_versetto' in prev_elem.get('class'):
                            antifona_div = prev_elem.find('div', class_='lo_antifona')
                            if antifona_div:
                                ant_text = antifona_div.get_text(strip=True)
                                if ant_text and 'ant.' in ant_text.lower():
                                    salmo['antifona_iniziale'] = prev_elem.get_text('\n', strip=True)
                                    break
                        j -= 1

                    # Cerca sottotitolo
                    j = i + 1
                    if j < len(elementi):
                        next_elem = elementi[j]
                        if next_elem.get('class') and 'lo_versetto' in next_elem.get('class'):
                            sottotitolo_div = next_elem.find('div', class_='lo_sottotitolo')
                            if sottotitolo_div:
                                salmo['sottotitolo'] = next_elem.get_text('\n', strip=True)
                                j += 1

                    # Raccogli tutti i versetti del salmo
                    while j < len(elementi):
                        vers_elem = elementi[j]

                        # Stop se troviamo un nuovo titolo o l'antifona finale
                        if vers_elem.get('class'):
                            if 'lo_titolo' in vers_elem.get('class'):
                                break

                            if 'lo_versetto' in vers_elem.get('class'):
                                # Controlla se è l'antifona finale
                                antifona_div = vers_elem.find('div', class_='lo_antifona')
                                if antifona_div:
                                    ant_text = antifona_div.get_text(strip=True)
                                    if ant_text and 'ant.' in ant_text.lower():
                                        salmo['antifona_finale'] = vers_elem.get_text('\n', strip=True)
                                        break

                                # Altrimenti è un versetto del salmo
                                verso_text = vers_elem.get_text('\n', strip=True)
                                if verso_text:
                                    salmo['testo'].append(verso_text)

                        j += 1

                    lodi['salmi'].append(salmo)
                    i = j
                    continue

            i += 1

    # ==================== LETTURA BREVE ====================
    lettura_titolo = soup.find('div', class_='lo_titolo', string=lambda x: x and 'LETTURA BREVE' in x)
    if lettura_titolo:
        lodi['lettura_breve']['riferimento'] = lettura_titolo.get_text(strip=True)
        lettura_vers = lettura_titolo.find_next('div', class_='lo_versetto')
        if lettura_vers:
            lodi['lettura_breve']['testo'] = lettura_vers.get_text(strip=True)

    # ==================== RESPONSORIO BREVE ====================
    resp_titolo = soup.find('div', class_='lo_titolo', string='RESPONSORIO BREVE')
    if resp_titolo:
        resp_vers = resp_titolo.find_next('div', class_='lo_versetto')
        if resp_vers:
            lodi['responsorio_breve'] = resp_vers.get_text('\n', strip=True)

    # ==================== CANTICO DI ZACCARIA (BENEDICTUS) ====================
    # Antifona al Benedictus
    ant_ben_elem = soup.find('div', class_='lo_antifona', string='Ant. al Ben.')
    if ant_ben_elem and ant_ben_elem.parent:
        lodi['benedictus']['antifona'] = ant_ben_elem.parent.get_text('\n', strip=True)

    # Cantico di Zaccaria
    benedictus_titolo = soup.find('div', class_='lo_titolo', string=lambda x: x and 'CANTICO DI ZACCARIA' in x)
    if benedictus_titolo:
        cantico_versi = []
        current = benedictus_titolo.find_next_sibling()

        while current:
            if current.name == 'div':
                if current.get('class'):
                    if 'lo_titolo' in current.get('class'):
                        break
                    if 'lo_versetto' in current.get('class') or 'lo_sottotitolonoi' in current.get('class'):
                        text = current.get_text('\n', strip=True)
                        if text and 'Ant. al Ben.' not in text:
                            cantico_versi.append(text)

            current = current.find_next_sibling()

        lodi['benedictus']['cantico'] = '\n\n'.join(cantico_versi)

    # ==================== INVOCAZIONI ====================
    invoc_titolo = soup.find('div', class_='lo_titolo', string='INVOCAZIONI')
    if invoc_titolo:
        invoc_vers = invoc_titolo.find_next('div', class_='lo_versetto')
        if invoc_vers:
            lodi['invocazioni'] = invoc_vers.get_text('\n', strip=True)

    # ==================== ORAZIONE ====================
    orazione_titolo = soup.find('div', class_='lo_titolo', string='ORAZIONE')
    if orazione_titolo:
        # Cerca il versetto successivo che contiene l'orazione
        orazione_vers = orazione_titolo.find_next('div', class_='lo_versetto')
        if orazione_vers:
            lodi['orazione'] = orazione_vers.get_text(strip=True)

    # ==================== BENEDIZIONE FINALE ====================
    # Cerca l'ultima div lo_versetto che contiene la benedizione
    tutti_versetti = soup.find_all('div', class_='lo_versetto')
    if tutti_versetti:
        ultimo = tutti_versetti[-1]
        testo_ultimo = ultimo.get_text(strip=True)
        if 'benedica' in testo_ultimo.lower() or 'conduca alla vita eterna' in testo_ultimo.lower():
            lodi['benedizione_finale'] = ultimo.get_text('\n', strip=True)

    return lodi

def estrai_tutti_testi_tra(testo, inizio, fine):
    """
    Estrae tutti i testi compresi tra due stringhe.

    Returns:
        list: Lista di tutti i testi estratti
    """
    risultati = []
    pos = 0

    while True:
        try:
            pos_inizio = testo.index(inizio, pos) + len(inizio)
            pos_fine = testo.index(fine, pos_inizio)
            risultati.append(testo[pos_inizio:pos_fine])
            pos = pos_fine + len(fine)
        except ValueError:
            break

    return risultati
def format_date(date_string):
    """Formatta la data da YYYYMMDD a formato leggibile italiano"""
    try:
        date_obj = datetime.strptime(date_string, "%Y%m%d")
        giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]

        giorno_settimana = giorni[date_obj.weekday()]
        giorno = date_obj.day
        mese = mesi[date_obj.month - 1]
        anno = date_obj.year

        return f"{giorno_settimana} {giorno} {mese} {anno}"
    except:
        return date_string
def extract_lodi(data_liturgia):
    """
    Estrae le Lodi Mattutine COMPLETE per la data specificata
    """
    url = f"https://www.chiesacattolica.it/la-liturgia-delle-ore/?data-liturgia={data_liturgia}&ora=lodi-mattutine"

    print(f"Recupero dati da: {url}")

    try:
        response = requests.get(url, timeout=30)
        response.encoding = 'utf-8'
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Errore nel recupero dei dati: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
    risultati=estrai_tutti_testi_tra(str(soup),'<div class="row cci-liturgia-ore-menu-container">','Amen.</div>')
    print(risultati)
    soup=risultati

    lodi = {
        "data": data_liturgia,
        "data_formattata": format_date(data_liturgia),
        "tipo": "Lodi Mattutine",
        "url_fonte": url,
        "introduzione": {
            "versetto_iniziale": {"versetto": "", "risposta": ""},
            "dossologia": "",
            "nota": ""
        },
        "inno": {
            "opzione_1": {"lingua": "italiano", "testo_completo": []},
            "opzione_2": {"lingua": "latino", "testo_completo": []}
        },
        "salmodia": [
            {"numero": 1, "antifona": "", "titolo_salmo": "", "sottotitolo": "",
             "citazione_introduttiva": "", "testo_completo": []},
            {"numero": 2, "antifona": "", "titolo_cantico": "", "sottotitolo": "",
             "citazione_introduttiva": "", "testo_completo": []},
            {"numero": 3, "antifona": "", "titolo_salmo": "", "sottotitolo": "",
             "citazione_introduttiva": "", "testo_completo": []}
        ],
        "lettura_breve": {"riferimento": "", "testo_completo": ""},
        "responsorio_breve": {"testo_completo": []},
        "cantico_evangelico": {
            "nome": "Cantico di Zaccaria (Benedictus)",
            "riferimento": "Lc 1, 68-79",
            "sottotitolo": "", "antifona": "", "testo_completo": [], "dossologia": ""
        },
        "invocazioni": {
            "introduzione": "", "ritornello": "",
            "invocazioni_lista": [], "padre_nostro": "Padre nostro"
        },
        "orazione": {"testo_completo": ""},
        "conclusione": {"benedizione": "", "risposta": ""}
    }

    #page_text = soup.get_text(separator="\n")
    page_text = str(soup)
    lines = [clean_text(line) for line in page_text.split("\n") if clean_text(line)]

    i = 0
    inno_opzione = 1
    collecting_inno = False
    collecting_benedictus = False

    while i < len(lines):
        line = lines[i]

        if "O Dio, vieni a salvarmi" in line:
            lodi["introduzione"]["versetto_iniziale"]["versetto"] = clean_text("O Dio, vieni a salvarmi")
            i += 1
            if i < len(lines) and "R." in lines[i]:
                i += 1
            if i < len(lines):
                lodi["introduzione"]["versetto_iniziale"]["risposta"] = clean_text(lines[i])
            i += 1
            continue

        if "Gloria al Padre e al Figlio" in line and not collecting_benedictus:
            dossologia_lines = []
            while i < len(lines) and "Amen" not in lines[i]:
                dossologia_lines.append(clean_text(lines[i]))
                i += 1
            if i < len(lines) and "Amen" in lines[i]:
                dossologia_lines.append(clean_text(lines[i]))
                i += 1
            lodi["introduzione"]["dossologia"] = "\n".join(dossologia_lines)
            continue

        if "Questa introduzione si omette" in line:
            lodi["introduzione"]["nota"] = clean_text(line)
            i += 1
            continue

        if line == "INNO":
            collecting_inno = True
            inno_opzione = 1
            i += 1
            continue

        if collecting_inno and line == "Oppure:":
            inno_opzione = 2
            i += 1
            continue

        if collecting_inno and line.startswith("1 ant"):
            collecting_inno = False
            continue

        if collecting_inno:
            cleaned = clean_text(line)
            if cleaned:
                if inno_opzione == 1:
                    lodi["inno"]["opzione_1"]["testo_completo"].append(cleaned)
                else:
                    lodi["inno"]["opzione_2"]["testo_completo"].append(cleaned)
            i += 1
            continue

        if line == "1 ant.":
            salmo_idx = 0
            i += 1
            antifona_lines = []
            while i < len(lines) and not lines[i].startswith("SALMO"):
                antifona_lines.append(clean_text(lines[i]))
                i += 1
            lodi["salmodia"][salmo_idx]["antifona"] = " ".join(antifona_lines)

            if i < len(lines) and lines[i].startswith("SALMO"):
                lodi["salmodia"][salmo_idx]["titolo_salmo"] = clean_text(lines[i])
                i += 1

            sottotitolo_lines = []
            while i < len(lines) and not lines[i].startswith("("):
                sottotitolo_lines.append(clean_text(lines[i]))
                i += 1
            if sottotitolo_lines:
                lodi["salmodia"][salmo_idx]["sottotitolo"] = " ".join(sottotitolo_lines)

            if i < len(lines) and lines[i].startswith("("):
                citazione_lines = []
                while i < len(lines):
                    citazione_lines.append(clean_text(lines[i]))
                    if lines[i].endswith(").") or lines[i].endswith(")"):
                        i += 1
                        break
                    i += 1
                lodi["salmodia"][salmo_idx]["citazione_introduttiva"] = " ".join(citazione_lines)

            testo_lines = []
            while i < len(lines) and lines[i] != "1 ant.":
                cleaned = clean_text(lines[i])
                if cleaned:
                    testo_lines.append(cleaned)
                i += 1
            lodi["salmodia"][salmo_idx]["testo_completo"] = testo_lines

            if i < len(lines) and lines[i] == "1 ant.":
                i += 1
                while i < len(lines) and not (lines[i] == "2 ant." or lines[i] == "LETTURA BREVE"):
                    i += 1
            continue

        if line == "2 ant.":
            salmo_idx = 1
            i += 1
            antifona_lines = []
            while i < len(lines) and not lines[i].startswith("CANTICO"):
                antifona_lines.append(clean_text(lines[i]))
                i += 1
            lodi["salmodia"][salmo_idx]["antifona"] = " ".join(antifona_lines)

            if i < len(lines) and lines[i].startswith("CANTICO"):
                lodi["salmodia"][salmo_idx]["titolo_cantico"] = clean_text(lines[i])
                i += 1

            sottotitolo_lines = []
            while i < len(lines) and not lines[i].startswith("("):
                sottotitolo_lines.append(clean_text(lines[i]))
                i += 1
            if sottotitolo_lines:
                lodi["salmodia"][salmo_idx]["sottotitolo"] = " ".join(sottotitolo_lines)

            if i < len(lines) and lines[i].startswith("("):
                citazione_lines = []
                while i < len(lines):
                    citazione_lines.append(clean_text(lines[i]))
                    if lines[i].endswith(").") or lines[i].endswith(")"):
                        i += 1
                        break
                    i += 1
                lodi["salmodia"][salmo_idx]["citazione_introduttiva"] = " ".join(citazione_lines)

            testo_lines = []
            while i < len(lines) and lines[i] != "2 ant.":
                cleaned = clean_text(lines[i])
                if cleaned:
                    testo_lines.append(cleaned)
                i += 1
            lodi["salmodia"][salmo_idx]["testo_completo"] = testo_lines

            if i < len(lines) and lines[i] == "2 ant.":
                i += 1
                while i < len(lines) and not (lines[i] == "3 ant." or lines[i] == "LETTURA BREVE"):
                    i += 1
            continue

        if line == "3 ant.":
            salmo_idx = 2
            i += 1
            antifona_lines = []
            while i < len(lines) and not lines[i].startswith("SALMO"):
                antifona_lines.append(clean_text(lines[i]))
                i += 1
            lodi["salmodia"][salmo_idx]["antifona"] = " ".join(antifona_lines)

            if i < len(lines) and lines[i].startswith("SALMO"):
                lodi["salmodia"][salmo_idx]["titolo_salmo"] = clean_text(lines[i])
                i += 1

            sottotitolo_lines = []
            while i < len(lines) and not lines[i].startswith("("):
                sottotitolo_lines.append(clean_text(lines[i]))
                i += 1
            if sottotitolo_lines:
                lodi["salmodia"][salmo_idx]["sottotitolo"] = " ".join(sottotitolo_lines)

            if i < len(lines) and lines[i].startswith("("):
                citazione_lines = []
                while i < len(lines):
                    citazione_lines.append(clean_text(lines[i]))
                    if lines[i].endswith(").") or lines[i].endswith(")"):
                        i += 1
                        break
                    i += 1
                lodi["salmodia"][salmo_idx]["citazione_introduttiva"] = " ".join(citazione_lines)

            testo_lines = []
            while i < len(lines) and lines[i] != "3 ant." and lines[i] != "LETTURA BREVE":
                cleaned = clean_text(lines[i])
                if cleaned:
                    testo_lines.append(cleaned)
                i += 1
            lodi["salmodia"][salmo_idx]["testo_completo"] = testo_lines

            if i < len(lines) and lines[i] == "3 ant.":
                i += 1
                while i < len(lines) and lines[i] != "LETTURA BREVE":
                    i += 1
            continue

        if line == "LETTURA BREVE":
            i += 1
            if i < len(lines):
                lodi["lettura_breve"]["riferimento"] = clean_text(lines[i])
                i += 1
            lettura_lines = []
            while i < len(lines) and not lines[i].startswith("RESPONSORIO"):
                lettura_lines.append(clean_text(lines[i]))
                i += 1
            lodi["lettura_breve"]["testo_completo"] = "\n".join(lettura_lines)
            continue

        if line == "RESPONSORIO BREVE":
            i += 1
            responsorio_lines = []
            while i < len(lines) and not (lines[i].startswith("Ant") or "CANTICO" in lines[i]):
                cleaned = clean_text(lines[i])
                if cleaned:
                    responsorio_lines.append(cleaned)
                i += 1
            lodi["responsorio_breve"]["testo_completo"] = responsorio_lines
            continue

        if "Ant. al Ben" in line:
            i += 1
            antifona_ben_lines = []
            while i < len(lines) and not ("CANTICO" in lines[i]):
                antifona_ben_lines.append(clean_text(lines[i]))
                i += 1
            lodi["cantico_evangelico"]["antifona"] = "\n".join(antifona_ben_lines)
            continue

        if line == "CANTICO DI ZACCARIA":
            i += 1
            if i < len(lines) and lines[i].startswith("Lc"):
                lodi["cantico_evangelico"]["riferimento"] = clean_text(lines[i])
                i += 1
            if i < len(lines) and not lines[i].startswith("Benedetto"):
                lodi["cantico_evangelico"]["sottotitolo"] = clean_text(lines[i])
                i += 1
            collecting_benedictus = True
            continue

        if collecting_benedictus:
            if "Ant. al Ben" in line:
                collecting_benedictus = False
                i += 1
                while i < len(lines) and lines[i] != "INVOCAZIONI":
                    i += 1
                continue

            if line == "INVOCAZIONI":
                collecting_benedictus = False
                continue

            if "Gloria al Padre" in line:
                doss_lines = []
                while i < len(lines) and "Amen" not in lines[i]:
                    doss_lines.append(clean_text(lines[i]))
                    i += 1
                if i < len(lines):
                    doss_lines.append(clean_text(lines[i]))
                    i += 1
                lodi["cantico_evangelico"]["dossologia"] = "\n".join(doss_lines)
                continue

            cleaned = clean_text(line)
            if cleaned:
                lodi["cantico_evangelico"]["testo_completo"].append(cleaned)
            i += 1
            continue

        if line == "INVOCAZIONI":
            i += 1
            intro_lines = []
            while i < len(lines) and not ("Gesù" in lines[i] or "Cristo" in lines[i]):
                intro_lines.append(clean_text(lines[i]))
                i += 1
            lodi["invocazioni"]["introduzione"] = "\n".join(intro_lines)

            ritornello_lines = []
            while i < len(lines) and lines[i] != "—":
                ritornello_lines.append(clean_text(lines[i]))
                i += 1
            lodi["invocazioni"]["ritornello"] = "\n".join(ritornello_lines)

            invocazioni_list = []
            current_invocazione = []

            while i < len(lines) and not lines[i].startswith("Padre nostro"):
                if lines[i] == "—":
                    if current_invocazione:
                        invocazioni_list.append("\n".join(current_invocazione))
                    current_invocazione = []
                    i += 1
                    while i < len(lines) and lines[i] != "—" and not lines[i].startswith("Padre nostro"):
                        cleaned = clean_text(lines[i])
                        if cleaned:
                            current_invocazione.append(cleaned)
                        i += 1
                else:
                    i += 1

            if current_invocazione:
                invocazioni_list.append("\n".join(current_invocazione))

            lodi["invocazioni"]["invocazioni_lista"] = invocazioni_list

            if i < len(lines) and "Padre nostro" in lines[i]:
                i += 1
            continue

        if line == "ORAZIONE":
            i += 1
            orazione_lines = []
            while i < len(lines) and not lines[i].startswith("Il Signore"):
                orazione_lines.append(clean_text(lines[i]))
                i += 1
            lodi["orazione"]["testo_completo"] = " ".join(orazione_lines)
            continue

        if "Il Signore ci benedica" in line:
            lodi["conclusione"]["benedizione"] = clean_text(line)
            i += 1
            if i < len(lines) and "R." in lines[i]:
                i += 1
            if i < len(lines):
                lodi["conclusione"]["risposta"] = clean_text(lines[i])
            break

        i += 1

    return lodi

def stampa_lodi(lodi):
    """
    Stampa le Lodi in formato leggibile
    """
    print("=" * 80)
    print(f"LODI MATTUTINE - {lodi['data']}")
    print("=" * 80)
    print(f"\n{lodi['celebrazione']}\n")

    print("\n--- VERSETTO INIZIALE ---")
    print(lodi['versetto_iniziale'])
    print(f"\n{lodi['gloria']}")
    if lodi['nota']:
        print(f"\nNota: {lodi['nota']}")

    print("\n--- INNO ---")
    print(lodi['inno'])

    for salmo in lodi['salmi']:
        print(f"\n--- {salmo['titolo']} ---")
        if salmo['antifona_iniziale']:
            print(f"\n{salmo['antifona_iniziale']}")
        if salmo['sottotitolo']:
            print(f"\n{salmo['sottotitolo']}")
        print()
        for verso in salmo['testo']:
            print(verso)
        if salmo['antifona_finale']:
            print(f"\n{salmo['antifona_finale']}")

    print(f"\n--- LETTURA BREVE ---")
    print(f"{lodi['lettura_breve']['riferimento']}")
    print(f"{lodi['lettura_breve']['testo']}")

    print(f"\n--- RESPONSORIO BREVE ---")
    print(lodi['responsorio_breve'])

    print(f"\n--- CANTICO DI ZACCARIA (BENEDICTUS) ---")
    print(lodi['benedictus']['antifona'])
    print(f"\n{lodi['benedictus']['cantico']}")

    print(f"\n--- INVOCAZIONI ---")
    print(lodi['invocazioni'])

    print(f"\n--- PADRE NOSTRO ---")
    print("Padre nostro.")

    print(f"\n--- ORAZIONE ---")
    print(lodi['orazione'])

    print(f"\n--- BENEDIZIONE FINALE ---")
    print(lodi['benedizione_finale'])

    print("\n" + "=" * 80)


# UTILIZZO
if __name__ == "__main__":
    # Il tuo HTML
    html_content = """['\n<ul class="col-md-12 cci-liturgia-ore-menu list-inline">\n<li class="cci-liturgia-ore-menu-item">\n<a data-dataliturgia="20251017" data-dataliturgialabel="venerdi-17-ottobre-2025" data-liturgiatitolo="invitatorio" data-num_memorie="1" data-titololiturgialabel="santignazio-di-antiochia-vescovo-e-martire-memoria-iv-settimana-del-salterio" href="https://www.chiesacattolica.it/la-liturgia-delle-ore/?data-liturgia=20251017&amp;ora=invitatorio" title="Liturgia delle ore Invitatorio venerdì 17 Ottobre 2025">\n                Invitatorio            </a>\n</li>\n<li class="cci-liturgia-ore-menu-item">\n<a data-dataliturgia="20251017" data-dataliturgialabel="venerdi-17-ottobre-2025" data-liturgiatitolo="ufficio-delle-letture" data-num_memorie="1" data-titololiturgialabel="santignazio-di-antiochia-vescovo-e-martire-memoria-iv-settimana-del-salterio" href="https://www.chiesacattolica.it/la-liturgia-delle-ore/?data-liturgia=20251017&amp;ora=ufficio-delle-letture" title="Liturgia delle ore Ufficio delle letture venerdì 17 Ottobre 2025">\n                Ufficio delle letture            </a>\n</li>\n<li class="cci-liturgia-ore-menu-item cci-liturgia-ore-menu-item-current">\n<a data-dataliturgia="20251017" data-dataliturgialabel="venerdi-17-ottobre-2025" data-liturgiatitolo="lodi-mattutine" data-num_memorie="1" data-titololiturgialabel="santignazio-di-antiochia-vescovo-e-martire-memoria-iv-settimana-del-salterio" href="https://www.chiesacattolica.it/la-liturgia-delle-ore/?data-liturgia=20251017&amp;ora=lodi-mattutine" title="Liturgia delle ore Lodi mattutine venerdì 17 Ottobre 2025">\n                Lodi mattutine            </a>\n</li>\n<li class="cci-liturgia-ore-menu-item">\n<a data-dataliturgia="20251017" data-dataliturgialabel="venerdi-17-ottobre-2025" data-liturgiatitolo="ora-media" data-num_memorie="1" data-titololiturgialabel="santignazio-di-antiochia-vescovo-e-martire-memoria-iv-settimana-del-salterio" href="https://www.chiesacattolica.it/la-liturgia-delle-ore/?data-liturgia=20251017&amp;ora=ora-media" title="Liturgia delle ore Ora Media venerdì 17 Ottobre 2025">\n                Ora Media            </a>\n</li>\n<li class="cci-liturgia-ore-menu-item">\n<a data-dataliturgia="20251017" data-dataliturgialabel="venerdi-17-ottobre-2025" data-liturgiatitolo="vespri" data-num_memorie="1" data-titololiturgialabel="santignazio-di-antiochia-vescovo-e-martire-memoria-iv-settimana-del-salterio" href="https://www.chiesacattolica.it/la-liturgia-delle-ore/?data-liturgia=20251017&amp;ora=vespri" title="Liturgia delle ore Vespri venerdì 17 Ottobre 2025">\n                Vespri            </a>\n</li>\n<li class="cci-liturgia-ore-menu-item">\n<a data-dataliturgia="20251017" data-dataliturgialabel="venerdi-17-ottobre-2025" data-liturgiatitolo="compieta" data-num_memorie="1" data-titololiturgialabel="santignazio-di-antiochia-vescovo-e-martire-memoria-iv-settimana-del-salterio" href="https://www.chiesacattolica.it/la-liturgia-delle-ore/?data-liturgia=20251017&amp;ora=compieta" title="Liturgia delle ore Compieta venerdì 17 Ottobre 2025">\n                Compieta            </a>\n</li>\n</ul>\n</div>\n<div class="row">\n<div class="col-md-8" data-data_liturgia="20251017" data-num_memorie="1" data-selected_ora="lodi-mattutine" data-tipologia_giorno="feriale" id="cci_content_page">\n<div class="cci_breadcrumb"><a href="https://www.chiesacattolica.it/" property="v:title" rel="v:url">Home</a><span class="cci_separator"> — </span>Liturgia delle Ore</div><!-- .breadcrumbs --> <span class="cci-data-estesa-liturgia">venerdì 17 Ottobre 2025</span>\n<h1 class="cci_content_page_current_title">Lodi mattutine</h1>\n<div class="cci-opere-giorni-liturgia">SANT’IGNAZIO DI ANTIOCHIA, VESCOVO E MARTIRE - MEMORIA - IV SETTIMANA DEL SALTERIO</div>\n<div class="cci-liturgia-giorno-font-increase">\n            Grandezza Testo\n             <a class="cci-diminiuisci-font" href="#" title="Clicca più volte per diminuire la grandezza del carattere">A</a>\n<a class="cci-standard-font" href="#" title="Dimensione originale">A</a>\n<a class="cci-aumenta-font" href="#" title="Clicca più volte per aumentare la dimensione del carattere">A</a>\n</div>\n<article class="seed-post">\n<div class="cci-liturgia-ore cci-fontsize-dynamic">\n<div class="lo_versetto">\n<div class="lo_versetto">\n<div class="lo_antifona">V.</div>\r\nO Dio, vieni a salvarmi\r\n\r\n<div class="lo_antifona"><br/>\r\nR.</div>\r\nSignore, vieni presto in mio aiuto.</div>\n</div>\n<div class="lo_versetto">Gloria al Padre e al Figlio<br/>\r\n\xa0\xa0 e allo Spirito Santo.<br/>\r\nCome era nel principio, e ora e sempre<br/>\r\n\xa0\xa0 nei secoli dei secoli. Amen. Alleluia.</div>\n<div class="lo_nota">Questa introduzione si omette quando si comincia l\'Ufficio con l\'Invitatorio.</div>\n<div class="lo_titolo">INNO</div>\n<br/>\r\nO martire di Dio,<br/>\r\ndiscepolo fedele<br/>\r\nche hai segnato nel sangue<br/>\r\nil patto del battesimo!<br/>\n<br/>\r\nTu dividi con Cristo,<br/>\r\nagnello del riscatto,<br/>\r\nla croce e la vittoria<br/>\r\nnel regno dei beati.<br/>\n<br/>\r\nIntercedi per noi<br/>\r\npellegrini nel tempo<br/>\r\ne guida i nostri passi<br/>\r\nsulla via della pace.<br/>\n<br/>\r\nTu libera gli oppressi,<br/>\r\nsostieni i vacillanti,<br/>\r\ne raduna i dispersi<br/>\r\nnell’Amore del Padre.<br/>\n<br/>\r\nA te sia lode, o Cristo,<br/>\r\nParola del Dio vivo,<br/>\r\nche sveli nel martirio<br/>\r\nla forza del tuo Spirito. Amen.<br/>\r\n\xa0\r\n<div class="lo_titolo">Oppure:</div>\n<br/>\r\nMartyr Dei, qui únicum<br/>\r\nPatris sequéndo Fílium<br/>\r\nvictis triúmphas hóstibus,<br/>\r\nvictor\xa0 fruens cæléstibus,<br/>\n<br/>\r\nTui precátus múnere<br/>\r\nnostrum reátum dílue,<br/>\r\narcens mali contágium,<br/>\r\nvitæ repéllens tædium.<br/>\n<br/>\r\nSolúta sunt iam víncula<br/>\r\ntui sacráti córporis;<br/>\r\nnos solve vinclis sæculi<br/>\r\namóre Fílii Dei.<br/>\n<br/>\r\nHonor Patri cum Fílio<br/>\r\net Spíritu Paráclito,<br/>\r\nqui te coróna pérpeti<br/>\r\ncingunt in aula glóriæ. Amen.<div class="lo_versetto">\n<div class="lo_antifona">1 ant.</div>\r\nCrea in me, o Dio, un cuore puro,<br/>\r\n\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0 rinnova in me uno spirito saldo.</div>\n<div class="lo_titolo">SALMO 50\xa0\xa0\xa0 Pietà di me, o Signore</div>\n<div class="lo_versetto">\n<div class="lo_sottotitolo">Rinnovatevi nello spirito della vostra mente e rivestite<br/>\r\nl’uomo nuovo\r\n<div class="lo_normal">(cfr. Ef 4, 23-24).</div>\n</div>\n</div>\n<div class="lo_versetto">Pietà di me, o Dio,<br/>\r\n\xa0\xa0\xa0\xa0\xa0 secondo la tua misericordia; *<br/>\r\n\xa0\xa0 nel tuo grande amore<br/>\r\n\xa0\xa0\xa0\xa0\xa0 cancella il mio peccato.</div>\n<div class="lo_versetto">Lavami da tutte le mie colpe, *<br/>\r\n\xa0 \xa0mondami dal mio peccato.<br/>\r\nRiconosco la mia colpa, *<br/>\r\n\xa0 \xa0il mio peccato mi sta sempre dinanzi.</div>\n<div class="lo_versetto">Contro di te, contro te solo ho peccato, *<br/>\r\n\xa0 \xa0quello che è male ai tuoi occhi, io l’ho fatto;<br/>\r\nperciò sei giusto quando parli, *<br/>\r\n\xa0 \xa0retto nel tuo giudizio.</div>\n<div class="lo_versetto">Ecco, nella colpa sono stato generato, *<br/>\r\n\xa0 \xa0nel peccato mi ha concepito mia madre.<br/>\r\nMa tu vuoi la sincerità del cuore *<br/>\r\n\xa0 \xa0e nell’intimo m’insegni la sapienza.</div>\n<div class="lo_versetto">Purificami con issopo e sarò mondato; *<br/>\r\n\xa0 \xa0lavami e sarò più bianco della neve.\xa0<br/>\r\nFammi sentire gioia e letizia, *<br/>\r\n\xa0 \xa0esulteranno le ossa che hai spezzato.</div>\n<div class="lo_versetto">Distogli lo sguardo dai miei peccati, *<br/>\r\n\xa0 \xa0cancella tutte le mie colpe.<br/>\r\nCrea in me, o Dio, un cuore puro, *<br/>\r\n\xa0 \xa0rinnova in me uno spirito saldo.</div>\n<div class="lo_versetto">Non respingermi dalla tua presenza *<br/>\r\n\xa0 \xa0e non privarmi del tuo santo spirito.<br/>\r\nRendimi la gioia di essere salvato, *<br/>\r\n\xa0 \xa0sostieni in me un animo generoso.</div>\n<div class="lo_versetto">Insegnerò agli erranti le tue vie *<br/>\r\n\xa0 \xa0e i peccatori a te ritorneranno.<br/>\r\nLiberami dal sangue, Dio, Dio mia salvezza, *<br/>\r\n\xa0 \xa0la mia lingua esalterà la tua giustizia.</div>\n<div class="lo_versetto">Signore, apri le mie labbra *<br/>\r\n\xa0 \xa0e la mia bocca proclami la tua lode;<br/>\r\npoiché non gradisci il sacrificio *<br/>\r\n\xa0 \xa0e se offro olocausti, non li accetti.</div>\n<div class="lo_versetto">Uno spirito contrito *<br/>\r\n\xa0 \xa0è sacrificio a Dio,<br/>\r\nun cuore affranto e umiliato *<br/>\r\n\xa0 \xa0tu, o Dio, non disprezzi.</div>\n<div class="lo_versetto">Nel tuo amore<br/>\r\n\xa0\xa0 \xa0\xa0 fa’ grazia a Sion, *<br/>\r\n\xa0\xa0 rialza le mura<br/>\r\n\xa0\xa0 \xa0\xa0 di Gerusalemme.</div>\n<div class="lo_versetto">Allora gradirai i sacrifici prescritti, *<br/>\r\n\xa0 \xa0l’olocausto e l’intera oblazione,<br/>\r\nallora immoleranno vittime *<br/>\r\n\xa0 \xa0sopra il tuo altare.</div>\n<div class="lo_versetto">\n<div class="lo_antifona">1 ant.</div>\r\nCrea in me, o Dio, un cuore puro,<br/>\r\n\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0 rinnova in me uno spirito saldo.</div>\n<div class="lo_versetto">\n<div class="lo_antifona">2 ant.</div>\r\nRallegrati, Gerusalemme:<br/>\r\n\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0 in te si raduneranno i popoli<br/>\r\n\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0 e benediranno il Signore.</div>\n<div class="lo_titolo">CANTICO\xa0\xa0\xa0 Tb 13, 10-13. 15. 16c-17a<br/>\r\nRingraziamento per la liberazione del popolo</div>\n<div class="lo_sottotitolo">\n<div class="lo_versetto"><br/>\r\nMi mostrò la città santa, Gerusalemme... risplendente<br/>\r\ndella gloria di Dio\r\n<div class="lo_normal">(Ap 21, 10-11).</div>\n</div>\n</div>\n<div class="lo_versetto"><br/>\r\nTutti parlino del Signore *<br/>\r\n\xa0 \xa0e diano lode a lui in Gerusalemme.</div>\n<div class="lo_versetto">Gerusalemme, città santa, †<br/>\r\n\xa0 \xa0ti ha castigata per le opere dei tuoi figli, *<br/>\r\n\xa0 \xa0e avrà ancora pietà per i figli dei giusti.</div>\n<div class="lo_versetto">Da’ lode degnamente al Signore *<br/>\r\n\xa0 \xa0e benedici il re dei secoli;</div>\n<div class="lo_versetto">egli ricostruirà in te il suo tempio con gioia, *<br/>\r\n\xa0 \xa0per allietare in te tutti i deportati,<br/>\r\nper far contenti in te tutti gli sventurati, *<br/>\r\n\xa0 \xa0per tutte le generazioni dei secoli.</div>\n<div class="lo_versetto">Come luce splendida brillerai<br/>\r\n\xa0 \xa0 \xa0sino ai confini della terra; *<br/>\r\n\xa0\xa0 nazioni numerose verranno a te da lontano;</div>\n<div class="lo_versetto">gli abitanti di tutti i confini della terra †<br/>\r\n\xa0 \xa0verranno verso la dimora del tuo santo nome, *<br/>\r\n\xa0 \xa0portando in mano i doni per il re del cielo.</div>\n<div class="lo_versetto">Generazioni e generazioni<br/>\r\n\xa0 \xa0 \xa0esprimeranno in te l’esultanza *<br/>\r\n\xa0 \xa0e il nome della città eletta<br/>\r\n\xa0 \xa0 \xa0durerà nei secoli.</div>\n<div class="lo_versetto">Sorgi ed esulta per i figli dei giusti: †<br/>\r\n\xa0 \xa0tutti presso di te si raduneranno *<br/>\r\n\xa0 \xa0e benediranno il Signore dei secoli.</div>\n<div class="lo_versetto">Beati coloro che ti amano, *<br/>\r\n\xa0 \xa0beati coloro che gioiscono per la tua pace.</div>\n<div class="lo_versetto">Anima mia,<br/>\r\n\xa0\xa0 \xa0\xa0benedici il Signore, il gran sovrano: †<br/>\r\n\xa0 \xa0Gerusalemme sarà ricostruita *<br/>\r\n\xa0 \xa0come città della sua residenza per sempre.</div>\n<div class="lo_versetto">\n<div class="lo_antifona">2 ant.</div>\r\nRallegrati, Gerusalemme:<br/>\r\n\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0 in te si raduneranno i popoli<br/>\r\n\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0 e benediranno il Signore.</div>\n<div class="lo_versetto"><div class="lo_antifona">3 ant.</div>\r\nCittà di Dio, loda il tuo Signore:<br/>\r\n\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0 egli manda a te la sua parola.</div><div class="lo_titolo">SALMO 147\xa0\xa0\xa0 La Gerusalemme riedificata</div>\n<div class="lo_sottotitolo">Vieni, ti mostrerò la fidanzata, la sposa dell’Agnello</div>\r\n(Ap 21, 9).<br/>\r\n\xa0\r\n<div class="lo_versetto">Glorifica il Signore, Gerusalemme, *<br/>\r\n\xa0\xa0\xa0 loda, Sion, il tuo Dio.<br/>\r\nPerché ha rinforzato le sbarre delle tue porte, *<br/>\r\n\xa0\xa0\xa0 in mezzo a te ha benedetto i tuoi figli.</div>\n<div class="lo_versetto">Egli ha messo pace nei tuoi confini *<br/>\r\n\xa0\xa0\xa0 e ti sazia con fior di frumento.<br/>\r\nManda sulla terra la sua parola, *<br/>\r\n\xa0\xa0\xa0 il suo messaggio corre veloce.</div>\n<div class="lo_versetto">Fa scendere la neve come lana, *<br/>\r\n\xa0\xa0\xa0 come polvere sparge la brina.<br/>\r\nGetta come briciole la grandine, *<br/>\r\n\xa0\xa0\xa0 di fronte al suo gelo chi resiste?</div>\n<div class="lo_versetto">Manda una sua parola ed ecco si scioglie, *<br/>\r\n\xa0\xa0\xa0 fa soffiare il vento e scorrono le acque.<br/>\r\nAnnunzia a Giacobbe la sua parola, *<br/>\r\n\xa0\xa0\xa0 le sue leggi e i suoi decreti a Israele.</div>\n<div class="lo_versetto">Così non ha fatto<br/>\r\n\xa0\xa0\xa0\xa0\xa0\xa0 con nessun altro popolo, *<br/>\r\nnon ha manifestato ad altri<br/>\r\n\xa0\xa0\xa0 i suoi precetti.</div>\n<div class="lo_versetto"><div class="lo_antifona">3 ant.</div>\r\nCittà di Dio, loda il tuo Signore:<br/>\r\n\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0 egli manda a te la sua parola.</div><div class="lo_titolo">LETTURA BREVE\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0 2 Cor 1, 3-5</div>\n<div class="lo_versetto">\xa0\xa0 Sia benedetto Dio, Padre del Signore nostro Gesù Cristo, Padre misericordioso e Dio di ogni consolazione, il quale ci consola in ogni nostra tribolazione perché possiamo anche noi consolare quelli che si trovano in qualsiasi genere di afflizione con la consolazione con cui siamo consolati noi stessi da Dio. Infatti, come abbondano le sofferenze di Cristo in noi, così, per mezzo di Cristo, abbonda anche la nostra consolazione.</div>\r\n\xa0<div class="lo_titolo">RESPONSORIO BREVE</div>\n<div class="lo_versetto">\n<div class="lo_rosso">R.</div>\r\nMia forza,\r\n\r\n<div class="lo_rosso">*</div>\r\nmio canto è il Signore.<br/>\r\nMia forza, mio canto è il Signore.\r\n<div class="lo_rosso"><br/>\r\nV.</div>\r\nÈ lui la mia salvezza:<br/>\r\nmio canto è il Signore.<br/>\r\n\xa0\xa0 Gloria al Padre e al Figlio e allo Spirito Santo.<br/>\r\nMia forza, mio canto è il Signore.</div>\n<div class="lo_versetto"><div class="lo_antifona">Ant. al Ben.</div>\nCristo, morto per me,<br/>\nCristo, risorto per me:<br/>\nè lui che cerco e desidero.</div><div class="lo_titolo">CANTICO DI ZACCARIA\r\n<div class="lo_rif">Lc 1, 68-79</div>\n</div>\n<div class="lo_sottotitolonoi">\n<div class="lo_rosso">\n<div class="center">\n<div class="lo_versetto">Il Messia e il suo Precursore</div>\n</div>\n</div>\n</div>\n<div class="lo_versetto">Benedetto il Signore Dio d’Israele, *<br/>\r\n\xa0 \xa0perché ha visitato e redento il suo popolo,</div>\n<div class="lo_versetto">e ha suscitato per noi una salvezza potente *<br/>\r\n\xa0 \xa0nella casa di Davide, suo servo,</div>\n<div class="lo_versetto">come aveva promesso *<br/>\r\n\xa0 \xa0per bocca dei suoi santi profeti d’un tempo:</div>\n<div class="lo_versetto">salvezza dai nostri nemici, *<br/>\r\n\xa0 \xa0e dalle mani di quanti ci odiano.</div>\n<div class="lo_versetto">Così egli ha concesso misericordia ai nostri padri *<br/>\r\n\xa0 \xa0e si è ricordato della sua santa alleanza,</div>\n<div class="lo_versetto">del giuramento fatto ad Abramo, nostro padre, *<br/>\r\n\xa0 \xa0di concederci, liberàti dalle mani dei nemici,</div>\n<div class="lo_versetto">di servirlo senza timore, in santità e giustizia *<br/>\r\n\xa0 \xa0al suo cospetto, per tutti i nostri giorni.</div>\n<div class="lo_versetto">E tu, bambino, sarai chiamato profeta dell’Altissimo *<br/>\r\n\xa0 \xa0perché andrai innanzi al Signore<br/>\r\n\xa0\xa0\xa0\xa0\xa0 a preparargli le strade,</div>\n<div class="lo_versetto">per dare al suo popolo la conoscenza della salvezza *<br/>\r\n\xa0 \xa0nella remissione dei suoi peccati,</div>\n<div class="lo_versetto">grazie alla bontà misericordiosa del nostro Dio, *<br/>\r\n\xa0 \xa0per cui verrà a visitarci dall’alto un sole che sorge,</div>\n<div class="lo_versetto">per rischiarare quelli che stanno nelle tenebre *<br/>\r\n\xa0 \xa0e nell’ombra della morte</div>\n<div class="lo_versetto">e dirigere i nostri passi *<br/>\r\n\xa0 \xa0sulla via della pace.</div>\n<div class="lo_versetto">Gloria al Padre e al Figlio *<br/>\r\n\xa0 \xa0e allo Spirito Santo.</div>\r\nCome era nel principio, e ora e sempre *<br/>\r\n\xa0 \xa0nei secoli dei secoli. Amen.<div class="lo_versetto"><div class="lo_antifona">Ant. al Ben.</div>\nCristo, morto per me,<br/>\nCristo, risorto per me:<br/>\nè lui che cerco e desidero.</div><div class="lo_titolo">INVOCAZIONI</div>\n<div class="lo_versetto">In unione con i santi martiri, uccisi a causa del vangelo,<br/>\r\n\xa0\xa0 celebriamo e invochiamo il nostro Salvatore,<br/>\r\n\xa0\xa0 testimone fedele di Dio Padre:\xa0\xa0\r\n<div class="lo_sottotitolo">\xa0\xa0 Ci hai redenti con il tuo sangue, o Signore.<br/>\r\n\xa0</div>\r\nPer i tuoi martiri, che abbracciarono la morte\xa0a<br/>\r\n\xa0\xa0\xa0testimonianza della fede,\r\n<div class="lo_rosso"><br/>\r\n–</div>\r\ndonaci la vera libertà di spirito.<br/>\r\nPer i tuoi martiri, che confessarono la fede\xa0sino<br/>\r\n\xa0\xa0\xa0all’effusione del sangue,\r\n<div class="lo_rosso"><br/>\r\n–</div>\r\nda’ a noi una fede pura e coerente.<br/>\r\nPer i tuoi martiri, che seguirono le tue orme\xa0sul<br/>\r\n\xa0\xa0\xa0cammino della croce,\r\n<div class="lo_rosso"><br/>\r\n–</div>\r\nfa’ che sosteniamo con fortezza le prove della vita.<br/>\r\nPer i tuoi martiri, che lavarono le vesti nel sangue<br/>\r\n\xa0\xa0\xa0dell’Agnello,\r\n<div class="lo_rosso"><br/>\r\n–</div>\r\ndonaci di vincere le seduzioni della carne e del<br/>\r\n\xa0\xa0\xa0mondo.</div>\r\n\xa0<div class="lo_versetto">Padre nostro.</div>\n<div class="lo_titolo">\n<div class="lo_titolo">ORAZIONE</div>\n</div>\n<div class="lo_versetto">\xa0\xa0 O Dio onnipotente ed eterno, che nel sacrificio dei martiri edifichi la tua Chiesa, mistico corpo del Cristo, fa’ che la gloriosa passione che meritò a sant’Ignazio una corona immortale ci renda sempre forti nella fede. Per il nostro Signore.</div>\n<div class="lo_versetto">Il Signore ci benedica, ci preservi da ogni male e ci conduca alla vita eterna.\r\n<div class="lo_antifona"><br/>\r\nR.</div>\r\n']"""

    # Estrai le lodi
    lodi = estrai_lodi_complete(html_content)

    # Stampa tutto
    stampa_lodi(lodi)

    # Oppure salva in JSON
    import json

    with open('lodi_mattutine.json', 'w', encoding='utf-8') as f:
        json.dump(lodi, f, ensure_ascii=False, indent=2)