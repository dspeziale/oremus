import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

# Importa le classi dal lrgyParser
from old.lrgyParser import LiturgiaManager, LodiParser, VespriParser, SantoParser

class LiturgiaDBManager:
    """Manager per salvare i dati liturgici in SQLite"""

    def __init__(self, db_path: str = "instance/oremus.db"):
        self.db_path = db_path
        self._ensure_db_dir()
        self.init_db()

    def _ensure_db_dir(self):
        """Assicura che la cartella instance esista"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def init_db(self):
        """Inizializza il database SQLite con le tabelle necessarie"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabella principale per i giorni liturgici
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS giorni_liturgici (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                data_iso TEXT UNIQUE NOT NULL,
                giorno_settimana TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                FOREIGN KEY (giorno_id) REFERENCES giorni_liturgici(id) ON DELETE CASCADE
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
                FOREIGN KEY (giorno_id) REFERENCES giorni_liturgici(id) ON DELETE CASCADE
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
                FOREIGN KEY (lodi_id) REFERENCES lodi_mattutine(id) ON DELETE CASCADE,
                FOREIGN KEY (vespri_id) REFERENCES vespri(id) ON DELETE CASCADE
            )
        ''')

        # Tabella per versicoli
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS versicoli (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lodi_id INTEGER,
                vespri_id INTEGER,
                versicolo TEXT,
                risposta TEXT,
                FOREIGN KEY (lodi_id) REFERENCES lodi_mattutine(id) ON DELETE CASCADE,
                FOREIGN KEY (vespri_id) REFERENCES vespri(id) ON DELETE CASCADE
            )
        ''')

        # Tabella per invocazioni/intercessioni
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invocazioni (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                giorno_id INTEGER NOT NULL,
                lodi_id INTEGER,
                vespri_id INTEGER,
                tipo TEXT,
                contenuto TEXT,
                FOREIGN KEY (giorno_id) REFERENCES giorni_liturgici(id) ON DELETE CASCADE,
                FOREIGN KEY (lodi_id) REFERENCES lodi_mattutine(id) ON DELETE CASCADE,
                FOREIGN KEY (vespri_id) REFERENCES vespri(id) ON DELETE CASCADE
            )
        ''')

        # Tabella per orazioni
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orazioni (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                giorno_id INTEGER NOT NULL,
                lodi_id INTEGER,
                vespri_id INTEGER,
                tipo TEXT,
                testo TEXT,
                FOREIGN KEY (giorno_id) REFERENCES giorni_liturgici(id) ON DELETE CASCADE,
                FOREIGN KEY (lodi_id) REFERENCES lodi_mattutine(id) ON DELETE CASCADE,
                FOREIGN KEY (vespri_id) REFERENCES vespri(id) ON DELETE CASCADE
            )
        ''')

        # Tabella per santi del giorno - FIXED
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS santi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                giorno_id INTEGER NOT NULL,
                giorno TEXT NOT NULL,
                nome_santo TEXT NOT NULL,
                martirologio TEXT,
                tipo TEXT DEFAULT 'principale',
                santo_principale TEXT,
                FOREIGN KEY (giorno_id) REFERENCES giorni_liturgici(id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        conn.close()

    def get_or_create_giorno(self, data: str, data_iso: str, giorno_settimana: str) -> int:
        """Ottiene o crea il record del giorno liturgico"""
        conn = sqlite3.connect(self.db_path)
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
            result = cursor.fetchone()
            giorno_id = result[0] if result else None
            if not giorno_id:
                raise ValueError(f"Impossibile ottenere giorno per {data_iso}")

        conn.close()
        return giorno_id

    def insert_lodi(self, giorno_id: int, lodi_data: Dict) -> Optional[int]:
        """Inserisce i dati delle lodi mattutine"""
        if not lodi_data:
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
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

            # Versicoli
            for versicolo in lodi_data.get('versicoli', []):
                cursor.execute('''
                    INSERT INTO versicoli (lodi_id, versicolo, risposta)
                    VALUES (?, ?, ?)
                ''', (lodi_id, versicolo.get('versicolo'), versicolo.get('risposta')))

            # Antifone e salmi
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

            # Invocazioni
            for invocazione in lodi_data.get('invocazioni', []):
                cursor.execute('''
                    INSERT INTO invocazioni (giorno_id, lodi_id, tipo, contenuto)
                    VALUES (?, ?, ?, ?)
                ''', (giorno_id, lodi_id, 'lodi', invocazione))

            # Orazione
            if lodi_data.get('orazione'):
                cursor.execute('''
                    INSERT INTO orazioni (giorno_id, lodi_id, tipo, testo)
                    VALUES (?, ?, ?, ?)
                ''', (giorno_id, lodi_id, 'lodi', lodi_data.get('orazione')))

            conn.commit()
            return lodi_id
        finally:
            conn.close()

    def insert_vespri(self, giorno_id: int, vespri_data: Dict) -> Optional[int]:
        """Inserisce i dati dei vespri"""
        if not vespri_data:
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
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

            # Versicoli
            for versicolo in vespri_data.get('versicoli', []):
                cursor.execute('''
                    INSERT INTO versicoli (vespri_id, versicolo, risposta)
                    VALUES (?, ?, ?)
                ''', (vespri_id, versicolo.get('versicolo'), versicolo.get('risposta')))

            # Antifone e salmi
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

            # Intercessioni
            for intercessione in vespri_data.get('intercessioni', []):
                cursor.execute('''
                    INSERT INTO invocazioni (giorno_id, vespri_id, tipo, contenuto)
                    VALUES (?, ?, ?, ?)
                ''', (giorno_id, vespri_id, 'vespri', intercessione))

            # Orazione
            if vespri_data.get('orazione'):
                cursor.execute('''
                    INSERT INTO orazioni (giorno_id, vespri_id, tipo, testo)
                    VALUES (?, ?, ?, ?)
                ''', (giorno_id, vespri_id, 'vespri', vespri_data.get('orazione')))

            conn.commit()
            return vespri_id
        finally:
            conn.close()

    def insert_santi(self, giorno_id: int, santo_data: Dict):
        """Inserisce i dati dei santi del giorno"""
        if not santo_data:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Santo principale
            if santo_data.get('santo_principale'):
                santo = santo_data['santo_principale']
                cursor.execute('''
                    INSERT INTO santi (giorno_id, giorno, nome_santo, martirologio, tipo, santo_principale)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    giorno_id,
                    santo_data.get('giorno'),
                    santo.get('nome'),
                    santo.get('martirologio'),
                    'principale',
                    santo.get('nome')
                ))

            # Altri santi
            for santo in santo_data.get('altri_santi', []):
                cursor.execute('''
                    INSERT INTO santi (giorno_id, giorno, nome_santo, martirologio, tipo, santo_principale)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    giorno_id,
                    santo_data.get('giorno'),
                    santo.get('nome'),
                    santo.get('martirologio'),
                    'altro',
                    None
                ))

            conn.commit()
        finally:
            conn.close()

    def save_liturgia_data(self, data: Dict) -> bool:
        """Salva un giorno liturgico completo nel database"""
        try:
            giorno_id = self.get_or_create_giorno(
                data.get('data'),
                data.get('data_iso'),
                data.get('giorno_settimana')
            )

            self.insert_lodi(giorno_id, data.get('lodi_mattutine'))
            self.insert_vespri(giorno_id, data.get('vespri'))
            self.insert_santi(giorno_id, data.get('santo_del_giorno'))

            return True
        except Exception as e:
            print(f"✗ Errore nel salvataggio: {e}")
            return False


class LiturgiaParserWithDB(LiturgiaManager):
    """Estende LiturgiaManager per salvare automaticamente in SQLite"""

    def __init__(self, output_dir: str = "json", db_path: str = "instance/oremus.db"):
        super().__init__(output_dir)
        self.db_manager = LiturgiaDBManager(db_path)

    def save_json(self, data: Dict, filename: str) -> bool:
        """Salva JSON e contemporaneamente nel database"""
        # Salva il JSON
        json_saved = super().save_json(data, filename)

        # Salva nel database
        if json_saved:
            db_saved = self.db_manager.save_liturgia_data(data)
            if db_saved:
                print(f"✅ Salvato in DB: {data.get('data_iso')}")
            else:
                print(f"⚠️  JSON salvato ma DB fallito per {data.get('data_iso')}")
            return db_saved

        return False

    def get_date_range(self, start_date: str, end_date: str):
        """Override per aggiungere il salvataggio in DB"""
        print(f"\n📖 Scaricamento dati da {start_date} a {end_date}...")
        super().get_date_range(start_date, end_date)


if __name__ == "__main__":
    manager = LiturgiaParserWithDB()

    print("=" * 70)
    print("📖 PARSER LITURGIA + SQLITE DATABASE")
    print("=" * 70)

    # Elabora un intervallo di date
    manager.get_date_range("20251001", "20251130")

    print("\n" + "=" * 70)
    print(f"✨ Database salvato in: instance/oremus.db")
    print("=" * 70)