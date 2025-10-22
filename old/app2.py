import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'oremus'
app.config['JSON_AS_ASCII'] = False
CORS(app)

DB_PATH = 'instance/oremus.db'


# ============================================
# DATABASE HELPER FUNCTIONS
# ============================================

def get_db_connection():
    """Crea una connessione al database SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_giorno_liturgico(data_iso: str = None):
    """Ottiene il giorno liturgico per una data specifica o oggi"""
    if not data_iso:
        data_iso = datetime.now().strftime('%Y-%m-%d')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM giorni_liturgici WHERE data_iso = ?', (data_iso,))
    giorno = cursor.fetchone()
    conn.close()
    return dict(giorno) if giorno else None


def get_lodi_by_giorno(giorno_id: int):
    """Ottiene i dati delle lodi per un giorno"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM lodi_mattutine WHERE giorno_id = ?', (giorno_id,))
    lodi = cursor.fetchone()

    if lodi:
        lodi = dict(lodi)
        lodi_id = lodi['id']

        # Salmi e antifone
        cursor.execute('SELECT * FROM antifone_salmi WHERE lodi_id = ?', (lodi_id,))
        lodi['salmi'] = [dict(row) for row in cursor.fetchall()]

        # Versicoli
        cursor.execute('SELECT * FROM versicoli WHERE lodi_id = ?', (lodi_id,))
        lodi['versicoli'] = [dict(row) for row in cursor.fetchall()]

        # Invocazioni
        cursor.execute('SELECT * FROM invocazioni WHERE lodi_id = ?', (lodi_id,))
        lodi['invocazioni'] = [dict(row) for row in cursor.fetchall()]

        # Orazioni
        cursor.execute('SELECT * FROM orazioni WHERE lodi_id = ?', (lodi_id,))
        lodi['orazioni'] = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return lodi


def get_vespri_by_giorno(giorno_id: int):
    """Ottiene i dati dei vespri per un giorno"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM vespri WHERE giorno_id = ?', (giorno_id,))
    vespri = cursor.fetchone()

    if vespri:
        vespri = dict(vespri)
        vespri_id = vespri['id']

        # Salmi e antifone
        cursor.execute('SELECT * FROM antifone_salmi WHERE vespri_id = ?', (vespri_id,))
        vespri['salmi'] = [dict(row) for row in cursor.fetchall()]

        # Versicoli
        cursor.execute('SELECT * FROM versicoli WHERE vespri_id = ?', (vespri_id,))
        vespri['versicoli'] = [dict(row) for row in cursor.fetchall()]

        # Intercessioni
        cursor.execute('SELECT * FROM invocazioni WHERE vespri_id = ?', (vespri_id,))
        vespri['intercessioni'] = [dict(row) for row in cursor.fetchall()]

        # Orazioni
        cursor.execute('SELECT * FROM orazioni WHERE vespri_id = ?', (vespri_id,))
        vespri['orazioni'] = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return vespri


def get_santi_by_giorno(giorno_id: int):
    """Ottiene i santi per un giorno"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM santi WHERE giorno_id = ? ORDER BY tipo DESC', (giorno_id,))
    santi = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return santi


def get_calendario(mese: int = None, anno: int = None):
    """Ottiene tutti i giorni del mese"""
    if not mese:
        mese = datetime.now().month
    if not anno:
        anno = datetime.now().year

    conn = get_db_connection()
    cursor = conn.cursor()

    # Ottieni tutti i giorni del mese
    cursor.execute('''
        SELECT * FROM giorni_liturgici 
        WHERE strftime('%Y', data_iso) = ? AND strftime('%m', data_iso) = ?
        ORDER BY data_iso
    ''', (str(anno), f'{mese:02d}'))

    giorni = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return giorni


# ============================================
# ROUTES - HOME & MAIN PAGES
# ============================================

@app.route('/')
def index():
    """Homepage - mostra il giorno di oggi"""
    giorno = get_giorno_liturgico()

    if not giorno:
        return render_template('error.html', message='Dati non disponibili per oggi'), 404

    lodi = get_lodi_by_giorno(giorno['id'])
    vespri = get_vespri_by_giorno(giorno['id'])
    santi = get_santi_by_giorno(giorno['id'])

    return render_template('index.html',
                           giorno=giorno,
                           lodi=lodi,
                           vespri=vespri,
                           santi=santi)


@app.route('/calendario')
def calendario():
    """Visualizza il calendario del mese"""
    mese = request.args.get('mese', datetime.now().month, type=int)
    anno = request.args.get('anno', datetime.now().year, type=int)

    giorni = get_calendario(mese, anno)

    return render_template('calendario.html',
                           giorni=giorni,
                           mese=mese,
                           anno=anno)


@app.route('/giorno/<data_iso>')
def giorno_dettaglio(data_iso):
    """Visualizza il dettaglio di un giorno specifico"""
    giorno = get_giorno_liturgico(data_iso)

    if not giorno:
        return render_template('error.html', message=f'Nessun dato per {data_iso}'), 404

    lodi = get_lodi_by_giorno(giorno['id'])
    vespri = get_vespri_by_giorno(giorno['id'])
    santi = get_santi_by_giorno(giorno['id'])

    return render_template('giorno.html',
                           giorno=giorno,
                           lodi=lodi,
                           vespri=vespri,
                           santi=santi)


# ============================================
# ROUTES - LITURGY PAGES
# ============================================

@app.route('/lodi')
def lodi():
    """Visualizza le lodi di oggi"""
    data_iso = request.args.get('data', datetime.now().strftime('%Y-%m-%d'))
    giorno = get_giorno_liturgico(data_iso)

    if not giorno:
        return render_template('error.html', message='Dati non disponibili'), 404

    lodi = get_lodi_by_giorno(giorno['id'])

    if not lodi:
        return render_template('error.html', message='Lodi non disponibili per questo giorno'), 404

    return render_template('lodi.html', giorno=giorno, lodi=lodi)


@app.route('/vespri')
def vespri():
    """Visualizza i vespri di oggi"""
    data_iso = request.args.get('data', datetime.now().strftime('%Y-%m-%d'))
    giorno = get_giorno_liturgico(data_iso)

    if not giorno:
        return render_template('error.html', message='Dati non disponibili'), 404

    vespri = get_vespri_by_giorno(giorno['id'])

    if not vespri:
        return render_template('error.html', message='Vespri non disponibili per questo giorno'), 404

    return render_template('vespri.html', giorno=giorno, vespri=vespri)


@app.route('/santi')
def santi():
    """Visualizza i santi del giorno"""
    data_iso = request.args.get('data', datetime.now().strftime('%Y-%m-%d'))
    giorno = get_giorno_liturgico(data_iso)

    if not giorno:
        return render_template('error.html', message='Dati non disponibili'), 404

    santi_list = get_santi_by_giorno(giorno['id'])

    if not santi_list:
        return render_template('error.html', message='Nessun santo disponibile per questo giorno'), 404

    return render_template('santi.html', giorno=giorno, santi=santi_list)


# ============================================
# ROUTES - INFO PAGES
# ============================================

@app.route('/about')
def about():
    """Pagina chi siamo"""
    return render_template('about.html')


# ============================================
# API ENDPOINTS
# ============================================

@app.route('/api/giorno/<data_iso>')
def api_giorno(data_iso):
    """API per ottenere un giorno completo"""
    giorno = get_giorno_liturgico(data_iso)

    if not giorno:
        return jsonify({'error': 'Non trovato'}), 404

    lodi = get_lodi_by_giorno(giorno['id'])
    vespri = get_vespri_by_giorno(giorno['id'])
    santi = get_santi_by_giorno(giorno['id'])

    return jsonify({
        'giorno': dict(giorno),
        'lodi': dict(lodi) if lodi else None,
        'vespri': dict(vespri) if vespri else None,
        'santi': santi
    })


@app.route('/api/calendario/<int:anno>/<int:mese>')
def api_calendario(anno, mese):
    """API per ottenere il calendario"""
    giorni = get_calendario(mese, anno)
    return jsonify({'giorni': [dict(g) for g in giorni]})


@app.route('/api/santi/<int:anno>/<int:mese>/<int:giorno>')
def api_santi(anno, mese, giorno):
    """API per ottenere i santi di un giorno"""
    data_iso = f'{anno:04d}-{mese:02d}-{giorno:02d}'
    giorno_record = get_giorno_liturgico(data_iso)

    if not giorno_record:
        return jsonify({'error': 'Non trovato'}), 404

    santi_list = get_santi_by_giorno(giorno_record['id'])
    return jsonify({'santi': santi_list})


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', message='Pagina non trovata'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('error.html', message='Errore del server'), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=59000)