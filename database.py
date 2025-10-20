#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database SQLite per OREMUS - Gestione completa della Liturgia delle Ore
"""
import sqlite3
import os
from datetime import datetime
from pathlib import Path


class OremusDB:
    """Gestione database SQLite per Oremus"""

    DB_PATH = "instance/oremus.db"

    def __init__(self):
        """Inizializza connessione e crea tabelle se necessario"""
        os.makedirs("instance", exist_ok=True)
        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Connessione al database"""
        self.conn = sqlite3.connect(self.DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def close(self):
        """Chiude connessione"""
        if self.conn:
            self.conn.close()

    def create_tables(self):
        """Crea tabelle del database"""
        cursor = self.conn.cursor()

        # Tabella Date
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS date (
                id INTEGER PRIMARY KEY,
                data TEXT UNIQUE NOT NULL,
                data_formattata TEXT,
                giorno_settimana TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabella Santo del Giorno
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS santo_giorno (
                id INTEGER PRIMARY KEY,
                data_id INTEGER UNIQUE NOT NULL,
                santo_principale TEXT,
                numero_santi INTEGER,
                testo_completo TEXT,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(data_id) REFERENCES date(id)
            )
        ''')

        # Tabella Santi Commemorati
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS santo_commemorato (
                id INTEGER PRIMARY KEY,
                santo_giorno_id INTEGER NOT NULL,
                ordine INTEGER,
                nome TEXT,
                martirologio TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(santo_giorno_id) REFERENCES santo_giorno(id) ON DELETE CASCADE
            )
        ''')

        # Tabella Liturgia del Giorno
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS liturgia_giorno (
                id INTEGER PRIMARY KEY,
                data_id INTEGER UNIQUE NOT NULL,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(data_id) REFERENCES date(id)
            )
        ''')

        # Tabella Letture Liturgiche
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lettura_liturgica (
                id INTEGER PRIMARY KEY,
                liturgia_giorno_id INTEGER NOT NULL,
                tipo TEXT,
                riferimento TEXT,
                testo TEXT,
                ordine INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(liturgia_giorno_id) REFERENCES liturgia_giorno(id) ON DELETE CASCADE
            )
        ''')

        # Tabella Lodi Mattutine
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lodi_mattutine (
                id INTEGER PRIMARY KEY,
                data_id INTEGER UNIQUE NOT NULL,
                introduzione TEXT,
                inno TEXT,
                responsorio_breve TEXT,
                orazione TEXT,
                conclusione TEXT,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(data_id) REFERENCES date(id)
            )
        ''')

        # Tabella Salmodia Lodi
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS salmodia_lodi (
                id INTEGER PRIMARY KEY,
                lodi_mattutine_id INTEGER NOT NULL,
                numero INTEGER,
                antifona_inizio TEXT,
                titolo TEXT,
                testo TEXT,
                ordine INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(lodi_mattutine_id) REFERENCES lodi_mattutine(id) ON DELETE CASCADE
            )
        ''')

        # Tabella Lettura Breve Lodi
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lettura_breve_lodi (
                id INTEGER PRIMARY KEY,
                lodi_mattutine_id INTEGER UNIQUE NOT NULL,
                riferimento TEXT,
                testo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(lodi_mattutine_id) REFERENCES lodi_mattutine(id) ON DELETE CASCADE
            )
        ''')

        # Tabella Cantico Evangelico Lodi
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cantico_lodi (
                id INTEGER PRIMARY KEY,
                lodi_mattutine_id INTEGER UNIQUE NOT NULL,
                testo TEXT,
                dossologia TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(lodi_mattutine_id) REFERENCES lodi_mattutine(id) ON DELETE CASCADE
            )
        ''')

        # Tabella Vespri
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vespri (
                id INTEGER PRIMARY KEY,
                data_id INTEGER UNIQUE NOT NULL,
                introduzione TEXT,
                inno TEXT,
                responsorio_breve TEXT,
                orazione TEXT,
                conclusione TEXT,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(data_id) REFERENCES date(id)
            )
        ''')

        # Tabella Salmodia Vespri
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS salmodia_vespri (
                id INTEGER PRIMARY KEY,
                vespri_id INTEGER NOT NULL,
                numero INTEGER,
                antifona_inizio TEXT,
                titolo TEXT,
                testo TEXT,
                ordine INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(vespri_id) REFERENCES vespri(id) ON DELETE CASCADE
            )
        ''')

        # Tabella Lettura Breve Vespri
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lettura_breve_vespri (
                id INTEGER PRIMARY KEY,
                vespri_id INTEGER UNIQUE NOT NULL,
                riferimento TEXT,
                testo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(vespri_id) REFERENCES vespri(id) ON DELETE CASCADE
            )
        ''')

        # Tabella Cantico Evangelico Vespri (Magnificat)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cantico_vespri (
                id INTEGER PRIMARY KEY,
                vespri_id INTEGER UNIQUE NOT NULL,
                riferimento TEXT,
                sottotitolo TEXT,
                antifona TEXT,
                testo TEXT,
                dossologia TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(vespri_id) REFERENCES vespri(id) ON DELETE CASCADE
            )
        ''')

        # Tabella Log Estrazione
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS extraction_log (
                id INTEGER PRIMARY KEY,
                data TEXT,
                script TEXT,
                status TEXT,
                messaggio TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()

    def get_or_create_date(self, data, data_formattata="", santo_principale=""):
        """Ottiene o crea record data con santo principale incluso nella data_formattata"""
        cursor = self.conn.cursor()

        try:
            cursor.execute('SELECT id FROM date WHERE data = ?', (data,))
            row = cursor.fetchone()
            if row:
                # Se già esiste e abbiamo un santo, aggiorna la data_formattata
                if santo_principale:
                    cursor.execute('''
                        UPDATE date SET data_formattata = ? WHERE data = ?
                    ''', (f"{data_formattata}: {santo_principale}", data))
                    self.conn.commit()
                return row[0]

            from datetime import datetime
            dt = datetime.strptime(data, "%Y%m%d")
            giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
            giorno_settimana = giorni[dt.weekday()]

            # Costruisci la data_formattata con il santo
            if santo_principale:
                data_fmt_completa = f"{data_formattata}: {santo_principale}"
            else:
                data_fmt_completa = data_formattata

            cursor.execute('''
                INSERT INTO date (data, data_formattata, giorno_settimana)
                VALUES (?, ?, ?)
            ''', (data, data_fmt_completa, giorno_settimana))

            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"❌ Errore get_or_create_date: {e}")
            return None

    def save_santo_giorno(self, data_dict):
        """Salva Santo del Giorno e santi commemorati con nome e martirologio separati"""
        try:
            # Ottieni data formattata
            data = data_dict['data']
            data_formattata = data_dict.get('data_formattata', '')
            santo_principale = data_dict.get('santo_principale', '')

            # Crea/aggiorna la data con il santo nel nome
            date_id = self.get_or_create_date(data, data_formattata, santo_principale)

            if not date_id:
                print(f"❌ Errore: impossibile creare/trovare data")
                return False

            cursor = self.conn.cursor()

            santi_commemorati = data_dict.get('santi_commemorati', [])

            print(f"💾 Salvando santo: {santo_principale} con {len(santi_commemorati)} commemorati")

            # Salva santo principale
            cursor.execute('''
                INSERT OR REPLACE INTO santo_giorno 
                (data_id, santo_principale, numero_santi, testo_completo, url)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                date_id,
                santo_principale,
                len(santi_commemorati),
                data_dict.get('testo_completo', ''),
                data_dict.get('url', '')
            ))

            santo_id = cursor.lastrowid

            # Salva santi commemorati con nome e martirologio separati
            for i, santo_item in enumerate(santi_commemorati):
                # Gestisce sia formato dict che stringa
                if isinstance(santo_item, dict):
                    nome = santo_item.get('nome', '')
                    martirologio = santo_item.get('martirologio', '')
                else:
                    # Se è stringa, usa come nome
                    nome = str(santo_item)
                    martirologio = ''

                if nome.strip():  # Solo se c'è un nome
                    cursor.execute('''
                        INSERT INTO santo_commemorato (santo_giorno_id, ordine, nome, martirologio)
                        VALUES (?, ?, ?, ?)
                    ''', (santo_id, i + 1, nome, martirologio))
                    print(f"  ✓ Commemorato {i + 1}: {nome}")

            self.conn.commit()
            print(f"✅ Santo salvato con successo")
            return True
        except Exception as e:
            print(f"❌ Errore save_santo_giorno: {e}")
            import traceback
            traceback.print_exc()
            return False

    def save_liturgia_giorno(self, data_dict):
        """Salva Liturgia del Giorno e letture"""
        try:
            date_id = self.get_or_create_date(data_dict['data'])
            if not date_id:
                return False

            cursor = self.conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO liturgia_giorno (data_id, url)
                VALUES (?, ?)
            ''', (date_id, data_dict.get('url', '')))

            liturgia_id = cursor.lastrowid

            ordine = 0
            for sezione, contenuto in data_dict.get('sezioni', {}).items():
                cursor.execute('''
                    INSERT INTO lettura_liturgica 
                    (liturgia_giorno_id, tipo, riferimento, testo, ordine)
                    VALUES (?, ?, ?, ?, ?)
                ''', (liturgia_id, sezione, '', contenuto, ordine))
                ordine += 1

            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ Errore save_liturgia_giorno: {e}")
            return False

    def save_lodi_mattutine(self, data_dict):
        """Salva Lodi Mattutine complete"""
        try:
            date_id = self.get_or_create_date(data_dict['data'], data_dict.get('data_formattata', ''))
            if not date_id:
                return False

            cursor = self.conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO lodi_mattutine
                (data_id, introduzione, inno, responsorio_breve, orazione, conclusione, url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                date_id,
                data_dict.get('introduzione', ''),
                data_dict.get('inno', ''),
                data_dict.get('responsorio_breve', ''),
                data_dict.get('orazione', ''),
                data_dict.get('conclusione', ''),
                data_dict.get('url', '')
            ))

            lodi_id = cursor.lastrowid

            # Salva salmodia
            for salmo in data_dict.get('salmodia', []):
                cursor.execute('''
                    INSERT INTO salmodia_lodi
                    (lodi_mattutine_id, numero, antifona_inizio, titolo, testo, ordine)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    lodi_id,
                    salmo.get('numero', 0),
                    salmo.get('antifona_inizio', ''),
                    salmo.get('titolo', ''),
                    salmo.get('testo', ''),
                    salmo.get('numero', 0)
                ))

            # Salva lettura breve
            lettura_breve = data_dict.get('lettura_breve', {})
            if lettura_breve:
                cursor.execute('''
                    INSERT INTO lettura_breve_lodi
                    (lodi_mattutine_id, riferimento, testo)
                    VALUES (?, ?, ?)
                ''', (
                    lodi_id,
                    lettura_breve.get('riferimento', ''),
                    lettura_breve.get('testo', '')
                ))

            # Salva cantico evangelico
            cantico = data_dict.get('cantico_evangelico', {})
            if cantico:
                cursor.execute('''
                    INSERT INTO cantico_lodi
                    (lodi_mattutine_id, testo, dossologia)
                    VALUES (?, ?, ?)
                ''', (
                    lodi_id,
                    cantico.get('testo', ''),
                    cantico.get('dossologia', '')
                ))

            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ Errore save_lodi_mattutine: {e}")
            return False

    def save_vespri(self, data_dict):
        """Salva Vespri complete"""
        try:
            date_id = self.get_or_create_date(data_dict['data'], data_dict.get('data_formattata', ''))
            if not date_id:
                return False

            cursor = self.conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO vespri
                (data_id, introduzione, inno, responsorio_breve, orazione, conclusione, url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                date_id,
                data_dict.get('introduzione', ''),
                data_dict.get('inno', ''),
                data_dict.get('responsorio_breve', ''),
                data_dict.get('orazione', ''),
                data_dict.get('conclusione', ''),
                data_dict.get('url', '')
            ))

            vespri_id = cursor.lastrowid

            # Salva salmodia
            for salmo in data_dict.get('salmodia', []):
                cursor.execute('''
                    INSERT INTO salmodia_vespri
                    (vespri_id, numero, antifona_inizio, titolo, testo, ordine)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    vespri_id,
                    salmo.get('numero', 0),
                    salmo.get('antifona_inizio', ''),
                    salmo.get('titolo', ''),
                    salmo.get('testo', ''),
                    salmo.get('numero', 0)
                ))

            # Salva lettura breve
            lettura_breve = data_dict.get('lettura_breve', {})
            if lettura_breve:
                cursor.execute('''
                    INSERT INTO lettura_breve_vespri
                    (vespri_id, riferimento, testo)
                    VALUES (?, ?, ?)
                ''', (
                    vespri_id,
                    lettura_breve.get('riferimento', ''),
                    lettura_breve.get('testo', '')
                ))

            # Salva cantico evangelico (Magnificat)
            cantico = data_dict.get('cantico_evangelico', {})
            if cantico:
                cursor.execute('''
                    INSERT INTO cantico_vespri
                    (vespri_id, riferimento, sottotitolo, antifona, testo, dossologia)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    vespri_id,
                    cantico.get('riferimento', ''),
                    cantico.get('sottotitolo', ''),
                    cantico.get('antifona', ''),
                    cantico.get('testo', ''),
                    cantico.get('dossologia', '')
                ))

            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ Errore save_vespri: {e}")
            return False

    def log_extraction(self, data, script, status, messaggio):
        """Registra log estrazione"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO extraction_log (data, script, status, messaggio)
                VALUES (?, ?, ?, ?)
            ''', (data, script, status, messaggio))
            self.conn.commit()
        except Exception as e:
            print(f"❌ Errore log_extraction: {e}")


if __name__ == "__main__":
    db = OremusDB()
    print("✅ Database creato con successo!")
    db.close()