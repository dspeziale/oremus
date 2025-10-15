#!/usr/bin/env python3
"""
Applicazione Web Flask per navigare le Lodi Mattutine
UI/UX moderna e accattivante - Ottimizzata per smartphone
"""
from flask import Flask, render_template, jsonify, request
import sqlite3
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.config['DATABASE'] = 'lodi_mattutine.db'


def get_db_connection():
    """Crea connessione al database"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    """Pagina principale"""
    data_richiesta = request.args.get('data')
    conn = get_db_connection()

    if data_richiesta:
        lodi = conn.execute('SELECT * FROM lodi WHERE data = ?', (data_richiesta,)).fetchone()
    else:
        oggi = datetime.now().strftime("%Y%m%d")
        lodi = conn.execute('SELECT * FROM lodi WHERE data = ?', (oggi,)).fetchone()
        if not lodi:
            lodi = conn.execute('SELECT * FROM lodi ORDER BY data DESC LIMIT 1').fetchone()

    conn.close()
    return render_template('index.html', data=lodi['data'] if lodi else None)


@app.route('/calendario')
def calendario():
    """Pagina calendario"""
    conn = get_db_connection()
    date_disponibili = conn.execute(
        'SELECT data, data_formattata FROM lodi ORDER BY data DESC'
    ).fetchall()
    conn.close()
    return render_template('calendario.html', date=date_disponibili)


@app.route('/api/lodi/<data>')
def get_lodi(data):
    """API per ottenere le lodi"""
    conn = get_db_connection()
    lodi = conn.execute('SELECT * FROM lodi WHERE data = ?', (data,)).fetchone()

    if not lodi:
        conn.close()
        return jsonify({'error': 'Lodi non trovate'}), 404

    lodi_id = lodi['id']
    inni = conn.execute('SELECT * FROM inni WHERE lodi_id = ? ORDER BY opzione', (lodi_id,)).fetchall()
    salmodia = conn.execute('SELECT * FROM salmodia WHERE lodi_id = ? ORDER BY numero', (lodi_id,)).fetchall()
    lettura = conn.execute('SELECT * FROM lettura_breve WHERE lodi_id = ?', (lodi_id,)).fetchone()
    responsorio = conn.execute('SELECT * FROM responsorio_breve WHERE lodi_id = ?', (lodi_id,)).fetchone()
    cantico = conn.execute('SELECT * FROM cantico_evangelico WHERE lodi_id = ?', (lodi_id,)).fetchone()
    invocazioni = conn.execute('SELECT * FROM invocazioni WHERE lodi_id = ?', (lodi_id,)).fetchone()
    orazione = conn.execute('SELECT * FROM orazione WHERE lodi_id = ?', (lodi_id,)).fetchone()
    conn.close()

    response = {
        'data': lodi['data'],
        'data_formattata': lodi['data_formattata'],
        'introduzione': {
            'versetto': lodi['versetto_iniziale'],
            'risposta': lodi['risposta_versetto'],
            'dossologia': lodi['dossologia_introduzione']
        },
        'inni': [{'opzione': i['opzione'], 'lingua': i['lingua'], 'testo': i['testo']} for i in inni],
        'salmodia': [{'numero': s['numero'], 'antifona': s['antifona'], 'titolo': s['titolo'],
                      'sottotitolo': s['sottotitolo'], 'testo': s['testo']} for s in salmodia],
        'lettura_breve': {'riferimento': lettura['riferimento'] if lettura else '',
                          'testo': lettura['testo'] if lettura else ''},
        'responsorio_breve': {'testo': responsorio['testo'] if responsorio else ''},
        'cantico_evangelico': {
            'nome': cantico['nome'] if cantico else '',
            'antifona': cantico['antifona'] if cantico else '',
            'testo': cantico['testo'] if cantico else '',
            'dossologia': cantico['dossologia'] if cantico else ''
        },
        'invocazioni': {
            'introduzione': invocazioni['introduzione'] if invocazioni else '',
            'ritornello': invocazioni['ritornello'] if invocazioni else '',
            'lista': json.loads(invocazioni['invocazioni_lista']) if invocazioni else []
        },
        'orazione': {'testo': orazione['testo'] if orazione else ''},
        'conclusione': {'benedizione': lodi['benedizione_conclusione'], 'risposta': lodi['risposta_conclusione']}
    }
    return jsonify(response)


@app.route('/api/navigazione/<data>/<direzione>')
def navigazione(data, direzione):
    """Navigazione tra date"""
    conn = get_db_connection()
    if direzione == 'prev':
        risultato = conn.execute('SELECT data FROM lodi WHERE data < ? ORDER BY data DESC LIMIT 1', (data,)).fetchone()
    else:
        risultato = conn.execute('SELECT data FROM lodi WHERE data > ? ORDER BY data ASC LIMIT 1', (data,)).fetchone()
    conn.close()
    return jsonify({'data': risultato['data'] if risultato else None})


if __name__ == '__main__':
    import os

    if not os.path.exists('../templates'):
        os.makedirs('../templates')

    # Template base con design moderno
    with open('../templates/base.html', 'w', encoding='utf-8') as f:
        f.write('''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#1a1a2e">
    <title>{% block title %}Lodi Mattutine{% endblock %}</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #f59e0b;
            --dark: #1a1a2e;
            --darker: #0f0f1e;
            --light: #f8f9fa;
            --text: #e8e9ed;
            --text-muted: #a0a0b0;
            --accent: #ec4899;
            --success: #10b981;
            --gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-alt: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --card-bg: rgba(255, 255, 255, 0.05);
            --card-border: rgba(255, 255, 255, 0.1);
        }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--dark);
            color: var(--text);
            line-height: 1.7;
            overflow-x: hidden;
        }

        /* Sfondo animato */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(236, 72, 153, 0.1) 0%, transparent 50%);
            z-index: -1;
        }

        header {
            background: rgba(26, 26, 46, 0.8);
            backdrop-filter: blur(20px);
            padding: 1.5rem;
            position: sticky;
            top: 0;
            z-index: 100;
            border-bottom: 1px solid var(--card-border);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }

        header h1 {
            font-family: 'Playfair Display', serif;
            font-size: 1.8rem;
            text-align: center;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 1.5rem;
            padding-bottom: 100px;
        }

        .controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid var(--card-border);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }

        .date-display {
            font-family: 'Playfair Display', serif;
            font-size: 1rem;
            font-weight: 600;
            text-align: center;
            color: var(--text);
            flex: 1;
            line-height: 1.4;
        }

        button {
            background: var(--gradient);
            color: white;
            border: none;
            padding: 0.9rem 1.8rem;
            border-radius: 50px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
            white-space: nowrap;
        }

        button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(99, 102, 241, 0.4);
        }

        button:active:not(:disabled) {
            transform: translateY(0);
        }

        button:disabled {
            opacity: 0.3;
            cursor: not-allowed;
            box-shadow: none;
        }

        .section {
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            margin: 2rem 0;
            padding: 2rem;
            border-radius: 24px;
            border: 1px solid var(--card-border);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            animation: fadeInUp 0.5s ease;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .section-title {
            font-family: 'Playfair Display', serif;
            font-size: 1.6rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            display: flex;
            align-items: center;
            gap: 0.7rem;
        }

        .section-title::before {
            content: '✦';
            color: var(--primary);
            font-size: 1.2rem;
        }

        .verse-block {
            background: rgba(99, 102, 241, 0.05);
            padding: 1.2rem;
            border-radius: 16px;
            margin: 1rem 0;
            border-left: 4px solid var(--primary);
        }

        .verse-block strong {
            color: var(--secondary);
            font-weight: 600;
        }

        .antifona {
            font-style: italic;
            color: var(--accent);
            font-size: 1.05rem;
            padding: 1rem;
            background: rgba(236, 72, 153, 0.05);
            border-radius: 12px;
            margin: 1rem 0;
            border-left: 3px solid var(--accent);
        }

        .salmo-title {
            font-family: 'Playfair Display', serif;
            font-weight: 600;
            font-size: 1.2rem;
            color: var(--secondary);
            margin: 1.5rem 0 1rem;
        }

        pre {
            white-space: pre-wrap;
            font-family: 'Inter', sans-serif;
            line-height: 1.8;
            color: var(--text);
            font-size: 1rem;
        }

        .invocazione {
            margin: 1.2rem 0;
            padding: 1rem 1.5rem;
            background: rgba(16, 185, 129, 0.05);
            border-left: 3px solid var(--success);
            border-radius: 12px;
            transition: all 0.3s ease;
        }

        .invocazione:hover {
            background: rgba(16, 185, 129, 0.1);
            transform: translateX(5px);
        }

        nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(26, 26, 46, 0.95);
            backdrop-filter: blur(20px);
            display: flex;
            justify-content: space-around;
            padding: 1rem;
            border-top: 1px solid var(--card-border);
            box-shadow: 0 -4px 30px rgba(0, 0, 0, 0.3);
            z-index: 1000;
        }

        nav a {
            color: var(--text-muted);
            text-decoration: none;
            padding: 0.8rem 1.5rem;
            border-radius: 16px;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.3rem;
        }

        nav a .icon {
            font-size: 1.4rem;
        }

        nav a:hover, nav a.active {
            color: var(--text);
            background: var(--card-bg);
        }

        .loading {
            text-align: center;
            padding: 3rem;
            color: var(--text-muted);
            font-size: 1.1rem;
        }

        .loading::after {
            content: '...';
            animation: dots 1.5s steps(4, end) infinite;
        }

        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }

        .error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #fca5a5;
            padding: 1.5rem;
            border-radius: 16px;
            margin: 1rem 0;
        }

        /* Scrollbar personalizzata */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--darker);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary-dark);
        }

        @media (max-width: 600px) {
            header h1 {
                font-size: 1.4rem;
            }

            .container {
                padding: 1rem;
            }

            .section {
                padding: 1.5rem;
                margin: 1.5rem 0;
            }

            .section-title {
                font-size: 1.3rem;
            }

            button {
                padding: 0.7rem 1.2rem;
                font-size: 0.85rem;
            }

            .date-display {
                font-size: 0.85rem;
            }

            nav a {
                padding: 0.6rem 1rem;
                font-size: 0.8rem;
            }
        }

        {% block extra_style %}{% endblock %}
    </style>
</head>
<body>
    {% block content %}{% endblock %}

    <nav>
        <a href="/" id="nav-home">
            <span class="icon">🏠</span>
            <span>Home</span>
        </a>
        <a href="/calendario" id="nav-calendario">
            <span class="icon">📅</span>
            <span>Calendario</span>
        </a>
    </nav>

    {% block scripts %}{% endblock %}
</body>
</html>''')

    # Template index
    with open('../templates/index.html', 'w', encoding='utf-8') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Lodi Mattutine{% endblock %}

{% block content %}
<header>
    <h1>✝ Lodi Mattutine</h1>
</header>

<div class="container">
    <div class="controls">
        <button id="btn-prev" onclick="navigateDate('prev')">← Prec</button>
        <div class="date-display" id="date-display">Caricamento...</div>
        <button id="btn-next" onclick="navigateDate('next')">Succ →</button>
    </div>

    <div id="content">
        <div class="loading">Caricamento</div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
let currentData = '{{ data }}';

async function loadLodi(data) {
    const content = document.getElementById('content');
    content.innerHTML = '<div class="loading">Caricamento</div>';

    try {
        const response = await fetch(`/api/lodi/${data}`);
        if (!response.ok) throw new Error('Lodi non trovate');

        const lodi = await response.json();
        currentData = lodi.data;
        document.getElementById('date-display').textContent = lodi.data_formattata;

        let html = '';

        if (lodi.introduzione.versetto) {
            html += `
            <div class="section">
                <h2 class="section-title">Introduzione</h2>
                <div class="verse-block">
                    <p><strong>V.</strong> ${lodi.introduzione.versetto}</p>
                    <p><strong>R.</strong> ${lodi.introduzione.risposta}</p>
                </div>
                ${lodi.introduzione.dossologia ? `<pre>${lodi.introduzione.dossologia}</pre>` : ''}
            </div>`;
        }

        if (lodi.inni && lodi.inni.length > 0) {
            html += '<div class="section"><h2 class="section-title">Inno</h2>';
            lodi.inni.forEach((inno, idx) => {
                if (idx > 0) html += '<p style="margin:1rem 0;color:var(--secondary);font-weight:600;">Oppure:</p>';
                html += `<pre>${inno.testo}</pre>`;
            });
            html += '</div>';
        }

        if (lodi.salmodia && lodi.salmodia.length > 0) {
            html += '<div class="section"><h2 class="section-title">Salmodia</h2>';
            lodi.salmodia.forEach(salmo => {
                html += `
                <div class="antifona"><strong>Ant.</strong> ${salmo.antifona}</div>
                <div class="salmo-title">${salmo.titolo}</div>
                ${salmo.sottotitolo ? `<p style="font-style:italic;color:var(--text-muted);margin:0.5rem 0;">${salmo.sottotitolo}</p>` : ''}
                <pre>${salmo.testo}</pre>
                <div class="antifona">${salmo.antifona}</div>
                `;
            });
            html += '</div>';
        }

        if (lodi.lettura_breve.testo) {
            html += `
            <div class="section">
                <h2 class="section-title">Lettura Breve</h2>
                <p style="color:var(--secondary);font-weight:600;margin-bottom:1rem;">${lodi.lettura_breve.riferimento}</p>
                <pre>${lodi.lettura_breve.testo}</pre>
            </div>`;
        }

        if (lodi.responsorio_breve.testo) {
            html += `
            <div class="section">
                <h2 class="section-title">Responsorio Breve</h2>
                <pre>${lodi.responsorio_breve.testo}</pre>
            </div>`;
        }

        if (lodi.cantico_evangelico.testo) {
            html += `
            <div class="section">
                <h2 class="section-title">Cantico Evangelico</h2>
                <div class="antifona"><strong>Ant.</strong> ${lodi.cantico_evangelico.antifona}</div>
                <div class="salmo-title">${lodi.cantico_evangelico.nome}</div>
                <pre>${lodi.cantico_evangelico.testo}</pre>
                ${lodi.cantico_evangelico.dossologia ? `<pre style="margin-top:1rem;">${lodi.cantico_evangelico.dossologia}</pre>` : ''}
                <div class="antifona">${lodi.cantico_evangelico.antifona}</div>
            </div>`;
        }

        if (lodi.invocazioni.lista && lodi.invocazioni.lista.length > 0) {
            html += `
            <div class="section">
                <h2 class="section-title">Invocazioni</h2>
                <pre>${lodi.invocazioni.introduzione}</pre>
                <p style="color:var(--success);font-weight:600;margin:1rem 0;">${lodi.invocazioni.ritornello}</p>`;
            lodi.invocazioni.lista.forEach(inv => {
                html += `<div class="invocazione">${inv}</div>`;
            });
            html += `<p style="color:var(--secondary);font-weight:600;margin-top:1.5rem;">Padre nostro</p>
            </div>`;
        }

        if (lodi.orazione.testo) {
            html += `
            <div class="section">
                <h2 class="section-title">Orazione</h2>
                <p>${lodi.orazione.testo}</p>
            </div>`;
        }

        if (lodi.conclusione.benedizione) {
            html += `
            <div class="section">
                <h2 class="section-title">Conclusione</h2>
                <div class="verse-block">
                    <p><strong>V.</strong> ${lodi.conclusione.benedizione}</p>
                    <p><strong>R.</strong> ${lodi.conclusione.risposta}</p>
                </div>
            </div>`;
        }

        content.innerHTML = html;
        checkNavigationButtons();
        window.scrollTo(0, 0);

    } catch (error) {
        content.innerHTML = `<div class="error">❌ ${error.message}</div>`;
    }
}

async function navigateDate(direction) {
    try {
        const response = await fetch(`/api/navigazione/${currentData}/${direction}`);
        const result = await response.json();
        if (result.data) loadLodi(result.data);
    } catch (error) {
        console.error('Errore:', error);
    }
}

async function checkNavigationButtons() {
    try {
        const [prevRes, nextRes] = await Promise.all([
            fetch(`/api/navigazione/${currentData}/prev`),
            fetch(`/api/navigazione/${currentData}/next`)
        ]);
        const [prev, next] = await Promise.all([prevRes.json(), nextRes.json()]);
        document.getElementById('btn-prev').disabled = !prev.data;
        document.getElementById('btn-next').disabled = !next.data;
    } catch (error) {
        console.error('Errore:', error);
    }
}

if (currentData && currentData !== 'None') {
    loadLodi(currentData);
} else {
    document.getElementById('content').innerHTML = '<div class="error">Nessuna lode disponibile</div>';
}

document.getElementById('nav-home').classList.add('active');
</script>
{% endblock %}''')

    # Template calendario
    with open('../templates/calendario.html', 'w', encoding='utf-8') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Calendario{% endblock %}

{% block extra_style %}
<style>
    .calendar-grid {
        display: grid;
        gap: 1rem;
    }

    .date-card {
        background: var(--card-bg);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 20px;
        border: 1px solid var(--card-border);
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .date-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--gradient);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }

    .date-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.3);
        border-color: var(--primary);
    }

    .date-card:hover::before {
        transform: scaleX(1);
    }

    .date-card a {
        color: var(--text);
        text-decoration: none;
        display: block;
        font-size: 1.1rem;
        font-weight: 500;
    }

    .date-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        display: block;
    }
</style>
{% endblock %}

{% block content %}
<header>
    <h1>📅 Calendario</h1>
</header>

<div class="container">
    <div class="section">
        <h2 class="section-title">Date Disponibili</h2>
        <div class="calendar-grid">
            {% for data in date %}
            <div class="date-card" onclick="window.location.href='/?data={{ data['data'] }}'">
                <span class="date-icon">📖</span>
                <a href="/?data={{ data['data'] }}">{{ data['data_formattata'] }}</a>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.getElementById('nav-calendario').classList.add('active');
</script>
{% endblock %}''')

    print("\n" + "=" * 60)
    print("✨ APPLICAZIONE WEB LODI MATTUTINE - UI/UX MODERNA ✨")
    print("=" * 60)
    print("\n🎨 Design Features:")
    print("  • Dark mode elegante con effetti glassmorphism")
    print("  • Gradienti colorati e animazioni fluide")
    print("  • Typography professionale (Playfair + Inter)")
    print("  • Icons e visual feedback")
    print("  • Responsive design ottimizzato")
    print("\n🚀 Per avviare:")
    print("  1. pip install flask")
    print("  2. python app.py")
    print("  3. Apri: http://localhost:5000")
    print("=" * 60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)