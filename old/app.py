import random
import sqlite3
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'oremus'
app.config['JSON_AS_ASCII'] = False
CORS(app)

# ============================================
# DATABASE CONFIGURATION
# ============================================
# Prova più percorsi
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
    """Get today's date in ISO format"""
    return datetime.now().strftime('%Y-%m-%d')


def db_exists():
    """Check if database exists and is accessible"""
    try:
        return os.path.exists(DB_PATH) if DB_PATH else False
    except:
        return False


def get_all_dates():
    """Get all available dates in database"""
    try:
        conn = get_db_connection()
        if conn is None:
            return []

        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT data_iso FROM giorni_liturgici ORDER BY data_iso DESC LIMIT 10')
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()
        return dates
    except Exception as e:
        print(f"❌ Errore get_all_dates: {e}")
        return []


# ============================================
# HOME & MAIN ROUTES
# ============================================
@app.route('/')
def index():
    """Home page - Oggi (Today)"""
    try:
        if not db_exists():
            print(f"⚠️  DB non disponibile")
            return render_template('index.html', giorno=None, santi=[], lodi=None, vespri=None,
                                   error="Database non disponibile")

        conn = get_db_connection()
        if conn is None:
            return render_template('index.html', giorno=None, santi=[], lodi=None, vespri=None,
                                   error="Errore connessione DB")

        cursor = conn.cursor()

        today = get_today_date()
        print(f"📅 Cercando dati per: {today}")

        # Prendi il giorno liturgico di oggi
        cursor.execute('SELECT * FROM giorni_liturgici WHERE data_iso = ?', (today,))
        giorno = dict_from_row(cursor.fetchone())

        if giorno:
            giorno_id = giorno['id']
            print(f"✅ Giorno trovato: {giorno['data']}")
        else:
            print(f"⚠️  Nessun giorno trovato per {today}")
            # Prendi il primo giorno disponibile
            cursor.execute('SELECT * FROM giorni_liturgici ORDER BY data_iso DESC LIMIT 1')
            giorno = dict_from_row(cursor.fetchone())
            if not giorno:
                conn.close()
                return render_template('index.html', giorno=None, santi=[], lodi=None, vespri=None,
                                       error="Nessun giorno liturgico nel database")
            giorno_id = giorno['id']
            print(f"📅 Usando: {giorno['data']}")

        # Prendi i santi del giorno
        cursor.execute('SELECT * FROM santi WHERE giorno_id = ? ORDER BY tipo DESC', (giorno_id,))
        santi = [dict(row) for row in cursor.fetchall()]
        print(f"✅ Santi trovati: {len(santi)}")

        # Prendi le Lodi Mattutine
        cursor.execute('SELECT * FROM lodi_mattutine WHERE giorno_id = ?', (giorno_id,))
        lodi = dict_from_row(cursor.fetchone())
        if lodi:
            print(f"✅ Lodi trovate")

        # Prendi i Vespri
        cursor.execute('SELECT * FROM vespri WHERE giorno_id = ?', (giorno_id,))
        vespri = dict_from_row(cursor.fetchone())
        if vespri:
            print(f"✅ Vespri trovati")

        conn.close()

        return render_template('index.html', giorno=giorno, santi=santi, lodi=lodi, vespri=vespri, error=None)

    except Exception as e:
        print(f"❌ Errore in index: {e}")
        import traceback
        traceback.print_exc()
        return render_template('index.html', giorno=None, santi=[], lodi=None, vespri=None, error=str(e))


# ============================================
# LITURGIA ROUTES
# ============================================
@app.route('/lodi')
def lodi():
    """Lodi Mattutine (Morning Prayers)"""
    try:
        if not db_exists():
            return render_template('lodi.html', lodi=None, giorno=None, error="Database non disponibile")

        conn = get_db_connection()
        if conn is None:
            return render_template('lodi.html', lodi=None, giorno=None, error="Errore connessione DB")

        cursor = conn.cursor()
        today = get_today_date()

        # Prendi le Lodi Mattutine
        cursor.execute('''
            SELECT lm.* FROM lodi_mattutine lm
            INNER JOIN giorni_liturgici gl ON lm.giorno_id = gl.id
            WHERE gl.data_iso = ?
        ''', (today,))
        lodi_data = dict_from_row(cursor.fetchone())

        if not lodi_data:
            cursor.execute('SELECT gl.* FROM giorni_liturgici gl ORDER BY gl.data_iso DESC LIMIT 1')
            giorno = dict_from_row(cursor.fetchone())
            if giorno:
                cursor.execute('SELECT * FROM lodi_mattutine WHERE giorno_id = ?', (giorno['id'],))
                lodi_data = dict_from_row(cursor.fetchone())
        else:
            cursor.execute('SELECT * FROM giorni_liturgici WHERE data_iso = ?', (today,))
            giorno = dict_from_row(cursor.fetchone())

        conn.close()

        return render_template('lodi.html', lodi=lodi_data, giorno=giorno, error=None)

    except Exception as e:
        print(f"❌ Errore in lodi: {e}")
        return render_template('lodi.html', lodi=None, giorno=None, error=str(e))


@app.route('/vespri')
def vespri():
    """Vespri (Evening Prayers)"""
    try:
        if not db_exists():
            return render_template('vespri.html', vespri=None, giorno=None, error="Database non disponibile")

        conn = get_db_connection()
        if conn is None:
            return render_template('vespri.html', vespri=None, giorno=None, error="Errore connessione DB")

        cursor = conn.cursor()
        today = get_today_date()

        # Prendi i Vespri
        cursor.execute('''
            SELECT v.* FROM vespri v
            INNER JOIN giorni_liturgici gl ON v.giorno_id = gl.id
            WHERE gl.data_iso = ?
        ''', (today,))
        vespri_data = dict_from_row(cursor.fetchone())

        if not vespri_data:
            cursor.execute('SELECT gl.* FROM giorni_liturgici gl ORDER BY gl.data_iso DESC LIMIT 1')
            giorno = dict_from_row(cursor.fetchone())
            if giorno:
                cursor.execute('SELECT * FROM vespri WHERE giorno_id = ?', (giorno['id'],))
                vespri_data = dict_from_row(cursor.fetchone())
        else:
            cursor.execute('SELECT * FROM giorni_liturgici WHERE data_iso = ?', (today,))
            giorno = dict_from_row(cursor.fetchone())

        conn.close()

        return render_template('vespri.html', vespri=vespri_data, giorno=giorno, error=None)

    except Exception as e:
        print(f"❌ Errore in vespri: {e}")
        return render_template('vespri.html', vespri=None, giorno=None, error=str(e))


# ============================================
# DASHBOARD ROUTES
# ============================================
@app.route('/dashboard')
def dashboard():
    """Main dashboard view"""
    return render_template('dashboard.html')


@app.route('/dashboard/1')
def dashboard_1():
    """Dashboard variant 1"""
    return render_template('dashboard.html')


@app.route('/dashboard/2')
def dashboard_2():
    """Dashboard variant 2"""
    return render_template('dashboard.html')


@app.route('/dashboard/3')
def dashboard_3():
    """Dashboard variant 3"""
    return render_template('dashboard.html')


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
        users_list = [dict(row) for row in cursor.fetchall()]
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
@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """API endpoint to get dashboard statistics"""
    try:
        if not db_exists():
            return jsonify(
                {'total_users': 0, 'total_days': 0, 'new_users': 0, 'active_sessions': 0, 'total_prayers': 0})

        conn = get_db_connection()
        if conn is None:
            return jsonify(
                {'total_users': 0, 'total_days': 0, 'new_users': 0, 'active_sessions': 0, 'total_prayers': 0})

        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM utenti WHERE is_active = 1')
        total_users = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM giorni_liturgici')
        total_days = cursor.fetchone()[0]

        conn.close()

        stats = {
            'total_users': total_users,
            'total_days': total_days,
            'new_users': random.randint(1, 10),
            'active_sessions': random.randint(5, 50),
            'total_prayers': total_days * 2
        }
        print(f"✅ Stats: {stats}")
        return jsonify(stats)

    except Exception as e:
        print(f"❌ Errore in stats: {e}")
        return jsonify({'total_users': 0, 'total_days': 0, 'new_users': 0, 'active_sessions': 0, 'total_prayers': 0})


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


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🚀 OREMUS - Liturgia Divina")
    print("=" * 70)
    print(f"📁 Database path: {DB_PATH}")
    print(f"✅ Database exists: {db_exists()}")
    if db_exists():
        try:
            dates = get_all_dates()
            print(f"📅 Date disponibili: {dates[:3]}")
        except Exception as e:
            print(f"⚠️  Errore nel caricamento date: {e}")
    print("=" * 70 + "\n")
    app.run(debug=True, host='0.0.0.0', port=59000)