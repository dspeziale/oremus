from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.config['DB_PATH'] = 'instance/oremus.db'


def get_db_connection():
    """Connessione al database"""
    conn = sqlite3.connect(app.config['DB_PATH'])
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    """Pagina principale"""
    return render_template('index.html')


@app.route('/api/days')
def get_days():
    """Ottiene lista di tutti i giorni disponibili"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, data, data_iso, giorno_settimana FROM giorni_liturgici 
        ORDER BY data_iso DESC LIMIT 60
    ''')

    days = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(days)


@app.route('/api/day/<data_iso>')
def get_day(data_iso):
    """Ottiene i dati completi di un giorno"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Giorno principale
    cursor.execute('SELECT * FROM giorni_liturgici WHERE data_iso = ?', (data_iso,))
    giorno = dict(cursor.fetchone() or {})

    if not giorno:
        conn.close()
        return jsonify({'error': 'Giorno non trovato'}), 404

    giorno_id = giorno['id']

    # Santo del giorno
    cursor.execute('''
        SELECT * FROM santi WHERE giorno_id = ? ORDER BY tipo DESC
    ''', (giorno_id,))
    santi = [dict(row) for row in cursor.fetchall()]

    # Lodi mattutine
    cursor.execute('SELECT * FROM lodi_mattutine WHERE giorno_id = ?', (giorno_id,))
    lodi = dict(cursor.fetchone() or {})

    if lodi:
        # Versicoli lodi
        cursor.execute('SELECT * FROM versicoli WHERE lodi_id = ?', (lodi['id'],))
        lodi['versicoli'] = [dict(row) for row in cursor.fetchall()]

        # Antifone lodi
        cursor.execute('SELECT * FROM antifone_salmi WHERE lodi_id = ? ORDER BY antifona_numero', (lodi['id'],))
        lodi['antifone_salmi'] = [dict(row) for row in cursor.fetchall()]

        # Invocazioni lodi
        cursor.execute('SELECT contenuto FROM invocazioni WHERE lodi_id = ? AND tipo = ?', (lodi['id'], 'lodi'))
        lodi['invocazioni'] = [row['contenuto'] for row in cursor.fetchall()]

        # Orazioni lodi
        cursor.execute('SELECT testo FROM orazioni WHERE lodi_id = ? AND tipo = ?', (lodi['id'], 'lodi'))
        orazione_lodi = cursor.fetchone()
        lodi['orazione'] = orazione_lodi['testo'] if orazione_lodi else ''

        # Parse JSON fields
        if lodi.get('lettura_breve'):
            lodi['lettura_breve'] = json.loads(lodi['lettura_breve'])
        if lodi.get('responsorio_breve'):
            lodi['responsorio_breve'] = json.loads(lodi['responsorio_breve'])

    # Vespri
    cursor.execute('SELECT * FROM vespri WHERE giorno_id = ?', (giorno_id,))
    vespri = dict(cursor.fetchone() or {})

    if vespri:
        # Versicoli vespri
        cursor.execute('SELECT * FROM versicoli WHERE vespri_id = ?', (vespri['id'],))
        vespri['versicoli'] = [dict(row) for row in cursor.fetchall()]

        # Antifone vespri
        cursor.execute('SELECT * FROM antifone_salmi WHERE vespri_id = ? ORDER BY antifona_numero', (vespri['id'],))
        vespri['antifone_salmi'] = [dict(row) for row in cursor.fetchall()]

        # Intercessioni vespri
        cursor.execute('SELECT contenuto FROM invocazioni WHERE vespri_id = ? AND tipo = ?', (vespri['id'], 'vespri'))
        vespri['intercessioni'] = [row['contenuto'] for row in cursor.fetchall()]

        # Orazioni vespri
        cursor.execute('SELECT testo FROM orazioni WHERE vespri_id = ? AND tipo = ?', (vespri['id'], 'vespri'))
        orazione_vespri = cursor.fetchone()
        vespri['orazione'] = orazione_vespri['testo'] if orazione_vespri else ''

        # Parse JSON fields
        if vespri.get('lettura_breve'):
            vespri['lettura_breve'] = json.loads(vespri['lettura_breve'])
        if vespri.get('responsorio_breve'):
            vespri['responsorio_breve'] = json.loads(vespri['responsorio_breve'])

    conn.close()

    return jsonify({
        'giorno': giorno,
        'santi': santi,
        'lodi_mattutine': lodi,
        'vespri': vespri
    })


@app.route('/api/today')
def get_today():
    """Ottiene il giorno di oggi"""
    conn = get_db_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y%m%d')
    cursor.execute('SELECT data_iso FROM giorni_liturgici WHERE data_iso = ?', (today,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return jsonify({'data_iso': result['data_iso']})

    # Se oggi non esiste, prendi il più recente
    cursor.execute('SELECT data_iso FROM giorni_liturgici ORDER BY data_iso DESC LIMIT 1')
    result = cursor.fetchone()
    conn.close()

    if result:
        return jsonify({'data_iso': result['data_iso']})

    return jsonify({'error': 'Nessun dato disponibile'}), 404


@app.route('/api/santo/search')
def search_santo():
    """Ricerca santi per nome"""
    query = request.args.get('q', '')
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT s.*, g.data, g.data_iso 
        FROM santi s 
        JOIN giorni_liturgici g ON s.giorno_id = g.id 
        WHERE s.nome_santo LIKE ? 
        LIMIT 20
    ''', (f'%{query}%',))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0',port=59000)