#!/usr/bin/env python3
"""
OREMUS - Applicazione per visualizzare la Liturgia delle Ore
Dashboard con navigazione per date, santi del giorno, lodi e vespri
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
import json
from app import db_exists, get_db_connection, dict_from_row

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

DB_PATH = Path("instance/oremus.db")


def get_db():
    """Ritorna la connessione al database"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_giorno(data):
    """Recupera i dati di un giorno specifico"""
    conn = get_db()
    cursor = conn.cursor()

    # Recupera dati del giorno
    cursor.execute('''
        SELECT * FROM giorni_liturgici WHERE data = ?
    ''', (data,))

    giorno = cursor.fetchone()

    if giorno:
        # Recupera lodi
        cursor.execute('''
            SELECT * FROM lodi_mattutine WHERE data = ?
        ''', (data,))
        lodi = cursor.fetchone()

        # Recupera vespri
        cursor.execute('''
            SELECT * FROM vespri WHERE data = ?
        ''', (data,))
        vespri = cursor.fetchone()

        conn.close()

        return {
            'data': giorno['data'],
            'data_formattata': giorno['data_formattata'],
            'santo': giorno['santo_principale'],
            'colore': giorno['colore_liturgico'],
            'grado': giorno['grado_celebrazione'],
            'martirologio': giorno['martirologio'],
            'lodi': dict(lodi) if lodi else None,
            'vespri': dict(vespri) if vespri else None,
        }

    conn.close()
    return None


def get_all_dates():
    """Ritorna tutte le date disponibili nel database"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT giorno as data, santo_principale FROM santi 
        ORDER BY data ASC
    ''')

    dates = cursor.fetchall()
    conn.close()

    return [
        {
            'data': row['data'],
            'santo': row['santo_principale']
        } for row in dates
    ]


def get_today():
    """Ritorna la data odierna nel formato YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")


@app.route('/')
def index():
    """Homepage - Mostra il giorno odierno"""
    today = get_today()
    giorno = get_giorno(today)

    # Se non c'è un giorno per oggi, prendi il primo disponibile
    if not giorno:
        all_dates = get_all_dates()
        if all_dates:
            giorno = get_giorno(all_dates[0]['data'])
            today = all_dates[0]['data']

    all_dates = get_all_dates()

    return render_template(
        'index.html',
        giorno=giorno,
        today=today,
        all_dates=all_dates
    )

@app.route('/profile/edit', methods=['GET', 'POST'])
def profile_edit():
    """Edit profile page"""
    if request.method == 'POST':
        try:
            if not db_exists():
                return jsonify({'status': 'error', 'message': 'Database non disponibile'}), 400

            conn = get_db_connection()
            if conn is None:
                return jsonify({'status': 'error', 'message': 'Errore connessione DB'}), 400

            cursor = conn.cursor()
            data = request.get_json() or request.form

            cursor.execute('''
                UPDATE utenti 
                SET nome = ?, email = ?, telefono = ?, bio = ?, indirizzo = ?, citta = ?, paese = ?
                WHERE ruolo = ?
            ''', (
                data.get('nome'),
                data.get('email'),
                data.get('telefono'),
                data.get('bio'),
                data.get('indirizzo'),
                data.get('citta'),
                data.get('paese'),
                'admin'
            ))

            conn.commit()
            conn.close()

            print(f"✅ Profilo aggiornato")
            return jsonify({'status': 'success', 'message': 'Profilo aggiornato con successo'})
        except Exception as e:
            print(f"❌ Errore in profile_edit POST: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 400

    try:
        if not db_exists():
            return render_template('profile_edit.html', profile={'nome': 'Oremus', 'email': 'admin@oremus.it'})

        conn = get_db_connection()
        if conn is None:
            return render_template('profile_edit.html', profile={'nome': 'Oremus', 'email': 'admin@oremus.it'})

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM utenti WHERE ruolo = ? LIMIT 1', ('admin',))
        profile_data = dict_from_row(cursor.fetchone())
        conn.close()

        if not profile_data:
            profile_data = {'nome': 'Oremus', 'email': 'admin@oremus.it'}

        return render_template('profile_edit.html', profile=profile_data)

    except Exception as e:
        print(f"❌ Errore in profile_edit GET: {e}")
        return render_template('profile_edit.html', profile={'nome': 'Oremus', 'email': 'admin@oremus.it'})


@app.route('/profile/settings')
def profile_settings():
    """Profile settings page"""
    return render_template('profile_settings.html')


# ============================================
# NAVIGATION & UTILITY ROUTES
# ============================================
@app.route('/help')
def help():
    """Help page"""
    return render_template('help.html')


@app.route('/licenses')
def licenses():
    """Licenses information page"""
    return render_template('licenses.html')

@app.route('/profile')
def profile():
    """User profile page"""
    try:
        if not db_exists():
            return render_template('profile.html',
                                   profile={'nome': 'Oremus', 'email': 'admin@oremus.it', 'ruolo': 'admin'})

        conn = get_db_connection()
        if conn is None:
            return render_template('profile.html',
                                   profile={'nome': 'Oremus', 'email': 'admin@oremus.it', 'ruolo': 'admin'})

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM utenti WHERE ruolo = ? LIMIT 1', ('admin',))
        profile_data = dict_from_row(cursor.fetchone())
        conn.close()

        if not profile_data:
            profile_data = {'nome': 'Oremus', 'email': 'admin@oremus.it', 'ruolo': 'admin'}

        print(f"✅ Caricato profilo: {profile_data.get('nome', 'Oremus')}")
        return render_template('profile.html', profile=profile_data)

    except Exception as e:
        print(f"❌ Errore in profile: {e}")
        return render_template('profile.html', profile={'nome': 'Oremus', 'email': 'admin@oremus.it', 'ruolo': 'admin'})

@app.route('/logout')
def logout():
    """Logout user and redirect to home"""
    return redirect(url_for('index'))

@app.route('/giorno/<data>')
def giorno(data):
    """Visualizza un giorno specifico"""
    giorno_data = get_giorno(data)
    all_dates = get_all_dates()

    if not giorno_data:
        return render_template('error.html', message="Giorno non trovato"), 404

    return render_template(
        'index.html',
        giorno=giorno_data,
        today=data,
        all_dates=all_dates
    )


@app.route('/api/dates')
def api_dates():
    """API: Ritorna tutte le date disponibili"""
    return jsonify(get_all_dates())


@app.route('/api/giorno/<data>')
def api_giorno(data):
    """API: Ritorna i dati di un giorno specifico"""
    giorno_data = get_giorno(data)

    if not giorno_data:
        return jsonify({'error': 'Giorno non trovato'}), 404

    return jsonify(giorno_data)


@app.route('/calendario')
def calendario():
    """Visualizza il calendario interattivo"""
    all_dates = get_all_dates()
    today = get_today()

    return render_template(
        'calendario.html',
        all_dates=all_dates,
        today=today
    )


@app.route('/lodi')
def lodi():
    """Visualizza le Lodi Mattutine del giorno odierno"""
    today = get_today()
    giorno_data = get_giorno(today)
    all_dates = get_all_dates()

    if not giorno_data:
        all_dates = get_all_dates()
        if all_dates:
            today = all_dates[0]['data']
            giorno_data = get_giorno(today)

    return render_template(
        'lodi.html',
        giorno=giorno_data,
        today=today,
        all_dates=all_dates
    )


@app.route('/vespri')
def vespri():
    """Visualizza i Vespri del giorno odierno"""
    today = get_today()
    giorno_data = get_giorno(today)
    all_dates = get_all_dates()

    if not giorno_data:
        all_dates = get_all_dates()
        if all_dates:
            today = all_dates[0]['data']
            giorno_data = get_giorno(today)

    return render_template(
        'vespri.html',
        giorno=giorno_data,
        today=today,
        all_dates=all_dates
    )


@app.route('/santi')
def santi():
    """Visualizza la lista dei santi memorizzati"""
    all_dates = get_all_dates()
    today = get_today()

    santi_list = []
    for date_info in all_dates:
        giorno_data = get_giorno(date_info['data'])
        if giorno_data:
            santi_list.append({
                'data': giorno_data['data'],
                'data_formattata': giorno_data['data_formattata'],
                'santo': giorno_data['santo'],
                'colore': giorno_data['colore'],
                'grado': giorno_data['grado'],
                'martirologio': giorno_data['martirologio'],
            })

    return render_template(
        'santi.html',
        santi=santi_list,
        today=today,
        all_dates=all_dates
    )


@app.errorhandler(404)
def not_found(error):
    """Gestisce gli errori 404"""
    return render_template('error.html', message="Pagina non trovata"), 404


@app.errorhandler(500)
def server_error(error):
    """Gestisce gli errori 500"""
    return render_template('error.html', message="Errore interno del server"), 500


# Sezione da aggiungere a app.py

@app.route('/api/dashboard/giorni')
def get_dashboard_giorni():
    """API endpoint to get all liturgical days with their saints from database"""
    try:
        import sqlite3

        db_path = "instance/oremus.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query per ottenere giorni e santi
        cursor.execute('''
            SELECT 
                g.id,
                g.data,
                g.data_iso,
                g.giorno_settimana,
                s.nome_santo as santo_principale
            FROM giorni_liturgici g
            LEFT JOIN santi s ON g.id = s.giorno_id AND s.tipo = 'principale'
            ORDER BY g.data_iso ASC
        ''')

        giorni = []
        for row in cursor.fetchall():
            giorni.append({
                'id': row['id'],
                'data': row['data'],
                'data_iso': row['data_iso'],
                'giorno_settimana': row['giorno_settimana'],
                'santo_principale': row['santo_principale']
            })

        conn.close()

        return jsonify({
            'status': 'success',
            'giorni': giorni,
            'total': len(giorni)
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'giorni': []
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)