"""
Dashboard Liturgia - Flask Application con Layout Atlantis 2.0
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import calendar

app = Flask(__name__)
app.config['SECRET_KEY'] = 'liturgia-dashboard-atlantis-2.0'
app.config['JSON_AS_ASCII'] = False
CORS(app)

# Configurazione percorsi
JSON_DIR = Path('json')
if not JSON_DIR.exists():
    JSON_DIR = Path('static/data/json')
    if not JSON_DIR.exists():
        JSON_DIR.mkdir(parents=True, exist_ok=True)

# Cache per i dati
_data_cache = None


def load_json_data():
    """Carica tutti i file JSON dalla cartella json"""
    global _data_cache

    if _data_cache is not None:
        return _data_cache

    data = {}
    if JSON_DIR.exists():
        for json_file in JSON_DIR.glob("liturgia_*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    date_str = json_file.stem.replace("liturgia_", "")
                    data[date_str] = file_data
            except Exception as e:
                print(f"Errore nel caricamento di {json_file}: {e}")

    _data_cache = data
    return data


def get_statistics(data):
    """Calcola statistiche sui dati liturgici"""
    stats = {
        "total_days": len(data),
        "with_lodi": sum(1 for d in data.values() if d.get("lodi_mattutine")),
        "with_vespri": sum(1 for d in data.values() if d.get("vespri")),
        "with_santo": sum(1 for d in data.values() if d.get("santo_del_giorno")),
        "total_santi": sum(
            d.get("santo_del_giorno", {}).get("numero_santi_celebrati", 0)
            for d in data.values()
        )
    }
    return stats


def format_date(date_str):
    """Formatta la stringa data da YYYYMMDD a formato leggibile"""
    try:
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

        return {
            "full": f"{giorni[date_obj.weekday()]} {date_obj.day} {mesi[date_obj.month - 1]} {date_obj.year}",
            "short": f"{date_obj.day}/{date_obj.month}/{date_obj.year}",
            "day": date_obj.day,
            "month": mesi[date_obj.month - 1],
            "year": date_obj.year,
            "weekday": giorni[date_obj.weekday()]
        }
    except:
        return {
            "full": date_str,
            "short": date_str,
            "day": "",
            "month": "",
            "year": "",
            "weekday": ""
        }


@app.route('/')
def index():
    """Dashboard principale"""
    data = load_json_data()
    stats = get_statistics(data)

    # Ultimi 5 giorni
    recent_days = []
    for date_key in sorted(data.keys(), reverse=True)[:5]:
        day_data = data[date_key]
        recent_days.append({
            'date': format_date(date_key)['full'],
            'date_key': date_key,
            'has_lodi': bool(day_data.get('lodi_mattutine')),
            'has_vespri': bool(day_data.get('vespri')),
            'santo_nome': day_data.get('santo_del_giorno', {}).get('santo_principale', {}).get('nome', 'N/A')
        })

    return render_template('dashboard.html',
                           stats=stats,
                           recent_days=recent_days,
                           active_page='dashboard')


@app.route('/calendario')
def calendario():
    """Vista calendario"""
    data = load_json_data()

    # Ottieni mese e anno dalla query string o usa valori default
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)

    # Crea calendario del mese
    cal = calendar.monthcalendar(year, month)

    # Prepara i dati per il template
    calendar_data = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': 0, 'has_data': False})
            else:
                date_str = f"{year}{month:02d}{day:02d}"
                has_data = date_str in data
                santo_nome = ""
                if has_data:
                    santo_nome = data[date_str].get('santo_del_giorno', {}).get('santo_principale', {}).get('nome', '')
                week_data.append({
                    'day': day,
                    'has_data': has_data,
                    'date_str': date_str,
                    'santo_nome': santo_nome[:20] + '...' if len(santo_nome) > 20 else santo_nome
                })
        calendar_data.append(week_data)

    # Nomi dei mesi
    mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
            "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

    return render_template('calendario.html',
                           calendar_data=calendar_data,
                           month=month,
                           year=year,
                           month_name=mesi[month - 1],
                           active_page='calendario')


@app.route('/giorno/<date_key>')
def giorno_dettaglio(date_key):
    """Dettaglio di un giorno specifico"""
    data = load_json_data()

    if date_key not in data:
        return redirect(url_for('index'))

    day_data = data[date_key]
    formatted_date = format_date(date_key)

    return render_template('giorno_dettaglio.html',
                           day_data=day_data,
                           date_key=date_key,
                           formatted_date=formatted_date,
                           active_page='giorni')


@app.route('/santi')
def santi():
    """Vista elenco santi"""
    data = load_json_data()
    search_query = request.args.get('search', '').lower()

    # Raccogli tutti i santi
    all_saints = []
    for date_key, day_data in data.items():
        if day_data.get("santo_del_giorno"):
            santo = day_data["santo_del_giorno"]
            date_formatted = format_date(date_key)

            if santo.get("santo_principale", {}).get("nome"):
                santo_info = {
                    "data": date_formatted['short'],
                    "data_full": date_formatted['full'],
                    "date_key": date_key,
                    "nome": santo["santo_principale"]["nome"],
                    "martirologio": santo["santo_principale"].get("martirologio", "")[:200]
                }

                # Applica filtro ricerca se presente
                if not search_query or search_query in santo_info["nome"].lower():
                    all_saints.append(santo_info)

            # Altri santi
            for altro_santo in santo.get("altri_santi", []):
                santo_info = {
                    "data": date_formatted['short'],
                    "data_full": date_formatted['full'],
                    "date_key": date_key,
                    "nome": altro_santo.get("nome", ""),
                    "martirologio": altro_santo.get("martirologio", "")[:200]
                }

                if not search_query or search_query in santo_info["nome"].lower():
                    all_saints.append(santo_info)

    return render_template('santi.html',
                           saints=all_saints,
                           search_query=search_query,
                           total_saints=len(all_saints),
                           active_page='santi')


@app.route('/statistiche')
def statistiche():
    """Vista statistiche avanzate"""
    data = load_json_data()

    # Prepara dati per analisi
    stats_by_month = {}
    stats_by_weekday = {
        "Lunedì": {"lodi": 0, "vespri": 0, "santi": 0, "count": 0},
        "Martedì": {"lodi": 0, "vespri": 0, "santi": 0, "count": 0},
        "Mercoledì": {"lodi": 0, "vespri": 0, "santi": 0, "count": 0},
        "Giovedì": {"lodi": 0, "vespri": 0, "santi": 0, "count": 0},
        "Venerdì": {"lodi": 0, "vespri": 0, "santi": 0, "count": 0},
        "Sabato": {"lodi": 0, "vespri": 0, "santi": 0, "count": 0},
        "Domenica": {"lodi": 0, "vespri": 0, "santi": 0, "count": 0}
    }

    for date_key, day_data in data.items():
        # Analisi per mese
        month_key = date_key[:6]  # YYYYMM
        if month_key not in stats_by_month:
            stats_by_month[month_key] = {
                "lodi": 0, "vespri": 0, "santi": 0, "count": 0
            }

        stats_by_month[month_key]["count"] += 1
        if day_data.get("lodi_mattutine"):
            stats_by_month[month_key]["lodi"] += 1
        if day_data.get("vespri"):
            stats_by_month[month_key]["vespri"] += 1
        if day_data.get("santo_del_giorno"):
            stats_by_month[month_key]["santi"] += day_data["santo_del_giorno"].get("numero_santi_celebrati", 0)

        # Analisi per giorno della settimana
        date_obj = datetime.strptime(date_key, "%Y%m%d")
        giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        weekday = giorni[date_obj.weekday()]

        stats_by_weekday[weekday]["count"] += 1
        if day_data.get("lodi_mattutine"):
            stats_by_weekday[weekday]["lodi"] += 1
        if day_data.get("vespri"):
            stats_by_weekday[weekday]["vespri"] += 1
        if day_data.get("santo_del_giorno"):
            stats_by_weekday[weekday]["santi"] += day_data["santo_del_giorno"].get("numero_santi_celebrati", 0)

    # Prepara dati per i grafici
    chart_data = {
        "months": [],
        "lodi_data": [],
        "vespri_data": [],
        "santi_data": []
    }

    for month_key in sorted(stats_by_month.keys()):
        month_stats = stats_by_month[month_key]
        chart_data["months"].append(month_key)
        chart_data["lodi_data"].append(month_stats["lodi"])
        chart_data["vespri_data"].append(month_stats["vespri"])
        chart_data["santi_data"].append(month_stats["santi"])

    general_stats = get_statistics(data)

    return render_template('statistiche.html',
                           general_stats=general_stats,
                           stats_by_weekday=stats_by_weekday,
                           chart_data=chart_data,
                           active_page='statistiche')


@app.route('/api/search-dates')
def search_dates():
    """API per ricerca date"""
    data = load_json_data()
    dates = []

    for date_key in sorted(data.keys(), reverse=True):
        formatted = format_date(date_key)
        dates.append({
            'value': date_key,
            'label': formatted['full']
        })

    return jsonify(dates)


@app.route('/api/stats')
def api_stats():
    """API per statistiche"""
    data = load_json_data()
    stats = get_statistics(data)
    return jsonify(stats)


@app.errorhandler(404)
def page_not_found(e):
    """Gestione errore 404"""
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=59000)