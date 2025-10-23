# ============================================
# DATABASE QUERIES - SQLITE3 DIRETTO
# ============================================
import sqlite3
from datetime import datetime

DB_PATH = 'instance/oremus.db'


def get_connection():
    """
    Crea una connessione al database

    Returns:
        sqlite3.Connection: Connessione al database
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Permette l'accesso per colonna
        return conn
    except Exception as e:
        print(f"❌ Errore connessione DB: {e}")
        return None


# ============================================
# GIORNI LITURGICI
# ============================================

def get_giorno_id_by_iso_date(date_iso):
    """
    Recupera l'ID del giorno dalla data ISO (YYYYMMDD)

    Args:
        date_iso (str): Data nel formato YYYYMMDD (es: 20251023)

    Returns:
        int: ID del giorno, None se non trovato
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id FROM giorni_liturgici 
            WHERE data_iso = ?
        ''', (date_iso,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None
    except Exception as e:
        print(f"❌ Errore nel recupero del giorno: {e}")
        return None


def get_giorno_by_iso_date(date_iso):
    """
    Recupera il record completo del giorno dalla data ISO

    Args:
        date_iso (str): Data nel formato YYYYMMDD

    Returns:
        dict: Record del giorno, None se non trovato
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, data, data_iso, giorno_settimana, created_at
            FROM giorni_liturgici 
            WHERE data_iso = ?
        ''', (date_iso,))

        result = cursor.fetchone()
        conn.close()

        return dict(result) if result else None
    except Exception as e:
        print(f"❌ Errore nel recupero del giorno: {e}")
        return None


def get_today_giorno():
    """
    Recupera il giorno di oggi

    Returns:
        dict: Record del giorno odierno
    """
    today = datetime.now().strftime('%Y%m%d')
    return get_giorno_by_iso_date(today)


def get_giorno_range(start_date, end_date):
    """
    Recupera un intervallo di giorni liturgici

    Args:
        start_date (str): Data inizio YYYYMMDD
        end_date (str): Data fine YYYYMMDD

    Returns:
        list: Lista di dict con record giorni
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, data, data_iso, giorno_settimana, created_at
            FROM giorni_liturgici 
            WHERE data_iso >= ? AND data_iso <= ?
            ORDER BY data_iso ASC
        ''', (start_date, end_date))

        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]
    except Exception as e:
        print(f"❌ Errore nel recupero intervallo giorni: {e}")
        return []


def get_all_giorni_paginated(page=1, per_page=20):
    """
    Recupera tutti i giorni con paginazione

    Args:
        page (int): Numero pagina
        per_page (int): Risultati per pagina

    Returns:
        tuple: (list di dict, totale record)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Totale
        cursor.execute('SELECT COUNT(*) FROM giorni_liturgici')
        total = cursor.fetchone()[0]

        # Pagina
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT id, data, data_iso, giorno_settimana, created_at
            FROM giorni_liturgici 
            ORDER BY data_iso DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))

        results = cursor.fetchall()
        conn.close()

        return ([dict(row) for row in results], total)
    except Exception as e:
        print(f"❌ Errore nel recupero pagina giorni: {e}")
        return ([], 0)


# ============================================
# LODI MATTUTINE
# ============================================

def get_lodi_by_giorno_id(giorno_id):
    """
    Recupera le Lodi Mattutine di un giorno specifico

    Args:
        giorno_id (int): ID del giorno

    Returns:
        dict: Record delle Lodi, None se non trovate
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, giorno_id, tipo, titolo, gloria_al_padre, inno, 
                   lettura_breve, responsorio_breve, antifona_cantico_finale, 
                   cantico_finale
            FROM lodi_mattutine 
            WHERE giorno_id = ?
        ''', (giorno_id,))

        result = cursor.fetchone()
        conn.close()

        return dict(result) if result else None
    except Exception as e:
        print(f"❌ Errore nel recupero Lodi: {e}")
        return None


def get_lodi_by_iso_date(date_iso):
    """
    Recupera le Lodi Mattutine da una data ISO

    Args:
        date_iso (str): Data nel formato YYYYMMDD

    Returns:
        dict: Record delle Lodi, None se non trovate
    """
    giorno_id = get_giorno_id_by_iso_date(date_iso)
    if giorno_id:
        return get_lodi_by_giorno_id(giorno_id)
    return None


def get_today_lodi():
    """
    Recupera le Lodi di oggi

    Returns:
        dict: Record delle Lodi odierne
    """
    today = datetime.now().strftime('%Y%m%d')
    return get_lodi_by_iso_date(today)


# ============================================
# VESPRI
# ============================================

def get_vespri_by_giorno_id(giorno_id):
    """
    Recupera i Vespri di un giorno specifico

    Args:
        giorno_id (int): ID del giorno

    Returns:
        dict: Record dei Vespri, None se non trovati
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, giorno_id, tipo, titolo, gloria_al_padre, inno, 
                   lettura_breve, responsorio_breve, antifona_cantico_finale, 
                   cantico_finale
            FROM vespri 
            WHERE giorno_id = ?
        ''', (giorno_id,))

        result = cursor.fetchone()
        conn.close()

        return dict(result) if result else None
    except Exception as e:
        print(f"❌ Errore nel recupero Vespri: {e}")
        return None


def get_vespri_by_iso_date(date_iso):
    """
    Recupera i Vespri da una data ISO

    Args:
        date_iso (str): Data nel formato YYYYMMDD

    Returns:
        dict: Record dei Vespri, None se non trovati
    """
    giorno_id = get_giorno_id_by_iso_date(date_iso)
    if giorno_id:
        return get_vespri_by_giorno_id(giorno_id)
    return None


def get_today_vespri():
    """
    Recupera i Vespri di oggi

    Returns:
        dict: Record dei Vespri odierni
    """
    today = datetime.now().strftime('%Y%m%d')
    return get_vespri_by_iso_date(today)


# ============================================
# SANTI
# ============================================

def get_santi_by_giorno_id(giorno_id):
    """
    Recupera i santi di un giorno specifico

    Args:
        giorno_id (int): ID del giorno

    Returns:
        list: Lista di dict con i santi
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, giorno_id, giorno, nome_santo, martirologio, tipo
            FROM santi 
            WHERE giorno_id = ?
            ORDER BY tipo DESC
        ''', (giorno_id,))

        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]
    except Exception as e:
        print(f"❌ Errore nel recupero santi: {e}")
        return []


def get_santi_by_iso_date(date_iso):
    """
    Recupera i santi da una data ISO

    Args:
        date_iso (str): Data nel formato YYYYMMDD

    Returns:
        list: Lista di dict con i santi
    """
    giorno_id = get_giorno_id_by_iso_date(date_iso)
    if giorno_id:
        return get_santi_by_giorno_id(giorno_id)
    return []


def get_today_santi():
    """
    Recupera i santi di oggi

    Returns:
        list: Lista di dict con i santi di oggi
    """
    today = datetime.now().strftime('%Y%m%d')
    return get_santi_by_iso_date(today)


def get_santo_principale(giorno_id):
    """
    Recupera il santo principale di un giorno

    Args:
        giorno_id (int): ID del giorno

    Returns:
        dict: Record del santo principale, None se non trovato
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, giorno_id, giorno, nome_santo, martirologio, tipo
            FROM santi 
            WHERE giorno_id = ? AND tipo = 'principale'
            LIMIT 1
        ''', (giorno_id,))

        result = cursor.fetchone()
        conn.close()

        return dict(result) if result else None
    except Exception as e:
        print(f"❌ Errore nel recupero santo principale: {e}")
        return None


# ============================================
# ANTIFONE E SALMI
# ============================================

def get_antifone_salmi_by_lodi_id(lodi_id):
    """
    Recupera antifone e salmi per le Lodi

    Args:
        lodi_id (int): ID delle Lodi

    Returns:
        list: Lista di dict con antifone e salmi
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, lodi_id, vespri_id, antifona_numero, antifona_testo, 
                   tipo, numero, titolo, contenuto
            FROM antifone_salmi 
            WHERE lodi_id = ?
            ORDER BY antifona_numero ASC
        ''', (lodi_id,))

        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]
    except Exception as e:
        print(f"❌ Errore nel recupero antifone Lodi: {e}")
        return []


def get_antifone_salmi_by_vespri_id(vespri_id):
    """
    Recupera antifone e salmi per i Vespri

    Args:
        vespri_id (int): ID dei Vespri

    Returns:
        list: Lista di dict con antifone e salmi
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, lodi_id, vespri_id, antifona_numero, antifona_testo, 
                   tipo, numero, titolo, contenuto
            FROM antifone_salmi 
            WHERE vespri_id = ?
            ORDER BY antifona_numero ASC
        ''', (vespri_id,))

        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]
    except Exception as e:
        print(f"❌ Errore nel recupero antifone Vespri: {e}")
        return []


# ============================================
# VERSICOLI
# ============================================

def get_versicoli_by_lodi_id(lodi_id):
    """
    Recupera versicoli per le Lodi

    Args:
        lodi_id (int): ID delle Lodi

    Returns:
        list: Lista di dict con versicoli
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, lodi_id, vespri_id, versicolo, risposta
            FROM versicoli 
            WHERE lodi_id = ?
        ''', (lodi_id,))

        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]
    except Exception as e:
        print(f"❌ Errore nel recupero versicoli Lodi: {e}")
        return []


def get_versicoli_by_vespri_id(vespri_id):
    """
    Recupera versicoli per i Vespri

    Args:
        vespri_id (int): ID dei Vespri

    Returns:
        list: Lista di dict con versicoli
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, lodi_id, vespri_id, versicolo, risposta
            FROM versicoli 
            WHERE vespri_id = ?
        ''', (vespri_id,))

        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]
    except Exception as e:
        print(f"❌ Errore nel recupero versicoli Vespri: {e}")
        return []


# ============================================
# STATISTICHE DASHBOARD
# ============================================

def get_dashboard_stats():
    """
    Recupera statistiche per il dashboard

    Returns:
        dict: Statistiche generali
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Giorni totali
        cursor.execute('SELECT COUNT(*) FROM giorni_liturgici')
        total_days = cursor.fetchone()[0]

        # Lodi e Vespri
        cursor.execute('SELECT COUNT(*) FROM lodi_mattutine')
        total_lodi = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM vespri')
        total_vespri = cursor.fetchone()[0]

        # Santi
        cursor.execute('SELECT COUNT(*) FROM santi')
        total_santi = cursor.fetchone()[0]

        conn.close()

        return {
            'total_days': total_days,
            'total_lodi': total_lodi,
            'total_vespri': total_vespri,
            'total_santi': total_santi,
            'total_prayers': total_lodi + total_vespri
        }
    except Exception as e:
        print(f"❌ Errore nel recupero statistiche: {e}")
        return {
            'total_days': 0,
            'total_lodi': 0,
            'total_vespri': 0,
            'total_santi': 0,
            'total_prayers': 0
        }


def get_all_giorni_with_santi(limit=None):
    """
    Recupera tutti i giorni con il santo principale

    Args:
        limit (int): Massimo numero di risultati

    Returns:
        list: Lista di dict con giorni e santi
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT 
                g.id,
                g.data,
                g.data_iso,
                g.giorno_settimana,
                (SELECT nome_santo FROM santi WHERE giorno_id = g.id AND tipo = 'principale' LIMIT 1) as santo_principale
            FROM giorni_liturgici g
            ORDER BY g.data_iso DESC
        '''

        if limit:
            query += f' LIMIT {limit}'

        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]
    except Exception as e:
        print(f"❌ Errore nel recupero giorni con santi: {e}")
        return []


# ============================================
# RICERCA
# ============================================

def search_santi(query):
    """
    Ricerca santi per nome

    Args:
        query (str): Testo da cercare

    Returns:
        list: Lista di dict con santi trovati
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        search_term = f"%{query}%"
        cursor.execute('''
            SELECT id, giorno_id, giorno, nome_santo, martirologio, tipo
            FROM santi 
            WHERE nome_santo LIKE ? OR martirologio LIKE ?
            ORDER BY nome_santo ASC
            LIMIT 20
        ''', (search_term, search_term))

        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]
    except Exception as e:
        print(f"❌ Errore nella ricerca santi: {e}")
        return []


def search_giorni(query):
    """
    Ricerca giorni per data o giorno della settimana

    Args:
        query (str): Testo da cercare

    Returns:
        list: Lista di dict con giorni trovati
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        search_term = f"%{query}%"
        cursor.execute('''
            SELECT id, data, data_iso, giorno_settimana, created_at
            FROM giorni_liturgici 
            WHERE data LIKE ? OR giorno_settimana LIKE ? OR data_iso LIKE ?
            ORDER BY data_iso DESC
            LIMIT 20
        ''', (search_term, search_term, search_term))

        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]
    except Exception as e:
        print(f"❌ Errore nella ricerca giorni: {e}")
        return []