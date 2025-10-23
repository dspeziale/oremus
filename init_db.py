import sqlite3
import os
from datetime import datetime, timedelta

# Database path
DB_PATH = 'instance/oremus.db'


def init_database():
    """Initialize database with all tables - FORMATO DATA CORRETTO YYYYMMDD"""

    # Assicurati che la cartella esista
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Se il database esiste già, fai un backup
    if os.path.exists(DB_PATH):
        backup_path = DB_PATH + '.backup'
        print(f"⚠️  Database già esistente!")
        print(f"📦 Creando backup in: {backup_path}")
        os.rename(DB_PATH, backup_path)
        print(f"✅ Backup creato\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("📁 Inizializzazione database...")
    print(f"📍 Percorso: {os.path.abspath(DB_PATH)}\n")

    try:
        # ============================================
        # TABELLA: giorni_liturgici
        # ============================================
        print("📋 Creando tabella: giorni_liturgici")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS giorni_liturgici (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                data_iso TEXT UNIQUE NOT NULL,
                giorno_settimana TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ============================================
        # TABELLA: lodi_mattutine
        # ============================================
        print("📋 Creando tabella: lodi_mattutine")
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

        # ============================================
        # TABELLA: vespri
        # ============================================
        print("📋 Creando tabella: vespri")
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

        # ============================================
        # TABELLA: santi
        # ============================================
        print("📋 Creando tabella: santi")
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

        # ============================================
        # TABELLA: antifone_salmi
        # ============================================
        print("📋 Creando tabella: antifone_salmi")
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

        # ============================================
        # TABELLA: versicoli
        # ============================================
        print("📋 Creando tabella: versicoli")
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

        # ============================================
        # TABELLA: invocazioni
        # ============================================
        print("📋 Creando tabella: invocazioni")
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

        # ============================================
        # TABELLA: orazioni
        # ============================================
        print("📋 Creando tabella: orazioni")
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

        # ============================================
        # TABELLA: utenti
        # ============================================
        print("📋 Creando tabella: utenti")
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
        print("\n✅ Tutte le tabelle create con successo!")

        # # ============================================
        # # INSERISCI DATI DI TEST
        # # ============================================
        # print("\n📝 Inserendo dati di test...\n")
        #
        # # Inserisci utenti di test
        # test_users = [
        #     ('Admin Oremus', 'admin@oremus.it', 'password123', '+39 123 456 7890', 'admin'),
        #     ('Marco Rossi', 'marco@example.com', 'password123', '+39 111 222 3333', 'user'),
        #     ('Giulia Bianchi', 'giulia@example.com', 'password123', '+39 444 555 6666', 'user'),
        #     ('Andrea Verdi', 'andrea@example.com', 'password123', '+39 777 888 9999', 'moderator'),
        #     ('Roberto Neri', 'roberto@example.com', 'password123', '+39 121 212 1212', 'user'),
        # ]
        #
        # for nome, email, password, telefono, ruolo in test_users:
        #     try:
        #         cursor.execute('''
        #             INSERT INTO utenti (nome, email, password, telefono, ruolo, is_active, is_verified)
        #             VALUES (?, ?, ?, ?, ?, 1, 1)
        #         ''', (nome, email, password, telefono, ruolo))
        #         print(f"  ✅ Aggiunto utente: {nome} ({email})")
        #     except sqlite3.IntegrityError:
        #         print(f"  ⚠️  Utente già esiste: {email}")
        #
        # conn.commit()
        #
        # # ============================================
        # # Inserisci giorni liturgici DINAMICI (ultimi 30 giorni + 30 futuri)
        # # ============================================
        # print("\n📅 Generando giorni liturgici (da 30 giorni fa a 30 giorni nel futuro)...\n")
        #
        # giorni_settimana = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
        # mesi = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
        #         'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
        #
        # today = datetime.now()
        # start_date = today - timedelta(days=30)
        # end_date = today + timedelta(days=30)
        #
        # current_date = start_date
        # giorni_creati = 0
        #
        # while current_date <= end_date:
        #     try:
        #         # Formati data
        #         data_iso = current_date.strftime('%Y%m%d')  # 20251023
        #         data_formatted = current_date.strftime('%d') + ' ' + mesi[
        #             current_date.month] + ' ' + current_date.strftime('%Y')
        #         giorno_settimana = giorni_settimana[current_date.weekday()]
        #
        #         cursor.execute('''
        #             INSERT INTO giorni_liturgici (data, data_iso, giorno_settimana)
        #             VALUES (?, ?, ?)
        #         ''', (data_formatted, data_iso, giorno_settimana))
        #
        #         if current_date.day == today.day and current_date.month == today.month and current_date.year == today.year:
        #             print(f"  ✅ Aggiunto giorno: {data_formatted} ({data_iso}) ⭐ OGGI")
        #         elif giorni_creati % 5 == 0:  # Stampa ogni 5 giorni
        #             print(f"  ✅ Aggiunto giorno: {data_formatted} ({data_iso})")
        #
        #         giorni_creati += 1
        #
        #     except sqlite3.IntegrityError:
        #         pass  # Giorno già esiste
        #
        #     current_date += timedelta(days=1)
        #
        # print(f"\n  📊 Totale giorni creati: {giorni_creati}")
        # conn.commit()
        #
        # # Inserisci Lodi Mattutine, Vespri e Santi per oggi
        # cursor.execute("SELECT id FROM giorni_liturgici WHERE data_iso = ?", (today.strftime('%Y%m%d'),))
        # result = cursor.fetchone()
        #
        # if result:
        #     giorno_id = result[0]
        #     print(f"\n📚 Aggiungendo Liturgia per oggi (ID giorno: {giorno_id})...\n")
        #
        #     # Lodi Mattutine
        #     try:
        #         cursor.execute('''
        #             INSERT INTO lodi_mattutine
        #             (giorno_id, tipo, titolo, gloria_al_padre, inno, lettura_breve, responsorio_breve, antifona_cantico_finale, cantico_finale)
        #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        #         ''', (
        #             giorno_id,
        #             'Lodi',
        #             f'Lodi Mattutine - {today.strftime("%A %d %B %Y")}',
        #             'Gloria al Padre e al Figlio e allo Spirito Santo, come era nel principio, e ora e sempre, nei secoli dei secoli. Amen.',
        #             'O Dio, vieni a salvarmi, Signore, vieni in mio aiuto. Sia glorificato il Padre e il Figlio e lo Spirito Santo.',
        #             'Dal Vangelo: In quel tempo, Gesù disse ai suoi discepoli: "Ecco, noi saliremo a Gerusalemme..."',
        #             'V. Ascolta, Signore, la mia voce, R. secondo la tua misericordia.',
        #             'Cantico di Zaccaria',
        #             'Benedetto sia il Signore, Dio d\'Israele, perché ha visitato e redento il suo popolo.'
        #         ))
        #         print(f"  ✅ Aggiunte Lodi Mattutine")
        #     except Exception as e:
        #         print(f"  ⚠️  Errore Lodi: {e}")
        #
        #     # Vespri
        #     try:
        #         cursor.execute('''
        #             INSERT INTO vespri
        #             (giorno_id, tipo, titolo, gloria_al_padre, inno, lettura_breve, responsorio_breve, antifona_cantico_finale, cantico_finale)
        #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        #         ''', (
        #             giorno_id,
        #             'Vespri',
        #             f'Vespri - {today.strftime("%A %d %B %Y")}',
        #             'Gloria al Padre e al Figlio e allo Spirito Santo, come era nel principio, e ora e sempre, nei secoli dei secoli. Amen.',
        #             'O luce serena della gloria del Padre, divina sapienza, aiutaci a camminar verso la luce e preservaci dall\'errore di questa notte.',
        #             'Dal libro della Lettera ai Romani (12, 9-21): La carità non sia falsa. Abhorrire il male, restare attaccati al bene.',
        #             'V. Ti lodiamo, Signore, R. con tutto il cuore.',
        #             'Magnificat',
        #             'Magnificat anima mea Dominum et exultavit spiritus meus in Deo salutari meo.'
        #         ))
        #         print(f"  ✅ Aggiunti Vespri")
        #     except Exception as e:
        #         print(f"  ⚠️  Errore Vespri: {e}")
        #
        #     # Santo del Giorno
        #     try:
        #         cursor.execute('''
        #             INSERT INTO santi (giorno_id, giorno, nome_santo, martirologio, tipo)
        #             VALUES (?, ?, ?, ?, ?)
        #         ''', (
        #             giorno_id,
        #             today.strftime('%d %B'),
        #             'Santo del Giorno',
        #             'Memoria di un santo celebre della Chiesa Cattolica.',
        #             'principale'
        #         ))
        #         print(f"  ✅ Aggiunto Santo del Giorno")
        #     except Exception as e:
        #         print(f"  ⚠️  Errore Santo: {e}")
        #
        #     conn.commit()

        # Statistiche finali
        print("\n" + "=" * 70)
        print("📊 STATISTICHE DATABASE")
        print("=" * 70)

        cursor.execute("SELECT COUNT(*) FROM utenti")
        users_count = cursor.fetchone()[0]
        print(f"👥 Utenti: {users_count}")

        cursor.execute("SELECT COUNT(*) FROM giorni_liturgici")
        days_count = cursor.fetchone()[0]
        print(f"📅 Giorni liturgici: {days_count}")

        cursor.execute("SELECT COUNT(*) FROM lodi_mattutine")
        lodi_count = cursor.fetchone()[0]
        print(f"🙏 Lodi Mattutine: {lodi_count}")

        cursor.execute("SELECT COUNT(*) FROM vespri")
        vespri_count = cursor.fetchone()[0]
        print(f"🌙 Vespri: {vespri_count}")

        cursor.execute("SELECT COUNT(*) FROM santi")
        santi_count = cursor.fetchone()[0]
        print(f"✝️  Santi: {santi_count}")

        print("=" * 70)

        conn.close()
        print("\n✅ Database inizializzato con successo!\n")
        return True

    except Exception as e:
        print(f"\n❌ Errore durante l'inizializzazione: {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return False


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🗄️  INIZIALIZZAZIONE DATABASE OREMUS - FORMATO DATA CORRETTO (YYYYMMDD)")
    print("=" * 70 + "\n")

    success = init_database()

    if success:
        print("\n🎉 Database pronto!\n")
        print("📋 Dati di test aggiunti:")
        print("   👤 Admin: admin@oremus.it / password123")
        print("   👤 User1: marco@example.com / password123")
        print("   👤 User2: giulia@example.com / password123")
        print("   👤 User3: andrea@example.com / password123")
        print("   👤 User4: roberto@example.com / password123")
        print("\n📅 Giorni liturgici: Ultimi 30 giorni + 30 giorni futuri")
        print("📍 Data odierna inclusa nella sequenza")
        print("\n💡 Prossimo comando: python app3.py\n")
    else:
        print("\n⚠️  Errore nell'inizializzazione del database\n")