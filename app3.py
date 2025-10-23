#!/usr/bin/env python3
"""
OREMUS - Applicazione per visualizzare la Liturgia delle Ore
Versione unificata che combina app.py e app2.py
Dashboard con navigazione per date, santi del giorno, lodi e vespri
"""
import random
import sqlite3
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'oremus'
app.config['JSON_AS_ASCII'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
CORS(app)

# ============================================
# DATABASE CONFIGURATION
# ============================================
# Prova più percorsi per trovare il database
DB_PATHS = [
    'instance/oremus.db',
    os.path.join(os.path.dirname(__file__), 'instance', 'oremus.db'),
    os.path.abspath('instance/oremus.db'),
    '../instance/oremus.db',
    r'instance\oremus.db'
]

DB_PATH = None
for path in DB_PATHS:
    try:
        if os.path.exists(path):
            DB_PATH = os.path.abspath(path)
            print(f"✅ Database trovato: {DB_PATH}")
            break
    except:
        pass

if DB_PATH is None:
    print(f"⚠️  Database non trovato, provo con: {DB_PATHS[0]}")
    DB_PATH = DB_PATHS[0]


# ============================================
# DATABASE HELPERS
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


def get_today_date():
    """Get today's date in ISO format (YYYYMMDD)"""
    return datetime.now().strftime('%Y%m%d')


def get_today_formatted():
    """Get today's date in formatted format"""
    return datetime.now().strftime('%d %B %Y')


def db_exists():
    """Check if database exists and is accessible"""
    try:
        return os.path.exists(DB_PATH) if DB_PATH else False
    except:
        return False


def get_all_dates():
    """Get all available dates in database - optimized version"""
    try:
        conn = get_db_connection()
        if conn is None:
            return []

        cursor = conn.cursor()

        # Prova prima con data_iso, poi con fallback a data
        try:
            cursor.execute('''
                SELECT DISTINCT data_iso, giorno_settimana 
                FROM giorni_liturgici 
                ORDER BY data_iso DESC 
                LIMIT 100
            ''')
        except:
            cursor.execute('''
                SELECT DISTINCT data, giorno_settimana 
                FROM giorni_liturgici 
                ORDER BY data DESC 
                LIMIT 100
            ''')

        dates = []
        for row in cursor.fetchall():
            dates.append({
                'data': row[0],
                'giorno_settimana': row[1] if len(row) > 1 else ''
            })

        conn.close()
        return dates
    except Exception as e:
        print(f"❌ Errore get_all_dates: {e}")
        return []


def get_giorno_by_data(data_iso):
    """Recupera i dati completi di un giorno specifico"""
    try:
        conn = get_db_connection()
        if conn is None:
            return None

        cursor = conn.cursor()

        # Recupera il giorno liturgico
        cursor.execute('''
            SELECT * FROM giorni_liturgici WHERE data_iso = ? OR data = ?
        ''', (data_iso, data_iso))
        giorno_row = cursor.fetchone()

        if not giorno_row:
            conn.close()
            return None

        giorno = dict_from_row(giorno_row)
        giorno_id = giorno['id']

        # Recupera lodi
        cursor.execute('''
            SELECT * FROM lodi_mattutine WHERE giorno_id = ?
        ''', (giorno_id,))
        lodi = dict_from_row(cursor.fetchone())

        # Recupera vespri
        cursor.execute('''
            SELECT * FROM vespri WHERE giorno_id = ?
        ''', (giorno_id,))
        vespri = dict_from_row(cursor.fetchone())

        # Recupera santi
        cursor.execute('''
            SELECT * FROM santi WHERE giorno_id = ? ORDER BY tipo DESC
        ''', (giorno_id,))
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
        print(f"❌ Errore get_giorno_by_data: {e}")
        return None


# ============================================
# HOME & MAIN ROUTES
# ============================================
@app.route('/')
def index():
    """Home page - Mostra il giorno odierno o il primo disponibile"""
    try:
        if not db_exists():
            print(f"⚠️  DB non disponibile")
            return render_template('index.html', giorno=None, santi=[], lodi=None, vespri=None,
                                   all_dates=[], today=get_today_date(), error="Database non disponibile")

        today = get_today_date()
        print(f"📅 Cercando dati per: {today}")

        # Prova a recuperare il giorno odierno
        giorno_data = get_giorno_by_data(today)

        # Se non esiste oggi, prendi il primo disponibile
        if not giorno_data:
            print(f"⚠️  Nessun giorno trovato per {today}")
            all_dates = get_all_dates()
            if all_dates:
                giorno_data = get_giorno_by_data(all_dates[0]['data'])
                if giorno_data:
                    today = all_dates[0]['data']
            else:
                return render_template('index.html', giorno=None, santi=[], lodi=None, vespri=None,
                                       all_dates=[], today=today, error="Nessun giorno liturgico nel database")

        all_dates = get_all_dates()

        return render_template('index.html',
                               giorno=giorno_data['giorno'] if giorno_data else None,
                               santi=giorno_data['santi'] if giorno_data else [],
                               lodi=giorno_data['lodi'] if giorno_data else None,
                               vespri=giorno_data['vespri'] if giorno_data else None,
                               all_dates=all_dates,
                               today=today,
                               error=None)

    except Exception as e:
        print(f"❌ Errore in index: {e}")
        import traceback
        traceback.print_exc()
        return render_template('index.html', giorno=None, santi=[], lodi=None, vespri=None,
                               all_dates=[], today=get_today_date(), error=str(e))


# ============================================
# LITURGIA ROUTES
# ============================================
@app.route('/giorno/<data>')
def giorno(data):
    """Visualizza un giorno specifico"""
    try:
        if not db_exists():
            return render_template('error.html', message='Database non disponibile'), 500

        giorno_data = get_giorno_by_data(data)
        all_dates = get_all_dates()

        if not giorno_data:
            return render_template('error.html', message='Giorno non trovato'), 404

        return render_template('index.html',
                               giorno=giorno_data['giorno'],
                               santi=giorno_data['santi'],
                               lodi=giorno_data['lodi'],
                               vespri=giorno_data['vespri'],
                               all_dates=all_dates,
                               today=data,
                               error=None)

    except Exception as e:
        print(f"❌ Errore in giorno: {e}")
        return render_template('error.html', message=str(e)), 500


@app.route('/lodi/<data>')
def lodi_giorno(data):
    """Lodi Mattutine per un giorno specifico"""
    try:
        if not db_exists():
            return render_template('lodi.html', lodi=None, giorno=None, all_dates=[],
                                   error="Database non disponibile")

        giorno_data = get_giorno_by_data(data)
        all_dates = get_all_dates()

        if not giorno_data:
            return render_template('error.html', message='Giorno non trovato'), 404

        return render_template('lodi.html',
                               lodi=giorno_data['lodi'],
                               giorno=giorno_data['giorno'],
                               all_dates=all_dates,
                               today=data,
                               error=None)

    except Exception as e:
        print(f"❌ Errore in lodi_giorno: {e}")
        return render_template('error.html', message=str(e)), 500


@app.route('/vespri/<data>')
def vespri_giorno(data):
    """Vespri per un giorno specifico"""
    try:
        if not db_exists():
            return render_template('vespri.html', vespri=None, giorno=None, all_dates=[],
                                   error="Database non disponibile")

        giorno_data = get_giorno_by_data(data)
        all_dates = get_all_dates()

        if not giorno_data:
            return render_template('error.html', message='Giorno non trovato'), 404

        return render_template('vespri.html',
                               vespri=giorno_data['vespri'],
                               giorno=giorno_data['giorno'],
                               all_dates=all_dates,
                               today=data,
                               error=None)

    except Exception as e:
        print(f"❌ Errore in vespri_giorno: {e}")
        return render_template('error.html', message=str(e)), 500


# ============================================
# DASHBOARD ROUTES
# ============================================
@app.route('/dashboard')
def dashboard():
    """Main dashboard view"""
    try:
        if not db_exists():
            return render_template('dashboard.html', stats=None, error="Database non disponibile")

        stats = get_dashboard_stats_data()
        return render_template('dashboard.html', stats=stats, error=None)

    except Exception as e:
        print(f"❌ Errore in dashboard: {e}")
        return render_template('dashboard.html', stats=None, error=str(e))


@app.route('/dashboard/1')
def dashboard_1():
    """Dashboard variant 1"""
    return dashboard()


# ============================================
# CALENDARIO ROUTE
# ============================================
@app.route('/calendario')
def calendario():
    """Visualizza il calendario interattivo"""
    try:
        if not db_exists():
            return render_template('calendario.html', all_dates=[], today=get_today_date(),
                                   error="Database non disponibile")

        all_dates = get_all_dates()
        today = get_today_date()

        return render_template('calendario.html',
                               all_dates=all_dates,
                               today=today,
                               error=None)

    except Exception as e:
        print(f"❌ Errore in calendario: {e}")
        return render_template('calendario.html', all_dates=[], today=get_today_date(),
                               error=str(e))


# ============================================
# USER MANAGEMENT ROUTES
# ============================================
@app.route('/users')
def users():
    """List of all users"""
    try:
        if not db_exists():
            return render_template('users.html', users=[], error="Database non disponibile")

        conn = get_db_connection()
        if conn is None:
            return render_template('users.html', users=[], error="Errore connessione DB")

        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, nome, email, ruolo, data_registrazione 
            FROM utenti 
            WHERE is_active = 1
            ORDER BY data_registrazione DESC
        ''')
        users_list = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()

        print(f"✅ Caricati {len(users_list)} utenti dal database")
        return render_template('users.html', users=users_list, error=None)

    except Exception as e:
        print(f"❌ Errore in users: {e}")
        return render_template('users.html', users=[], error=str(e))


@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    """Add new user"""
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
                INSERT INTO utenti (nome, email, password, telefono, ruolo, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (
                data.get('nome'),
                data.get('email'),
                data.get('password', 'temp'),
                data.get('telefono'),
                data.get('ruolo', 'user')
            ))

            conn.commit()
            conn.close()

            print(f"✅ Utente aggiunto: {data.get('nome')}")
            return jsonify({'status': 'success', 'message': 'Utente aggiunto con successo'})
        except Exception as e:
            print(f"❌ Errore in add_user: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 400

    return render_template('add_user.html')


@app.route('/users/<int:user_id>')
def view_user(user_id):
    """View specific user details"""
    try:
        if not db_exists():
            return render_template('error.html', message='Database non disponibile'), 500

        conn = get_db_connection()
        if conn is None:
            return render_template('error.html', message='Errore connessione DB'), 500

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM utenti WHERE id = ?', (user_id,))
        user = dict_from_row(cursor.fetchone())
        conn.close()

        if not user:
            return render_template('error.html', message='Utente non trovato'), 404

        print(f"✅ Caricato utente: {user['nome']}")
        return render_template('view_user.html', user=user)

    except Exception as e:
        print(f"❌ Errore in view_user: {e}")
        return render_template('error.html', message='Errore nel caricamento utente'), 500


@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    """Edit specific user"""
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
                SET nome = ?, email = ?, telefono = ?, ruolo = ?
                WHERE id = ?
            ''', (
                data.get('nome'),
                data.get('email'),
                data.get('telefono'),
                data.get('ruolo'),
                user_id
            ))

            conn.commit()
            conn.close()

            print(f"✅ Utente {user_id} aggiornato")
            return jsonify({'status': 'success', 'message': 'Utente aggiornato con successo'})
        except Exception as e:
            print(f"❌ Errore in edit_user POST: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 400

    try:
        if not db_exists():
            return render_template('error.html', message='Database non disponibile'), 500

        conn = get_db_connection()
        if conn is None:
            return render_template('error.html', message='Errore connessione DB'), 500

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM utenti WHERE id = ?', (user_id,))
        user = dict_from_row(cursor.fetchone())
        conn.close()

        return render_template('add_user.html', user=user)

    except Exception as e:
        print(f"❌ Errore in edit_user GET: {e}")
        return render_template('error.html', message='Errore nel caricamento utente'), 500


@app.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Delete specific user"""
    try:
        if not db_exists():
            return jsonify({'status': 'error', 'message': 'Database non disponibile'}), 400

        conn = get_db_connection()
        if conn is None:
            return jsonify({'status': 'error', 'message': 'Errore connessione DB'}), 400

        cursor = conn.cursor()
        cursor.execute('DELETE FROM utenti WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()

        print(f"✅ Utente {user_id} eliminato")
        return jsonify({'status': 'success', 'message': 'Utente eliminato con successo'})
    except Exception as e:
        print(f"❌ Errore in delete_user: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400


# ============================================
# USER PROFILE ROUTES
# ============================================
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


@app.route('/logout')
def logout():
    """Logout user and redirect to home"""
    return redirect(url_for('index'))


# ============================================
# API ENDPOINTS
# ============================================
def get_dashboard_stats_data():
    """Calcola le statistiche per il dashboard"""
    try:
        conn = get_db_connection()
        if conn is None:
            return {
                'total_users': 0, 'total_days': 0, 'new_users': 0,
                'active_sessions': 0, 'total_prayers': 0
            }

        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM utenti WHERE is_active = 1')
        total_users = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM giorni_liturgici')
        total_days = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM santi')
        total_saints = cursor.fetchone()[0]

        conn.close()

        stats = {
            'total_users': total_users,
            'total_days': total_days,
            'total_saints': total_saints,
            'new_users': random.randint(1, 10),
            'active_sessions': random.randint(5, 50),
            'total_prayers': total_days * 2
        }
        print(f"✅ Stats: {stats}")
        return stats

    except Exception as e:
        print(f"❌ Errore in get_dashboard_stats_data: {e}")
        return {
            'total_users': 0, 'total_days': 0, 'new_users': 0,
            'active_sessions': 0, 'total_prayers': 0
        }


@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """API endpoint to get dashboard statistics"""
    stats = get_dashboard_stats_data()
    return jsonify(stats)


@app.route('/api/dates')
def api_dates():
    """API: Ritorna tutte le date disponibili"""
    try:
        all_dates = get_all_dates()
        return jsonify({
            'status': 'success',
            'dates': all_dates,
            'total': len(all_dates)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'dates': []
        }), 500


@app.route('/api/giorno/<data>')
def api_giorno(data):
    """API: Ritorna i dati completi di un giorno specifico"""
    try:
        giorno_data = get_giorno_by_data(data)

        if not giorno_data:
            return jsonify({'status': 'error', 'message': 'Giorno non trovato'}), 404

        return jsonify({
            'status': 'success',
            'giorno': giorno_data['giorno'],
            'santi': giorno_data['santi'],
            'lodi': giorno_data['lodi'],
            'vespri': giorno_data['vespri']
        })

    except Exception as e:
        print(f"❌ Errore in api_giorno: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/dashboard/giorni')
def get_dashboard_giorni():
    """API endpoint to get all liturgical days with their saints from database"""
    try:
        if not db_exists():
            return jsonify({
                'status': 'error',
                'message': 'Database non disponibile',
                'giorni': []
            }), 500

        conn = get_db_connection()
        if conn is None:
            return jsonify({
                'status': 'error',
                'message': 'Errore connessione DB',
                'giorni': []
            }), 500

        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                g.id,
                g.data,
                g.data_iso,
                g.giorno_settimana
            FROM giorni_liturgici g
            ORDER BY g.data_iso ASC
        ''')

        giorni = []
        for row in cursor.fetchall():
            row_dict = dict_from_row(row)
            giorni.append({
                'id': row_dict['id'],
                'data': row_dict.get('data'),
                'data_iso': row_dict.get('data_iso'),
                'giorno_settimana': row_dict.get('giorno_settimana')
            })

        conn.close()

        return jsonify({
            'status': 'success',
            'giorni': giorni,
            'total': len(giorni)
        })

    except Exception as e:
        print(f"❌ Errore in get_dashboard_giorni: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'giorni': []
        }), 500


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
# ERROR HANDLERS
# ============================================
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', message='Pagina non trovata'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('error.html', message='Errore interno del server'), 500


# ============================================
# DATABASE QUERY HELPERS - SQLITE3 DIRETTO ✅
# ============================================

def get_giorno_id_by_iso_date(date_iso):
    """Recupera l'ID del giorno dalla data ISO (YYYYMMDD)"""
    try:
        conn = get_db_connection()
        if conn is None:
            return None

        cursor = conn.cursor()
        cursor.execute('SELECT id FROM giorni_liturgici WHERE data_iso = ?', (date_iso,))
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None
    except Exception as e:
        print(f"❌ Errore nel recupero ID giorno: {e}")
        return None


def get_giorno_completo_by_iso(date_iso):
    """Recupera tutti i dati di un giorno da data ISO"""
    try:
        conn = get_db_connection()
        if conn is None:
            return None

        cursor = conn.cursor()

        cursor.execute('SELECT * FROM giorni_liturgici WHERE data_iso = ?', (date_iso,))
        giorno_row = cursor.fetchone()

        if not giorno_row:
            conn.close()
            return None

        giorno = dict_from_row(giorno_row)
        giorno_id = giorno['id']

        cursor.execute('SELECT * FROM lodi_mattutine WHERE giorno_id = ?', (giorno_id,))
        lodi = dict_from_row(cursor.fetchone())

        cursor.execute('SELECT * FROM vespri WHERE giorno_id = ?', (giorno_id,))
        vespri = dict_from_row(cursor.fetchone())

        cursor.execute('SELECT * FROM santi WHERE giorno_id = ? ORDER BY tipo DESC', (giorno_id,))
        santi = [dict_from_row(row) for row in cursor.fetchall()]

        conn.close()

        return {
            'giorno': giorno,
            'lodi': lodi,
            'vespri': vespri,
            'santi': santi
        }
    except Exception as e:
        print(f"❌ Errore recupero giorno completo: {e}")
        return None


def get_lodi_by_giorno_id(giorno_id):
    """Recupera Lodi di un giorno"""
    try:
        conn = get_db_connection()
        if conn is None:
            return None

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM lodi_mattutine WHERE giorno_id = ?', (giorno_id,))
        result = cursor.fetchone()
        conn.close()

        return dict_from_row(result)
    except Exception as e:
        print(f"❌ Errore recupero Lodi: {e}")
        return None


def get_vespri_by_giorno_id(giorno_id):
    """Recupera Vespri di un giorno"""
    try:
        conn = get_db_connection()
        if conn is None:
            return None

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM vespri WHERE giorno_id = ?', (giorno_id,))
        result = cursor.fetchone()
        conn.close()

        return dict_from_row(result)
    except Exception as e:
        print(f"❌ Errore recupero Vespri: {e}")
        return None


def get_santi_by_giorno_id(giorno_id):
    """Recupera Santi di un giorno"""
    try:
        conn = get_db_connection()
        if conn is None:
            return []

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM santi WHERE giorno_id = ? ORDER BY tipo DESC', (giorno_id,))
        results = cursor.fetchall()
        conn.close()

        return [dict_from_row(row) for row in results]
    except Exception as e:
        print(f"❌ Errore recupero Santi: {e}")
        return []


def get_dashboard_stats():
    """Recupera statistiche per dashboard"""
    try:
        conn = get_db_connection()
        if conn is None:
            return {'total_days': 0, 'total_users': 0, 'total_prayers': 0, 'new_users': 0}

        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM giorni_liturgici')
        total_days = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM utenti')
        total_users = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM lodi_mattutine')
        lodi_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM vespri')
        vespri_count = cursor.fetchone()[0]

        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute('SELECT COUNT(*) FROM utenti WHERE data_registrazione > ?', (week_ago,))
        new_users = cursor.fetchone()[0]

        conn.close()

        return {
            'total_days': total_days,
            'total_users': total_users,
            'total_prayers': lodi_count + vespri_count,
            'new_users': new_users
        }
    except Exception as e:
        print(f"❌ Errore recupero stats: {e}")
        return {'total_days': 0, 'total_users': 0, 'total_prayers': 0, 'new_users': 0}


def get_dashboard_giorni():
    """Recupera giorni con santi per dashboard"""
    try:
        conn = get_db_connection()
        if conn is None:
            return []

        cursor = conn.cursor()
        query = '''
            SELECT 
                g.id, g.data, g.data_iso, g.giorno_settimana,
                (SELECT nome_santo FROM santi WHERE giorno_id = g.id AND tipo = 'principale' LIMIT 1) as santo_principale
            FROM giorni_liturgici g
            ORDER BY g.data_iso DESC
            LIMIT 60
        '''
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()

        return [dict_from_row(row) for row in results]
    except Exception as e:
        print(f"❌ Errore recupero giorni dashboard: {e}")
        return []


# ============================================
# ROUTES: Dashboard e API
# ============================================


@app.route('/api/dashboard/stats')
def dashboard_stats():
    """API: Statistiche dashboard"""
    return jsonify(get_dashboard_stats())


@app.route('/api/dashboard/giorni')
def api_dashboard_giorni():
    """API: Giorni per dashboard"""
    return jsonify({'giorni': get_dashboard_giorni()})


# ============================================
# ROUTE: Lodi Mattutine
# ============================================

@app.route('/lodi')
def lodi_route():
    """Pagina Lodi Mattutine"""
    try:
        today = get_today_date()
        giorno_id = get_giorno_id_by_iso_date(today)

        if not giorno_id:
            return render_template('error.html', message="Dati non disponibili per oggi"), 404

        giorno_data = get_giorno_completo_by_iso(today)
        lodi = get_lodi_by_giorno_id(giorno_id) if giorno_data else None

        return render_template('lodi.html', lodi=lodi, giorno=giorno_data['giorno'] if giorno_data else None)
    except Exception as e:
        print(f"❌ Errore Lodi: {e}")
        return render_template('error.html', message=f"Errore: {str(e)}"), 500


# ============================================
# ROUTE: Vespri
# ============================================

@app.route('/vespri')
def vespri_route():
    """Pagina Vespri"""
    try:
        today = get_today_date()
        giorno_id = get_giorno_id_by_iso_date(today)

        if not giorno_id:
            return render_template('error.html', message="Dati non disponibili per oggi"), 404

        giorno_data = get_giorno_completo_by_iso(today)
        vespri = get_vespri_by_giorno_id(giorno_id) if giorno_data else None

        return render_template('vespri.html', vespri=vespri, giorno=giorno_data['giorno'] if giorno_data else None)
    except Exception as e:
        print(f"❌ Errore Vespri: {e}")
        return render_template('error.html', message=f"Errore: {str(e)}"), 500


# ============================================
# ROUTE: Santi del Giorno
# ============================================

@app.route('/santi')
def santi_route():
    """Pagina Santi del Giorno"""
    try:
        today = get_today_date()
        giorno_id = get_giorno_id_by_iso_date(today)

        if not giorno_id:
            return render_template('error.html', message="Dati non disponibili per oggi"), 404

        giorno_data = get_giorno_completo_by_iso(today)
        santi = get_santi_by_giorno_id(giorno_id) if giorno_data else []

        return render_template('index.html', santi=santi, giorno=giorno_data['giorno'] if giorno_data else None)
    except Exception as e:
        print(f"❌ Errore Santi: {e}")
        return render_template('error.html', message=f"Errore: {str(e)}"), 500


# ============================================
# MAIN - Server startup
# ============================================
if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🚀 OREMUS - Liturgia Divina (Versione Unificata 3.0 - SQLite3)")
    print("=" * 70)
    print(f"📁 Database path: {DB_PATH}")
    print(f"✅ Database exists: {db_exists()}")

    if db_exists():
        try:
            dates = get_all_dates()
            print(f"📅 Date disponibili: {len(dates)}")
            if dates:
                print(f"   Prima: {dates[-1]['data'] if dates else 'N/A'}")
                print(f"   Ultima: {dates[0]['data'] if dates else 'N/A'}")
        except Exception as e:
            print(f"⚠️  Errore nel caricamento date: {e}")

    print("=" * 70)
    print(f"🌐 Server running on: http://0.0.0.0:5000")
    print("=" * 70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)