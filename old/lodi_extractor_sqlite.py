#!/usr/bin/env python3
"""
Applicazione Web Flask per navigare le Lodi Mattutine
Con AdminLTE 3 - Dashboard Professionale
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


def get_statistics():
    """Ottieni statistiche generali"""
    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) as count FROM lodi').fetchone()['count']
    oldest = conn.execute('SELECT data_formattata FROM lodi ORDER BY data ASC LIMIT 1').fetchone()
    newest = conn.execute('SELECT data_formattata FROM lodi ORDER BY data DESC LIMIT 1').fetchone()
    conn.close()
    return {
        'total': total,
        'oldest': oldest['data_formattata'] if oldest else 'N/A',
        'newest': newest['data_formattata'] if newest else 'N/A'
    }


@app.route('/')
def index():
    """Dashboard principale"""
    stats = get_statistics()
    return render_template('index.html', stats=stats)


@app.route('/lodi')
def lodi_view():
    """Visualizzazione lodi"""
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
    return render_template('lodi.html', data=lodi['data'] if lodi else None)


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
    if not os.path.exists('../static'):
        os.makedirs('../static')

    # Template base AdminLTE
    with open('../templates/base.html', 'w', encoding='utf-8') as f:
        f.write('''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Lodi Mattutine{% endblock %}</title>

    <!-- Google Font: Source Sans Pro -->
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,400i,700&display=fallback">
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- AdminLTE -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/css/adminlte.min.css">

    <style>
        .content-wrapper {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }

        .liturgy-card {
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }

        .liturgy-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        }

        .section-title {
            color: #6366f1;
            font-weight: 600;
            font-size: 1.4rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #6366f1;
        }

        .antifona {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            font-style: italic;
            margin: 1rem 0;
        }

        .salmo-text {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #6366f1;
            line-height: 1.8;
        }

        .verse-block {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
        }

        .invocazione-item {
            background: #e8f5e9;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            border-left: 4px solid #4caf50;
        }

        .brand-link {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        }

        .nav-icon {
            color: #6366f1;
        }

        .nav-link.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
        }

        .nav-link.active .nav-icon {
            color: white !important;
        }

        @media print {
            .main-sidebar, .main-header, .content-header {
                display: none !important;
            }
            .content-wrapper {
                margin-left: 0 !important;
                background: white !important;
            }
        }
    </style>

    {% block extra_css %}{% endblock %}
</head>
<body class="hold-transition sidebar-mini layout-fixed">
<div class="wrapper">

    <!-- Navbar -->
    <nav class="main-header navbar navbar-expand navbar-white navbar-light">
        <!-- Left navbar links -->
        <ul class="navbar-nav">
            <li class="nav-item">
                <a class="nav-link" data-widget="pushmenu" href="#" role="button"><i class="fas fa-bars"></i></a>
            </li>
            <li class="nav-item d-none d-sm-inline-block">
                <a href="/" class="nav-link">Home</a>
            </li>
            <li class="nav-item d-none d-sm-inline-block">
                <a href="/lodi" class="nav-link">Lodi</a>
            </li>
        </ul>

        <!-- Right navbar links -->
        <ul class="navbar-nav ml-auto">
            <li class="nav-item">
                <a class="nav-link" data-widget="fullscreen" href="#" role="button">
                    <i class="fas fa-expand-arrows-alt"></i>
                </a>
            </li>
        </ul>
    </nav>

    <!-- Main Sidebar Container -->
    <aside class="main-sidebar sidebar-dark-primary elevation-4">
        <!-- Brand Logo -->
        <a href="/" class="brand-link">
            <i class="fas fa-cross brand-image ml-3" style="font-size: 2rem;"></i>
            <span class="brand-text font-weight-light">Lodi Mattutine</span>
        </a>

        <!-- Sidebar -->
        <div class="sidebar">
            <!-- Sidebar Menu -->
            <nav class="mt-2">
                <ul class="nav nav-pills nav-sidebar flex-column" data-widget="treeview" role="menu">
                    <li class="nav-item">
                        <a href="/" class="nav-link {% if request.path == '/' %}active{% endif %}">
                            <i class="nav-icon fas fa-tachometer-alt"></i>
                            <p>Dashboard</p>
                        </a>
                    </li>
                    <li class="nav-item">
                        <a href="/lodi" class="nav-link {% if request.path == '/lodi' %}active{% endif %}">
                            <i class="nav-icon fas fa-book-open"></i>
                            <p>Lodi del Giorno</p>
                        </a>
                    </li>
                    <li class="nav-item">
                        <a href="/calendario" class="nav-link {% if request.path == '/calendario' %}active{% endif %}">
                            <i class="nav-icon fas fa-calendar-alt"></i>
                            <p>Calendario</p>
                        </a>
                    </li>
                    <li class="nav-header">STRUMENTI</li>
                    <li class="nav-item">
                        <a href="#" class="nav-link" onclick="window.print()">
                            <i class="nav-icon fas fa-print"></i>
                            <p>Stampa</p>
                        </a>
                    </li>
                </ul>
            </nav>
        </div>
    </aside>

    <!-- Content Wrapper -->
    <div class="content-wrapper">
        {% block content %}{% endblock %}
    </div>

    <!-- Footer -->
    <footer class="main-footer">
        <strong>Copyright &copy; 2025 <a href="#">Lodi Mattutine</a>.</strong>
        Tutti i diritti riservati.
        <div class="float-right d-none d-sm-inline-block">
            <b>Version</b> 1.0.0
        </div>
    </footer>
</div>

<!-- jQuery -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
<!-- Bootstrap 4 -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/4.6.1/js/bootstrap.bundle.min.js"></script>
<!-- AdminLTE App -->
<script src="https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/js/adminlte.min.js"></script>

{% block scripts %}{% endblock %}
</body>
</html>''')

    # Template Dashboard
    with open('../templates/index.html', 'w', encoding='utf-8') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Dashboard - Lodi Mattutine{% endblock %}

{% block content %}
<!-- Content Header -->
<div class="content-header">
    <div class="container-fluid">
        <div class="row mb-2">
            <div class="col-sm-6">
                <h1 class="m-0 text-white">Dashboard</h1>
            </div>
        </div>
    </div>
</div>

<!-- Main content -->
<section class="content">
    <div class="container-fluid">
        <!-- Info boxes -->
        <div class="row">
            <div class="col-12 col-sm-6 col-md-4">
                <div class="info-box">
                    <span class="info-box-icon bg-info elevation-1"><i class="fas fa-database"></i></span>
                    <div class="info-box-content">
                        <span class="info-box-text">Lodi Totali</span>
                        <span class="info-box-number">{{ stats.total }}</span>
                    </div>
                </div>
            </div>

            <div class="col-12 col-sm-6 col-md-4">
                <div class="info-box">
                    <span class="info-box-icon bg-success elevation-1"><i class="fas fa-calendar-check"></i></span>
                    <div class="info-box-content">
                        <span class="info-box-text">Prima Data</span>
                        <span class="info-box-number" style="font-size: 1rem;">{{ stats.oldest }}</span>
                    </div>
                </div>
            </div>

            <div class="col-12 col-sm-6 col-md-4">
                <div class="info-box">
                    <span class="info-box-icon bg-warning elevation-1"><i class="fas fa-calendar"></i></span>
                    <div class="info-box-content">
                        <span class="info-box-text">Ultima Data</span>
                        <span class="info-box-number" style="font-size: 1rem;">{{ stats.newest }}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Cards -->
        <div class="row">
            <div class="col-lg-6">
                <div class="card card-primary card-outline liturgy-card">
                    <div class="card-header">
                        <h3 class="card-title"><i class="fas fa-book-open mr-2"></i>Lodi del Giorno</h3>
                    </div>
                    <div class="card-body">
                        <p>Consulta le Lodi Mattutine di oggi o naviga tra le date disponibili.</p>
                        <a href="/lodi" class="btn btn-primary">
                            <i class="fas fa-arrow-right mr-2"></i>Vai alle Lodi
                        </a>
                    </div>
                </div>
            </div>

            <div class="col-lg-6">
                <div class="card card-success card-outline liturgy-card">
                    <div class="card-header">
                        <h3 class="card-title"><i class="fas fa-calendar-alt mr-2"></i>Calendario</h3>
                    </div>
                    <div class="card-body">
                        <p>Visualizza tutte le date disponibili e scegli quale consultare.</p>
                        <a href="/calendario" class="btn btn-success">
                            <i class="fas fa-calendar-alt mr-2"></i>Apri Calendario
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <!-- Info Card -->
        <div class="row">
            <div class="col-12">
                <div class="card card-info card-outline liturgy-card">
                    <div class="card-header">
                        <h3 class="card-title"><i class="fas fa-info-circle mr-2"></i>Informazioni</h3>
                    </div>
                    <div class="card-body">
                        <h5>Liturgia delle Ore</h5>
                        <p>Le Lodi Mattutine sono la preghiera del mattino della Liturgia delle Ore, 
                        il grande tesoro di preghiera della Chiesa Cattolica.</p>

                        <h5 class="mt-3">Struttura delle Lodi</h5>
                        <ul>
                            <li><strong>Introduzione:</strong> Versetto iniziale e Gloria</li>
                            <li><strong>Inno:</strong> Canto poetico del mattino</li>
                            <li><strong>Salmodia:</strong> Tre salmi o cantici con antifone</li>
                            <li><strong>Lettura Breve:</strong> Dalla Sacra Scrittura</li>
                            <li><strong>Responsorio Breve</strong></li>
                            <li><strong>Benedictus:</strong> Cantico di Zaccaria</li>
                            <li><strong>Invocazioni</strong></li>
                            <li><strong>Padre Nostro</strong></li>
                            <li><strong>Orazione</strong></li>
                            <li><strong>Conclusione</strong></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>
{% endblock %}''')

    # Template Lodi
    with open('../templates/lodi.html', 'w', encoding='utf-8') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Lodi Mattutine{% endblock %}

{% block content %}
<div class="content-header">
    <div class="container-fluid">
        <div class="row mb-2">
            <div class="col-sm-12">
                <h1 class="m-0 text-white"><i class="fas fa-cross mr-2"></i>Lodi Mattutine</h1>
            </div>
        </div>
    </div>
</div>

<section class="content">
    <div class="container-fluid">
        <!-- Navigation Controls -->
        <div class="row mb-3">
            <div class="col-12">
                <div class="card liturgy-card">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col-md-3">
                                <button class="btn btn-primary btn-block" id="btn-prev" onclick="navigateDate('prev')">
                                    <i class="fas fa-chevron-left mr-2"></i>Precedente
                                </button>
                            </div>
                            <div class="col-md-6 text-center">
                                <h4 class="mb-0" id="date-display">
                                    <i class="fas fa-calendar-day mr-2"></i>Caricamento...
                                </h4>
                            </div>
                            <div class="col-md-3">
                                <button class="btn btn-primary btn-block" id="btn-next" onclick="navigateDate('next')">
                                    Successivo<i class="fas fa-chevron-right ml-2"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Content -->
        <div id="content">
            <div class="text-center text-white">
                <div class="spinner-border" role="status">
                    <span class="sr-only">Caricamento...</span>
                </div>
                <p class="mt-2">Caricamento delle Lodi...</p>
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block scripts %}
<script>
let currentData = '{{ data }}';

async function loadLodi(data) {
    const content = $('#content');
    content.html('<div class="text-center text-white"><div class="spinner-border"></div><p class="mt-2">Caricamento...</p></div>');

    try {
        const response = await fetch(`/api/lodi/${data}`);
        if (!response.ok) throw new Error('Lodi non trovate');

        const lodi = await response.json();
        currentData = lodi.data;
        $('#date-display').html(`<i class="fas fa-calendar-day mr-2"></i>${lodi.data_formattata}`);

        let html = '';

        // Introduzione
        if (lodi.introduzione.versetto) {
            html += `
            <div class="card liturgy-card">
                <div class="card-header bg-primary">
                    <h3 class="card-title"><i class="fas fa-play-circle mr-2"></i>INTRODUZIONE</h3>
                </div>
                <div class="card-body">
                    <div class="verse-block">
                        <p class="mb-2"><strong>V.</strong> ${lodi.introduzione.versetto}</p>
                        <p class="mb-0"><strong>R.</strong> ${lodi.introduzione.risposta}</p>
                    </div>
                    ${lodi.introduzione.dossologia ? `<pre class="mt-3 text-white">${lodi.introduzione.dossologia}</pre>` : ''}
                </div>
            </div>`;
        }

        // Inno
        if (lodi.inni && lodi.inni.length > 0) {
            html += '<div class="card liturgy-card"><div class="card-header bg-info">';
            html += '<h3 class="card-title"><i class="fas fa-music mr-2"></i>INNO</h3></div><div class="card-body">';
            lodi.inni.forEach((inno, idx) => {
                if (idx > 0) html += '<hr><p class="text-muted"><strong>Oppure:</strong></p>';
                html += `<pre class="salmo-text">${inno.testo}</pre>`;
            });
            html += '</div></div>';
        }

        // Salmodia
        if (lodi.salmodia && lodi.salmodia.length > 0) {
            html += '<div class="card liturgy-card"><div class="card-header bg-success">';
            html += '<h3 class="card-title"><i class="fas fa-book mr-2"></i>SALMODIA</h3></div><div class="card-body">';
            lodi.salmodia.forEach((salmo, idx) => {
                if (idx > 0) html += '<hr class="my-4">';
                html += `
                <div class="antifona"><strong>${salmo.numero}° Antifona:</strong> ${salmo.antifona}</div>
                <h5 class="mt-3 mb-2 text-primary"><i class="fas fa-scroll mr-2"></i>${salmo.titolo}</h5>
                ${salmo.sottotitolo ? `<p class="text-muted"><em>${salmo.sottotitolo}</em></p>` : ''}
                <pre class="salmo-text">${salmo.testo}</pre>
                <div class="antifona mt-3">${salmo.antifona}</div>
                `;
            });
            html += '</div></div>';
        }

        // Lettura Breve
        if (lodi.lettura_breve.testo) {
            html += `
            <div class="card liturgy-card">
                <div class="card-header bg-warning">
                    <h3 class="card-title"><i class="fas fa-bible mr-2"></i>LETTURA BREVE</h3>
                </div>
                <div class="card-body">
                    <h5 class="text-primary">${lodi.lettura_breve.riferimento}</h5>
                    <pre class="salmo-text mt-3">${lodi.lettura_breve.testo}</pre>
                </div>
            </div>`;
        }

        // Responsorio
        if (lodi.responsorio_breve.testo) {
            html += `
            <div class="card liturgy-card">
                <div class="card-header bg-secondary">
                    <h3 class="card-title"><i class="fas fa-comment-dots mr-2"></i>RESPONSORIO BREVE</h3>
                </div>
                <div class="card-body">
                    <pre class="salmo-text">${lodi.responsorio_breve.testo}</pre>
                </div>
            </div>`;
        }

        // Cantico Evangelico
        if (lodi.cantico_evangelico.testo) {
            html += `
            <div class="card liturgy-card">
                <div class="card-header" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                    <h3 class="card-title text-white"><i class="fas fa-star mr-2"></i>CANTICO EVANGELICO</h3>
                </div>
                <div class="card-body">
                    <div class="antifona"><strong>Antifona:</strong> ${lodi.cantico_evangelico.antifona}</div>
                    <h5 class="mt-3 mb-2 text-primary"><i class="fas fa-church mr-2"></i>${lodi.cantico_evangelico.nome}</h5>
                    <pre class="salmo-text">${lodi.cantico_evangelico.testo}</pre>
                    ${lodi.cantico_evangelico.dossologia ? `<pre class="salmo-text mt-3">${lodi.cantico_evangelico.dossologia}</pre>` : ''}
                    <div class="antifona mt-3">${lodi.cantico_evangelico.antifona}</div>
                </div>
            </div>`;
        }

        // Invocazioni
        if (lodi.invocazioni.lista && lodi.invocazioni.lista.length > 0) {
            html += `
            <div class="card liturgy-card">
                <div class="card-header" style="background: #4caf50;">
                    <h3 class="card-title text-white"><i class="fas fa-praying-hands mr-2"></i>INVOCAZIONI</h3>
                </div>
                <div class="card-body">
                    <pre class="salmo-text">${lodi.invocazioni.introduzione}</pre>
                    <div class="alert alert-success mt-3"><strong>${lodi.invocazioni.ritornello}</strong></div>`;
            lodi.invocazioni.lista.forEach(inv => {
                html += `<div class="invocazione-item">${inv}</div>`;
            });
            html += `<div class="alert alert-warning mt-3"><strong>Padre nostro</strong></div>
                </div>
            </div>`;
        }

        // Orazione
        if (lodi.orazione.testo) {
            html += `
            <div class="card liturgy-card">
                <div class="card-header bg-danger">
                    <h3 class="card-title"><i class="fas fa-hands mr-2"></i>ORAZIONE</h3>
                </div>
                <div class="card-body">
                    <p class="lead">${lodi.orazione.testo}</p>
                </div>
            </div>`;
        }

        // Conclusione
        if (lodi.conclusione.benedizione) {
            html += `
            <div class="card liturgy-card">
                <div class="card-header bg-dark">
                    <h3 class="card-title text-white"><i class="fas fa-check-circle mr-2"></i>CONCLUSIONE</h3>
                </div>
                <div class="card-body">
                    <div class="verse-block">
                        <p class="mb-2"><strong>V.</strong> ${lodi.conclusione.benedizione}</p>
                        <p class="mb-0"><strong>R.</strong> ${lodi.conclusione.risposta}</p>
                    </div>
                </div>
            </div>`;
        }

        content.html(html);
        checkNavigationButtons();
        window.scrollTo(0, 0);

    } catch (error) {
        content.html(`
            <div class="alert alert-danger">
                <h4><i class="icon fas fa-ban"></i> Errore!</h4>
                ${error.message}
            </div>
        `);
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
        $('#btn-prev').prop('disabled', !prev.data);
        $('#btn-next').prop('disabled', !next.data);
    } catch (error) {
        console.error('Errore:', error);
    }
}

if (currentData && currentData !== 'None') {
    loadLodi(currentData);
} else {
    $('#content').html(`
        <div class="alert alert-warning">
            <h4><i class="icon fas fa-exclamation-triangle"></i> Attenzione!</h4>
            Nessuna lode disponibile nel database.
        </div>
    `);
}
</script>
{% endblock %}''')

    # Template Calendario
    with open('../templates/calendario.html', 'w', encoding='utf-8') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Calendario - Lodi Mattutine{% endblock %}

{% block content %}
<div class="content-header">
    <div class="container-fluid">
        <div class="row mb-2">
            <div class="col-sm-12">
                <h1 class="m-0 text-white"><i class="fas fa-calendar-alt mr-2"></i>Calendario</h1>
            </div>
        </div>
    </div>
</div>

<section class="content">
    <div class="container-fluid">
        <div class="card liturgy-card">
            <div class="card-header bg-primary">
                <h3 class="card-title"><i class="fas fa-list mr-2"></i>Date Disponibili</h3>
                <div class="card-tools">
                    <span class="badge badge-light">{{ date|length }} date</span>
                </div>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover table-striped">
                        <thead>
                            <tr>
                                <th style="width: 50px">#</th>
                                <th>Data</th>
                                <th style="width: 150px">Azioni</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for data in date %}
                            <tr>
                                <td>{{ loop.index }}</td>
                                <td>
                                    <i class="fas fa-calendar-day text-primary mr-2"></i>
                                    <strong>{{ data['data_formattata'] }}</strong>
                                </td>
                                <td>
                                    <a href="/lodi?data={{ data['data'] }}" class="btn btn-primary btn-sm">
                                        <i class="fas fa-eye mr-1"></i>Visualizza
                                    </a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block scripts %}
<script>
$(document).ready(function() {
    // Evidenzia la voce di menu attiva
    $('.nav-link').removeClass('active');
    $('a[href="/calendario"]').addClass('active');
});
</script>
{% endblock %}''')

    print("\n" + "=" * 70)
    print("✨ APPLICAZIONE WEB LODI MATTUTINE CON ADMINLTE 3 ✨")
    print("=" * 70)
    print("\n🎨 Features AdminLTE:")
    print("  • Dashboard professionale con statistiche")
    print("  • Sidebar responsive con menu di navigazione")
    print("  • Cards con hover effects e gradients")
    print("  • Tabelle responsive per il calendario")
    print("  • Info boxes con icone Font Awesome")
    print("  • Navbar top con fullscreen mode")
    print("  • Layout responsive mobile-first")
    print("  • Funzione di stampa integrata")
    print("\n📱 Componenti:")
    print("  • Dashboard: panoramica con statistiche")
    print("  • Lodi: visualizzazione completa con navigazione")
    print("  • Calendario: tabella con tutte le date")
    print("  • Sidebar: menu laterale collassabile")
    print("\n🎯 Sezioni Colorate:")
    print("  • Introduzione → Blu (Primary)")
    print("  • Inno → Azzurro (Info)")
    print("  • Salmodia → Verde (Success)")
    print("  • Lettura Breve → Giallo (Warning)")
    print("  • Responsorio → Grigio (Secondary)")
    print("  • Benedictus → Gradiente Viola")
    print("  • Invocazioni → Verde (Success)")
    print("  • Orazione → Rosso (Danger)")
    print("  • Conclusione → Nero (Dark)")
    print("\n🚀 Per avviare:")
    print("  1. pip install flask")
    print("  2. python app.py")
    print("  3. Apri: http://localhost:5000")
    print("\n📦 CDN Utilizzati:")
    print("  • AdminLTE 3.2")
    print("  • Bootstrap 4.6")
    print("  • Font Awesome 6.4")
    print("  • jQuery 3.6")
    print("=" * 70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)