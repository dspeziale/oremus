# ============================================
# NORMALIZZAZIONE DATABASE - Query SQLite
# ============================================
# ⚠️ IMPORTANTE: L'app usa SQLite DIRETTO, non SQLAlchemy
#
# Questo file fornisce le correzioni per:
# 1. Rimuovere db.session.query()
# 2. Usare sqlite3 come in get_giorno_by_data()
# 3. Normalizzare i nomi delle tabelle
# ============================================

import sqlite3
import os
from datetime import datetime


# ============================================
# HELPER FUNCTIONS - Usa il pattern dell'app
# ============================================

def get_db_connection():
    """Get SQLite database connection"""
    DB_PATH = 'instance/oremus.db'
    try:
        if not os.path.exists(DB_PATH):
            print(f"❌ Database non esiste: {DB_PATH}")
            return None

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ Errore connessione DB: {e}")
        return None


def dict_from_row(row):
    """Convert sqlite3.Row to dict"""
    if row is None:
        return None
    return dict(row)


# ============================================
# CORRETTI - FUNZIONI DA USARE
# ============================================

def get_dashboard_stats():
    """✅ CORRETTO - API per statistiche dashboard"""
    try:
        conn = get_db_connection()
        if conn is None:
            return {'error': 'Database non disponibile'}

        cursor = conn.cursor()

        # Giorni totali
        cursor.execute('SELECT COUNT(*) as count FROM giorni_liturgici')
        total_days = cursor.fetchone()['count']

        # Utenti (se esiste tabella)
        try:
            cursor.execute('SELECT COUNT(*) as count FROM utenti')
            total_users = cursor.fetchone()['count']
        except:
            total_users = 0

        # Celebrazioni (Lodi + Vespri)
        cursor.execute('SELECT COUNT(*) as count FROM lodi_mattutine')
        lodi_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM vespri')
        vespri_count = cursor.fetchone()['count']

        total_prayers = lodi_count + vespri_count

        # Nuovi utenti questa settimana (se esiste)
        try:
            cursor.execute('''
                SELECT COUNT(*) as count FROM utenti 
                WHERE datetime(data_registrazione) >= datetime('now', '-7 days')
            ''')
            new_users = cursor.fetchone()['count']
        except:
            new_users = 0

        conn.close()

        return {
            'total_days': total_days,
            'total_users': total_users,
            'total_prayers': total_prayers,
            'new_users': new_users
        }

    except Exception as e:
        print(f"Errore statistiche: {e}")
        return {'error': str(e)}


def get_dashboard_giorni():
    """✅ CORRETTO - API per lista giorni con santi"""
    try:
        conn = get_db_connection()
        if conn is None:
            return {'error': 'Database non disponibile'}

        cursor = conn.cursor()

        # Recupera tutti i giorni
        cursor.execute('''
            SELECT id, data, data_iso, giorno_settimana 
            FROM giorni_liturgici 
            ORDER BY data_iso DESC
        ''')

        risultati = []
        for row in cursor.fetchall():
            giorno = dict_from_row(row)

            # Prendi il santo principale per questo giorno
            cursor.execute('''
                SELECT nome_santo 
                FROM santi 
                WHERE giorno_id = ? AND tipo = 'principale'
                LIMIT 1
            ''', (giorno['id'],))

            santo_row = cursor.fetchone()
            santo_principale = dict_from_row(santo_row)['nome_santo'] if santo_row else None

            risultati.append({
                'id': giorno['id'],
                'data': giorno['data'],
                'data_iso': giorno['data_iso'],
                'giorno_settimana': giorno['giorno_settimana'],
                'santo_principale': santo_principale
            })

        conn.close()
        return {'giorni': risultati}

    except Exception as e:
        print(f"Errore giorni: {e}")
        return {'error': str(e)}


def get_giorno_id_by_iso_date(date_iso):
    """✅ CORRETTO - Recupera ID giorno dalla data ISO"""
    try:
        conn = get_db_connection()
        if conn is None:
            return None

        cursor = conn.cursor()

        # Prova prima con data_iso, poi con fallback
        cursor.execute('''
            SELECT id FROM giorni_liturgici 
            WHERE data_iso = ? OR data = ?
            LIMIT 1
        ''', (date_iso, date_iso))

        row = cursor.fetchone()
        conn.close()

        return row['id'] if row else None

    except Exception as e:
        print(f"Errore get_giorno_id_by_iso_date: {e}")
        return None


def get_lodi_by_giorno(giorno_id):
    """✅ CORRETTO - Recupera lodi per un giorno"""
    try:
        conn = get_db_connection()
        if conn is None:
            return None

        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM lodi_mattutine WHERE giorno_id = ?
        ''', (giorno_id,))

        row = cursor.fetchone()
        conn.close()

        return dict_from_row(row)

    except Exception as e:
        print(f"Errore get_lodi_by_giorno: {e}")
        return None


def get_vespri_by_giorno(giorno_id):
    """✅ CORRETTO - Recupera vespri per un giorno"""
    try:
        conn = get_db_connection()
        if conn is None:
            return None

        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM vespri WHERE giorno_id = ?
        ''', (giorno_id,))

        row = cursor.fetchone()
        conn.close()

        return dict_from_row(row)

    except Exception as e:
        print(f"Errore get_vespri_by_giorno: {e}")
        return None


def get_santi_by_giorno(giorno_id):
    """✅ CORRETTO - Recupera santi per un giorno"""
    try:
        conn = get_db_connection()
        if conn is None:
            return []

        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM santi WHERE giorno_id = ? 
            ORDER BY tipo DESC, nome_santo ASC
        ''', (giorno_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict_from_row(row) for row in rows]

    except Exception as e:
        print(f"Errore get_santi_by_giorno: {e}")
        return []


def get_giorno_completo(date_iso):
    """✅ CORRETTO - Recupera tutti i dati di un giorno (versione corretta)"""
    try:
        conn = get_db_connection()
        if conn is None:
            return None

        cursor = conn.cursor()

        # Recupera il giorno
        cursor.execute('''
            SELECT * FROM giorni_liturgici 
            WHERE data_iso = ? OR data = ?
        ''', (date_iso, date_iso))

        giorno_row = cursor.fetchone()

        if not giorno_row:
            conn.close()
            return None

        giorno = dict_from_row(giorno_row)
        giorno_id = giorno['id']

        # Recupera lodi
        cursor.execute('SELECT * FROM lodi_mattutine WHERE giorno_id = ?', (giorno_id,))
        lodi = dict_from_row(cursor.fetchone())

        # Recupera vespri
        cursor.execute('SELECT * FROM vespri WHERE giorno_id = ?', (giorno_id,))
        vespri = dict_from_row(cursor.fetchone())

        # Recupera santi
        cursor.execute(
            'SELECT * FROM santi WHERE giorno_id = ? ORDER BY tipo DESC',
            (giorno_id,)
        )
        santi = [dict_from_row(row) for row in cursor.fetchall()]

        conn.close()

        return {
            'giorno': giorno,
            'lodi': lodi,
            'vespri': vespri,
            'santi': santi,
            'giorno_id': giorno_id
        }

    except Exception as e:
        print(f"Errore get_giorno_completo: {e}")
        return None


# ============================================
# ROUTE CORRETTE - Sostituisci le vecchie
# ============================================

# ✅ CORRETTO - Sostituisci la route /api/dashboard/stats
"""
@app.route('/api/dashboard/stats')
def dashboard_stats():
    return jsonify(get_dashboard_stats())
"""

# ✅ CORRETTO - Sostituisci la route /api/dashboard/giorni
"""
@app.route('/api/dashboard/giorni')
def dashboard_giorni():
    return jsonify(get_dashboard_giorni())
"""

# ✅ CORRETTO - Sostituisci la route /lodi
"""
@app.route('/lodi')
def lodi():
    try:
        date_param = request.args.get('date')

        if date_param:
            giorno_id = get_giorno_id_by_iso_date(date_param)
            if not giorno_id:
                return render_template('error.html', message="Data non trovata nel calendario"), 404
        else:
            today = datetime.now().strftime('%Y%m%d')
            giorno_id = get_giorno_id_by_iso_date(today)
            if not giorno_id:
                return render_template('error.html', message="Dati non disponibili per oggi"), 404

        # ✅ CORRETTO - Usa le funzioni qui
        lodi = get_lodi_by_giorno(giorno_id)
        giorno_data = get_giorno_completo(date_param or datetime.now().strftime('%Y%m%d'))
        giorno = giorno_data['giorno'] if giorno_data else None

        return render_template('lodi.html', lodi=lodi, giorno=giorno)
    except Exception as e:
        print(f"Errore Lodi: {e}")
        return render_template('error.html', message=f"Errore nel caricamento delle Lodi: {str(e)}"), 500
"""

# ✅ CORRETTO - Sostituisci la route /vespri
"""
@app.route('/vespri')
def vespri():
    try:
        date_param = request.args.get('date')

        if date_param:
            giorno_id = get_giorno_id_by_iso_date(date_param)
            if not giorno_id:
                return render_template('error.html', message="Data non trovata nel calendario"), 404
        else:
            today = datetime.now().strftime('%Y%m%d')
            giorno_id = get_giorno_id_by_iso_date(today)
            if not giorno_id:
                return render_template('error.html', message="Dati non disponibili per oggi"), 404

        # ✅ CORRETTO - Usa le funzioni qui
        vespri = get_vespri_by_giorno(giorno_id)
        giorno_data = get_giorno_completo(date_param or datetime.now().strftime('%Y%m%d'))
        giorno = giorno_data['giorno'] if giorno_data else None

        return render_template('vespri.html', vespri=vespri, giorno=giorno)
    except Exception as e:
        print(f"Errore Vespri: {e}")
        return render_template('error.html', message=f"Errore nel caricamento dei Vespri: {str(e)}"), 500
"""

# ✅ CORRETTO - Sostituisci la route /santi
"""
@app.route('/santi')
def santi():
    try:
        date_param = request.args.get('date')

        if date_param:
            giorno_id = get_giorno_id_by_iso_date(date_param)
            if not giorno_id:
                return render_template('error.html', message="Data non trovata nel calendario"), 404
        else:
            today = datetime.now().strftime('%Y%m%d')
            giorno_id = get_giorno_id_by_iso_date(today)
            if not giorno_id:
                return render_template('error.html', message="Dati non disponibili per oggi"), 404

        # ✅ CORRETTO - Usa le funzioni qui
        santi = get_santi_by_giorno(giorno_id)
        giorno_data = get_giorno_completo(date_param or datetime.now().strftime('%Y%m%d'))
        giorno = giorno_data['giorno'] if giorno_data else None

        return render_template('santi.html', santi=santi, giorno=giorno)
    except Exception as e:
        print(f"Errore Santi: {e}")
        return render_template('error.html', message=f"Errore nel caricamento dei Santi: {str(e)}"), 500
"""

# ============================================
# SUMMARY - COSA CAMBIA
# ============================================

"""
❌ DA RIMUOVERE (vecchio codice):
──────────────────────────────────────────

from sqlalchemy import and_
db.session.query(GiornoLiturgico).filter_by(data_iso=date_iso).first()
db.session.query(Santo).filter(and_(Santo.giorno_id == giorno.id, Santo.tipo == 'principale')).first()


✅ DA USARE (nuovo codice):
──────────────────────────────────────────

get_giorno_id_by_iso_date(date_iso)
get_lodi_by_giorno(giorno_id)
get_vespri_by_giorno(giorno_id)
get_santi_by_giorno(giorno_id)
get_giorno_completo(date_iso)
get_dashboard_stats()
get_dashboard_giorni()


🎯 VANTAGGI:
──────────────────────────────────────────

✓ Usa il pattern dell'app (sqlite3 diretto)
✓ Niente più db.session
✓ Niente più modelli SQLAlchemy non definiti
✓ Compatibile con il database SQLite esistente
✓ Connessioni gestite correttamente
✓ Error handling uniformato
"""