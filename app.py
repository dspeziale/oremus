#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oremus Web - Applicazione Flask
Interfaccia web per Liturgia delle Ore da instance/oremus.db
"""
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for
from database import OremusDB

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Inizializza database GLOBALE (per statistiche)
# Le query useranno connessioni per-request
_global_db = OremusDB()


def get_db():
    """Ottiene connessione database per il thread corrente"""
    if not hasattr(app, 'db'):
        app.db = OremusDB()
    return app.db


@app.teardown_appcontext
def close_db(error):
    """Chiude connessione al termine della request"""
    db = app.__dict__.pop('db', None)
    if db is not None:
        db.close()


def formato_data(date_string):
    """Formatta data YYYYMMDD a italiano"""
    try:
        dt = datetime.strptime(date_string, "%Y%m%d")
        giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
        return f"{giorni[dt.weekday()]} {dt.day} {mesi[dt.month - 1]} {dt.year}"
    except:
        return date_string


def get_data_string(dt_obj):
    """Converte datetime object a YYYYMMDD"""
    return dt_obj.strftime("%Y%m%d")


def get_santo(data):
    """Ottiene santo dal DB"""
    try:
        db = get_db()
        cursor = db.conn.cursor()
        cursor.execute('''
            SELECT id, santo_principale, numero_santi
            FROM santo_giorno s
            WHERE s.data_id = (SELECT id FROM date WHERE data = ?)
        ''', (data,))

        row = cursor.fetchone()
        if not row:
            return None

        santo_id, santo_principale, numero_santi = row

        # Santi commemorati
        cursor.execute('''
            SELECT testo FROM santo_commemorato
            WHERE santo_giorno_id = ?
            ORDER BY ordine
            LIMIT 5
        ''', (santo_id,))

        commemorati = [r[0] for r in cursor.fetchall()]

        return {
            'principale': santo_principale,
            'numero': numero_santi,
            'commemorati': commemorati
        }
    except Exception as e:
        print(f"Errore get_santo: {e}")
        return None


def get_lodi(data):
    """Ottiene Lodi dal DB"""
    try:
        db = get_db()
        cursor = db.conn.cursor()
        cursor.execute('''
            SELECT id, introduzione, inno, responsorio_breve, orazione, conclusione
            FROM lodi_mattutine
            WHERE data_id = (SELECT id FROM date WHERE data = ?)
        ''', (data,))

        row = cursor.fetchone()
        if not row:
            return None

        lodi_id = row[0]

        # Salmodia
        cursor.execute('''
            SELECT numero, antifona_inizio, titolo, testo
            FROM salmodia_lodi
            WHERE lodi_mattutine_id = ?
            ORDER BY numero
        ''', (lodi_id,))

        salmodia = []
        for r in cursor.fetchall():
            numero, antifona, titolo, testo = r[0], r[1], r[2], r[3]

            # Dividi il testo: prima riga è numero/titolo, resto è il testo
            testo_lines = testo.split('\n') if testo else []

            # Prima riga è numero/titolo del salmo, mantienila
            testo_formattato = '\n'.join(testo_lines) if testo_lines else ""

            salmodia.append({
                'numero': numero,
                'antifona': antifona,
                'titolo': titolo,
                'testo': testo_formattato
            })

        # Lettura breve
        cursor.execute('''
            SELECT riferimento, testo FROM lettura_breve_lodi
            WHERE lodi_mattutine_id = ?
        ''', (lodi_id,))

        lettura_row = cursor.fetchone()
        lettura_breve = {'riferimento': lettura_row[0], 'testo': lettura_row[1]} if lettura_row else None

        # Cantico
        cursor.execute('''
            SELECT testo, dossologia FROM cantico_lodi
            WHERE lodi_mattutine_id = ?
        ''', (lodi_id,))

        cantico_row = cursor.fetchone()
        cantico = {'testo': cantico_row[0], 'dossologia': cantico_row[1]} if cantico_row else None

        return {
            'introduzione': row[1],
            'inno': row[2],
            'salmodia': salmodia,
            'lettura_breve': lettura_breve,
            'responsorio_breve': row[3],
            'cantico': cantico,
            'orazione': row[4],
            'conclusione': row[5]
        }
    except Exception as e:
        print(f"Errore get_lodi: {e}")
        return None


def get_vespri(data):
    """Ottiene Vespri dal DB"""
    try:
        db = get_db()
        cursor = db.conn.cursor()
        cursor.execute('''
            SELECT id, introduzione, inno, responsorio_breve, orazione, conclusione
            FROM vespri
            WHERE data_id = (SELECT id FROM date WHERE data = ?)
        ''', (data,))

        row = cursor.fetchone()
        if not row:
            return None

        vespri_id = row[0]

        # Salmodia
        cursor.execute('''
            SELECT numero, antifona_inizio, titolo, testo
            FROM salmodia_vespri
            WHERE vespri_id = ?
            ORDER BY numero
        ''', (vespri_id,))

        salmodia = []
        for r in cursor.fetchall():
            numero, antifona, titolo, testo = r[0], r[1], r[2], r[3]

            # Dividi il testo: prima riga è numero/titolo, resto è il testo
            testo_lines = testo.split('\n') if testo else []

            # Prima riga è numero/titolo del salmo, mantienila
            testo_formattato = '\n'.join(testo_lines) if testo_lines else ""

            salmodia.append({
                'numero': numero,
                'antifona': antifona,
                'titolo': titolo,
                'testo': testo_formattato
            })

        # Lettura breve
        cursor.execute('''
            SELECT riferimento, testo FROM lettura_breve_vespri
            WHERE vespri_id = ?
        ''', (vespri_id,))

        lettura_row = cursor.fetchone()
        lettura_breve = {'riferimento': lettura_row[0], 'testo': lettura_row[1]} if lettura_row else None

        # Magnificat
        cursor.execute('''
            SELECT riferimento, sottotitolo, testo, dossologia FROM cantico_vespri
            WHERE vespri_id = ?
        ''', (vespri_id,))

        magnificat_row = cursor.fetchone()
        magnificat = {
            'riferimento': magnificat_row[0],
            'sottotitolo': magnificat_row[1],
            'testo': magnificat_row[2],
            'dossologia': magnificat_row[3]
        } if magnificat_row else None

        return {
            'introduzione': row[1],
            'inno': row[2],
            'salmodia': salmodia,
            'lettura_breve': lettura_breve,
            'responsorio_breve': row[3],
            'magnificat': magnificat,
            'orazione': row[4],
            'conclusione': row[5]
        }
    except Exception as e:
        print(f"Errore get_vespri: {e}")
        return None


def get_liturgia(data):
    """Ottiene Liturgia dal DB"""
    try:
        db = get_db()
        cursor = db.conn.cursor()
        cursor.execute('''
            SELECT id FROM liturgia_giorno
            WHERE data_id = (SELECT id FROM date WHERE data = ?)
        ''', (data,))

        row = cursor.fetchone()
        if not row:
            return None

        liturgia_id = row[0]

        cursor.execute('''
            SELECT tipo, riferimento, testo FROM lettura_liturgica
            WHERE liturgia_giorno_id = ?
            ORDER BY ordine
        ''', (liturgia_id,))

        letture = []
        for r in cursor.fetchall():
            letture.append({'tipo': r[0], 'riferimento': r[1], 'testo': r[2]})

        return {'letture': letture}
    except Exception as e:
        print(f"Errore get_liturgia: {e}")
        return None


def date_exists(data):
    """Verifica se data esiste nel DB"""
    try:
        db = get_db()
        cursor = db.conn.cursor()
        cursor.execute('SELECT id FROM date WHERE data = ?', (data,))
        return cursor.fetchone() is not None
    except:
        return False


@app.route('/')
def index():
    """Home - reindirizza a oggi"""
    today = datetime.now()
    data_today = get_data_string(today)
    return redirect(url_for('day', data=data_today))


@app.route('/day/<data>')
def day(data):
    """Pagina giorno completo"""
    try:
        dt = datetime.strptime(data, "%Y%m%d")
    except:
        return redirect(url_for('index'))

    # Giorni precedente/successivo
    dt_obj = datetime.strptime(data, "%Y%m%d")
    prev_date = (dt_obj - timedelta(days=1)).strftime("%Y%m%d")
    next_date = (dt_obj + timedelta(days=1)).strftime("%Y%m%d")

    # Carica dati
    santo = get_santo(data)
    lodi = get_lodi(data)
    vespri = get_vespri(data)
    liturgia = get_liturgia(data)
    data_fmt = formato_data(data)

    # Se non ha dati, mostra avviso
    has_data = santo or lodi or vespri or liturgia

    return render_template('day.html',
                           data=data,
                           data_fmt=data_fmt,
                           prev_date=prev_date,
                           next_date=next_date,
                           santo=santo,
                           lodi=lodi,
                           vespri=vespri,
                           liturgia=liturgia,
                           has_data=has_data
                           )


@app.route('/calendar')
def calendar():
    """Pagina calendario"""
    today = datetime.now()
    current_month = today.strftime("%Y%m")

    return render_template('calendar.html', current_month=current_month)


@app.route('/api/dates/<month>')
def api_dates(month):
    """API: ottiene date disponibili per mese con santo"""
    try:
        db = get_db()
        cursor = db.conn.cursor()

        # Converti da 2025-10 a 202510
        month_yyyymm = month.replace('-', '')

        cursor.execute('''
            SELECT d.data, d.data_formattata, s.santo_principale
            FROM date d
            LEFT JOIN santo_giorno s ON d.id = s.data_id
            WHERE d.data LIKE ?
            ORDER BY d.data
        ''', (month_yyyymm + '%',))

        dates = []
        for r in cursor.fetchall():
            dates.append({
                'data': r[0],
                'data_fmt': r[1],
                'santo': r[2] if r[2] else ''
            })

        return jsonify({'dates': dates, 'count': len(dates)})
    except Exception as e:
        print(f"❌ Errore API: {e}")
        return jsonify({'dates': [], 'error': str(e)})


@app.route('/api/search')
def api_search():
    """API: ricerca data"""
    q = request.args.get('q', '')

    if len(q) < 8:
        return jsonify({'results': []})

    try:
        db = get_db()
        cursor = db.conn.cursor()
        cursor.execute('''
            SELECT data, data_formattata FROM date
            WHERE data LIKE ?
            ORDER BY data DESC
            LIMIT 10
        ''', (q + '%',))

        results = [{'data': r[0], 'data_fmt': r[1]} for r in cursor.fetchall()]
        return jsonify({'results': results})
    except:
        return jsonify({'results': []})


@app.route('/about')
def about():
    """Pagina about"""
    stats = {'date': 0, 'lodi': 0, 'vespri': 0, 'santo': 0}
    try:
        db = get_db()
        cursor = db.conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM date')
        stats['date'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM lodi_mattutine')
        stats['lodi'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM vespri')
        stats['vespri'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM santo_giorno')
        stats['santo'] = cursor.fetchone()[0]
    except Exception as e:
        print(f"Errore statistiche: {e}")

    return render_template('about.html', stats=stats)


@app.errorhandler(404)
def not_found(error):
    """Pagina 404"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    """Pagina 500"""
    return render_template('500.html'), 500


@app.context_processor
def inject_now():
    """Inietta data/ora nei template"""
    return {'now': datetime.now()}


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)