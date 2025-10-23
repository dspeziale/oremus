import sqlite3
import os
from datetime import datetime

# Database path
DB_PATH = 'instance/oremus.db'


def get_table_columns(conn, table_name):
    """Get list of columns for a table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return columns


def migrate_database():
    """Migrate existing database to new schema"""

    if not os.path.exists(DB_PATH):
        print(f"❌ Database non trovato: {DB_PATH}")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔄 Migrazione database in corso...\n")

    try:
        # ============================================
        # VERIFICA E AGGIORNA: lodi_mattutine
        # ============================================
        print("📋 Controllando tabella: lodi_mattutine")
        lodi_columns = get_table_columns(conn, 'lodi_mattutine')
        print(f"   Colonne attuali: {lodi_columns}")

        if 'tipo' not in lodi_columns:
            print("   ➕ Aggiungendo colonna: tipo")
            cursor.execute('ALTER TABLE lodi_mattutine ADD COLUMN tipo TEXT DEFAULT NULL')
            conn.commit()
            print("   ✅ Colonna 'tipo' aggiunta")
        else:
            print("   ✅ Colonna 'tipo' già presente")

        if 'gloria_al_padre' not in lodi_columns:
            print("   ➕ Aggiungendo colonna: gloria_al_padre")
            cursor.execute('ALTER TABLE lodi_mattutine ADD COLUMN gloria_al_padre TEXT DEFAULT NULL')
            conn.commit()
            print("   ✅ Colonna 'gloria_al_padre' aggiunta")

        # ============================================
        # VERIFICA E AGGIORNA: vespri
        # ============================================
        print("\n📋 Controllando tabella: vespri")
        vespri_columns = get_table_columns(conn, 'vespri')
        print(f"   Colonne attuali: {vespri_columns}")

        if 'tipo' not in vespri_columns:
            print("   ➕ Aggiungendo colonna: tipo")
            cursor.execute('ALTER TABLE vespri ADD COLUMN tipo TEXT DEFAULT NULL')
            conn.commit()
            print("   ✅ Colonna 'tipo' aggiunta")
        else:
            print("   ✅ Colonna 'tipo' già presente")

        if 'gloria_al_padre' not in vespri_columns:
            print("   ➕ Aggiungendo colonna: gloria_al_padre")
            cursor.execute('ALTER TABLE vespri ADD COLUMN gloria_al_padre TEXT DEFAULT NULL')
            conn.commit()
            print("   ✅ Colonna 'gloria_al_padre' aggiunta")

        # ============================================
        # VERIFICA E AGGIORNA: santi
        # ============================================
        print("\n📋 Controllando tabella: santi")
        try:
            santi_columns = get_table_columns(conn, 'santi')
            print(f"   Colonne attuali: {santi_columns}")
        except:
            print("   ℹ️  Tabella non esiste, verrà creata")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS santi (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    giorno_id INTEGER NOT NULL,
                    giorno TEXT NOT NULL,
                    nome_santo TEXT NOT NULL,
                    martirologio TEXT,
                    tipo TEXT DEFAULT 'principale',
                    FOREIGN KEY (giorno_id) REFERENCES giorni_liturgici(id) ON DELETE CASCADE
                )
            ''')
            conn.commit()
            print("   ✅ Tabella 'santi' creata")

        # ============================================
        # VERIFICA E AGGIORNA: utenti
        # ============================================
        print("\n📋 Controllando tabella: utenti")
        try:
            utenti_columns = get_table_columns(conn, 'utenti')
            print(f"   Colonne attuali: {utenti_columns}")
        except:
            print("   ℹ️  Tabella non esiste, verrà creata")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS utenti (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    telefono TEXT,
                    ruolo TEXT DEFAULT 'user',
                    is_active BOOLEAN DEFAULT 1,
                    is_verified BOOLEAN DEFAULT 0,
                    data_registrazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultimo_accesso TIMESTAMP,
                    bio TEXT,
                    indirizzo TEXT,
                    citta TEXT,
                    cap TEXT,
                    provincia TEXT,
                    paese TEXT
                )
            ''')
            conn.commit()
            print("   ✅ Tabella 'utenti' creata")

        # ============================================
        # STATISTICHE
        # ============================================
        print("\n" + "=" * 70)
        print("📊 STATISTICHE DATABASE")
        print("=" * 70)

        cursor.execute("SELECT COUNT(*) FROM giorni_liturgici")
        days_count = cursor.fetchone()[0]
        print(f"📅 Giorni liturgici: {days_count}")

        cursor.execute("SELECT COUNT(*) FROM lodi_mattutine")
        lodi_count = cursor.fetchone()[0]
        print(f"🙏 Lodi Mattutine: {lodi_count}")

        cursor.execute("SELECT COUNT(*) FROM vespri")
        vespri_count = cursor.fetchone()[0]
        print(f"🌙 Vespri: {vespri_count}")

        try:
            cursor.execute("SELECT COUNT(*) FROM santi")
            santi_count = cursor.fetchone()[0]
            print(f"✝️  Santi: {santi_count}")
        except:
            print(f"✝️  Santi: N/A")

        try:
            cursor.execute("SELECT COUNT(*) FROM utenti")
            users_count = cursor.fetchone()[0]
            print(f"👥 Utenti: {users_count}")
        except:
            print(f"👥 Utenti: N/A")

        print("=" * 70)

        conn.close()
        print("\n✅ Migrazione completata con successo!\n")
        return True

    except Exception as e:
        print(f"\n❌ Errore durante la migrazione: {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return False


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🔄 MIGRAZIONE DATABASE OREMUS")
    print("=" * 70 + "\n")

    success = migrate_database()

    if success:
        print("🎉 Migrazione completata! Ora puoi eseguire: python app.py\n")
    else:
        print("⚠️  Errore durante la migrazione\n")