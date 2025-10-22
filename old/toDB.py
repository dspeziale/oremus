import json
import sqlite3
import os
from pathlib import Path
from datetime import datetime

DB_PATH = "../instance/oremus.db"
JSON_DIR = "../json"


def init_db():
    """Inizializza il database SQLite con le tabelle necessarie"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabella principale per i giorni liturgici
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS giorni_liturgici (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT UNIQUE NOT NULL,
            data_iso TEXT NOT NULL,
            giorno_settimana TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabella per lodi mattutine
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lodi_mattutine (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            giorno_id INTEGER NOT NULL,
            tipo TEXT,
            titolo TEXT,
            gloria_al_padre TEXT,
            inno TEXT,
            lettura_breve TEXT,
            responsorio_breve TEXT,
            antifona_cantico_finale TEXT,
            cantico_finale TEXT,
            FOREIGN KEY (giorno_id) REFERENCES giorni_liturgici(id)
        )
    ''')

    # Tabella per vespri
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vespri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            giorno_id INTEGER NOT NULL,
            tipo TEXT,
            titolo TEXT,
            gloria_al_padre TEXT,
            inno TEXT,
            lettura_breve TEXT,
            responsorio_breve TEXT,
            antifona_cantico_finale TEXT,
            cantico_finale TEXT,
            FOREIGN KEY (giorno_id) REFERENCES giorni_liturgici(id)
        )
    ''')

    # Tabella per antifone e salmi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS antifone_salmi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lodi_id INTEGER,
            vespri_id INTEGER,
            antifona_numero TEXT,
            antifona_testo TEXT,
            tipo TEXT,
            numero TEXT,
            titolo TEXT,
            contenuto TEXT,
            FOREIGN KEY (lodi_id) REFERENCES lodi_mattutine(id),
            FOREIGN KEY (vespri_id) REFERENCES vespri(id)
        )
    ''')

    # Tabella per invocazioni/intercessioni
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invocazioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            giorno_id INTEGER NOT NULL,
            tipo TEXT,
            contenuto TEXT,
            FOREIGN KEY (giorno_id) REFERENCES giorni_liturgici(id)
        )
    ''')

    # Tabella per orazioni
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orazioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            giorno_id INTEGER NOT NULL,
            tipo TEXT,
            testo TEXT,
            FOREIGN KEY (giorno_id) REFERENCES giorni_liturgici(id)
        )
    ''')

    # Tabella per santi del giorno
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS santi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            giorno_id INTEGER NOT NULL,
            giorno TEXT NOT NULL,
            nome_santo TEXT NOT NULL,
            martirologio TEXT,
            tipo TEXT DEFAULT 'principale',
            FOREIGN KEY (giorno_id) REFERENCES giorni_liturgici(id)
        )
    ''')

    conn.commit()
    conn.close()


def insert_giorno_liturgico(data, data_iso, giorno_settimana):
    """Inserisce o restituisce il giorno liturgico"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO giorni_liturgici (data, data_iso, giorno_settimana)
            VALUES (?, ?, ?)
        ''', (data, data_iso, giorno_settimana))
        conn.commit()
        giorno_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        cursor.execute('SELECT id FROM giorni_liturgici WHERE data_iso = ?', (data_iso,))
        giorno_id = cursor.fetchone()[0]

    conn.close()
    return giorno_id


def insert_lodi(giorno_id, lodi_data):
    """Inserisce i dati delle lodi mattutine"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cantico = lodi_data.get('cantico_finale', {})
    cantico_finale_text = cantico.get('contenuto', '') if isinstance(cantico, dict) else ''

    cursor.execute('''
        INSERT INTO lodi_mattutine 
        (giorno_id, tipo, titolo, gloria_al_padre, inno, lettura_breve, responsorio_breve, antifona_cantico_finale, cantico_finale)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        giorno_id,
        lodi_data.get('tipo'),
        lodi_data.get('titolo'),
        lodi_data.get('gloria_al_padre'),
        lodi_data.get('inno'),
        json.dumps(lodi_data.get('lettura_breve', {})),
        json.dumps(lodi_data.get('responsorio_breve', {})),
        lodi_data.get('antifona_cantico_finale'),
        cantico_finale_text
    ))

    lodi_id = cursor.lastrowid

    # Inserisci antifone e salmi
    for item in lodi_data.get('antifone_e_salmi', []):
        cursor.execute('''
            INSERT INTO antifone_salmi 
            (lodi_id, antifona_numero, antifona_testo, tipo, numero, titolo, contenuto)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            lodi_id,
            item.get('antifona_numero'),
            item.get('antifona_testo'),
            item.get('tipo'),
            item.get('numero'),
            item.get('titolo'),
            item.get('contenuto')
        ))

    # Inserisci invocazioni
    for invocazione in lodi_data.get('invocazioni', []):
        cursor.execute('''
            INSERT INTO invocazioni (giorno_id, tipo, contenuto)
            VALUES (?, ?, ?)
        ''', (giorno_id, 'lodi', invocazione))

    # Inserisci orazione
    if lodi_data.get('orazione'):
        cursor.execute('''
            INSERT INTO orazioni (giorno_id, tipo, testo)
            VALUES (?, ?, ?)
        ''', (giorno_id, 'lodi', lodi_data.get('orazione')))

    conn.commit()
    conn.close()


def insert_vespri(giorno_id, vespri_data):
    """Inserisce i dati dei vespri"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cantico = vespri_data.get('cantico_finale', {})
    cantico_finale_text = cantico.get('contenuto', '') if isinstance(cantico, dict) else ''

    cursor.execute('''
        INSERT INTO vespri 
        (giorno_id, tipo, titolo, gloria_al_padre, inno, lettura_breve, responsorio_breve, antifona_cantico_finale, cantico_finale)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        giorno_id,
        vespri_data.get('tipo'),
        vespri_data.get('titolo'),
        vespri_data.get('gloria_al_padre'),
        vespri_data.get('inno'),
        json.dumps(vespri_data.get('lettura_breve', {})),
        json.dumps(vespri_data.get('responsorio_breve', {})),
        vespri_data.get('antifona_cantico_finale'),
        cantico_finale_text
    ))

    vespri_id = cursor.lastrowid

    # Inserisci antifone e salmi
    for item in vespri_data.get('antifone_e_salmi', []):
        cursor.execute('''
            INSERT INTO antifone_salmi 
            (vespri_id, antifona_numero, antifona_testo, tipo, numero, titolo, contenuto)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            vespri_id,
            item.get('antifona_numero'),
            item.get('antifona_testo'),
            item.get('tipo'),
            item.get('numero'),
            item.get('titolo'),
            item.get('contenuto')
        ))

    # Inserisci intercessioni
    for intercessione in vespri_data.get('intercessioni', []):
        cursor.execute('''
            INSERT INTO invocazioni (giorno_id, tipo, contenuto)
            VALUES (?, ?, ?)
        ''', (giorno_id, 'vespri', intercessione))

    # Inserisci orazione
    if vespri_data.get('orazione'):
        cursor.execute('''
            INSERT INTO orazioni (giorno_id, tipo, testo)
            VALUES (?, ?, ?)
        ''', (giorno_id, 'vespri', vespri_data.get('orazione')))

    conn.commit()
    conn.close()


def insert_santi(giorno_id, santo_data):
    """Inserisce i dati dei santi del giorno"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Santo principale
    if santo_data.get('santo_principale'):
        santo = santo_data['santo_principale']
        cursor.execute('''
            INSERT INTO santi (giorno_id, giorno, nome_santo, martirologio, tipo)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            giorno_id,
            santo_data.get('giorno'),
            santo.get('nome'),
            santo.get('martirologio'),
            'principale'
        ))

    # Altri santi
    for santo in santo_data.get('altri_santi', []):
        cursor.execute('''
            INSERT INTO santi (giorno_id, giorno, nome_santo, martirologio, tipo)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            giorno_id,
            santo_data.get('giorno'),
            santo.get('nome'),
            santo.get('martirologio'),
            'altro'
        ))

    conn.commit()
    conn.close()


def process_json_files():
    """Legge e processa tutti i file JSON"""
    os.makedirs("../instance", exist_ok=True)
    init_db()

    json_files = list(Path(JSON_DIR).glob('liturgia_*.json'))

    if not json_files:
        print(f"Nessun file JSON trovato in {JSON_DIR}")
        return

    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Inserisci il giorno
            giorno_id = insert_giorno_liturgico(
                data.get('data'),
                data.get('data_iso'),
                data.get('giorno_settimana')
            )

            # Inserisci lodi
            if data.get('lodi_mattutine'):
                insert_lodi(giorno_id, data['lodi_mattutine'])

            # Inserisci vespri
            if data.get('vespri'):
                insert_vespri(giorno_id, data['vespri'])

            # Inserisci santi
            if data.get('santo_del_giorno'):
                insert_santi(giorno_id, data['santo_del_giorno'])

            print(f"✓ Elaborato: {json_file.name}")

        except Exception as e:
            print(f"✗ Errore in {json_file.name}: {e}")

    print(f"\n✓ Database creato in: {DB_PATH}")


if __name__ == '__main__':
    process_json_files()