#!/usr/bin/env python3
"""
Orchestratore Oremus - Esegue tutti gli script e salva su DB
Uso: python orchestrate.py YYYYMMDD [YYYYMMDD_END]
"""
import sys
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

from database import OremusDB


class OremusOrchestrator:
    """Orchestra estrazione liturgica e salvataggio su DB"""

    SCRIPTS = {
        'santo': 'santo.py',
        'liturgia': 'liturgia.py',
        'lodi': 'lodi.py',
        'vespri': 'vespri.py'
    }

    JSON_PATHS = {
        'santo': 'json/santo_{}.json',
        'liturgia': 'json/liturgia_{}.json',
        'lodi': 'json/lodi_mattutine_{}.json',
        'vespri': 'json/vespri_{}.json'
    }

    def __init__(self):
        """Inizializza orchestratore"""
        self.db = OremusDB()
        os.makedirs('json', exist_ok=True)

    def parse_date_range(self, arg1, arg2=None):
        """Parsa single date o range"""
        try:
            start = datetime.strptime(arg1, "%Y%m%d")
            if arg2:
                end = datetime.strptime(arg2, "%Y%m%d")
            else:
                end = start

            # Genera lista date
            dates = []
            current = start
            while current <= end:
                dates.append(current.strftime("%Y%m%d"))
                current += timedelta(days=1)

            return dates
        except ValueError as e:
            print(f"❌ Formato data non valido: {e}")
            return []

    def run_script(self, script_name, data):
        """Esegue script Python"""
        try:
            result = subprocess.run(
                [sys.executable, script_name, data],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=60
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Timeout"
        except Exception as e:
            return False, "", str(e)

    def load_json(self, json_path):
        """Carica file JSON"""
        try:
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"❌ Errore caricamento {json_path}: {e}")
        return None

    def process_date(self, data):
        """Processa una singola data"""
        print(f"\n{'=' * 80}")
        print(f"📅 ELABORAZIONE DATA: {data}")
        print(f"{'=' * 80}")

        results = {}

        # Esegui ogni script
        for script_type, script_name in self.SCRIPTS.items():
            print(f"\n⏳ Esecuzione {script_type.upper()}...")

            success, stdout, stderr = self.run_script(script_name, data)

            if success:
                print(f"✅ {script_type.upper()} completato")

                # Carica JSON e salva su DB
                json_path = self.JSON_PATHS[script_type].format(data)
                json_data = self.load_json(json_path)

                if json_data:
                    # Salva su database in base al tipo
                    if script_type == 'santo':
                        self.db.save_santo_giorno(json_data)
                        print(f"   ✓ Santo salvato su DB")
                    elif script_type == 'liturgia':
                        self.db.save_liturgia_giorno(json_data)
                        print(f"   ✓ Liturgia salvata su DB")
                    elif script_type == 'lodi':
                        self.db.save_lodi_mattutine(json_data)
                        print(f"   ✓ Lodi salvate su DB")
                    elif script_type == 'vespri':
                        self.db.save_vespri(json_data)
                        print(f"   ✓ Vespri salvati su DB")

                    # Log successo
                    self.db.log_extraction(data, script_name, 'SUCCESS',
                                           f"File salvato: {json_path}")
                    results[script_type] = 'OK'
                else:
                    print(f"   ⚠️  JSON non trovato: {json_path}")
                    results[script_type] = 'JSON_NOT_FOUND'
            else:
                print(f"❌ {script_type.upper()} FALLITO")
                if stderr:
                    print(f"   Errore: {stderr[:200]}")

                # Log errore
                self.db.log_extraction(data, script_name, 'FAILED', stderr[:500])
                results[script_type] = 'FAILED'

        return results

    def print_summary(self, data_list, all_results):
        """Stampa riepilogo finale"""
        print(f"\n\n{'=' * 80}")
        print(f"📊 RIEPILOGO ELABORAZIONE")
        print(f"{'=' * 80}\n")

        total_dates = len(data_list)
        total_scripts = len(self.SCRIPTS)

        # Conta successi
        success_count = 0
        for date_results in all_results.values():
            for script_type, status in date_results.items():
                if status == 'OK':
                    success_count += 1

        total_operations = total_dates * total_scripts

        print(f"📅 Date elaborate: {total_dates}")
        print(f"📜 Script totali: {len(self.SCRIPTS)}")
        print(f"✅ Operazioni riuscite: {success_count}/{total_operations}")
        print(f"📊 Percentuale successo: {(success_count / total_operations * 100):.1f}%")

        # Dettagli per data
        print(f"\n{'─' * 80}")
        print("DETTAGLI PER DATA:\n")

        for data in data_list:
            date_results = all_results.get(data, {})
            statuses = list(date_results.values())

            # Determina icona
            if all(s == 'OK' for s in statuses):
                icon = "✅"
            elif any(s == 'FAILED' for s in statuses):
                icon = "❌"
            else:
                icon = "⚠️"

            status_str = " | ".join([f"{k}: {v}" for k, v in date_results.items()])
            print(f"{icon} {data}: {status_str}")

        print(f"\n📂 Database: {OremusDB.DB_PATH}")
        print(f"📂 JSON: json/")
        print(f"{'=' * 80}\n")

    def run(self, args):
        """Esegue orchestrazione"""
        args.append("20251020")
        args.append("20251104")
        if len(args) < 1:
            print("📖 OREMUS - Orchestratore Liturgico")
            print("────────────────────────────────────")
            print("\nUso:")
            print("  python orchestrate.py YYYYMMDD              # Data singola")
            print("  python orchestrate.py YYYYMMDD YYYYMMDD     # Range date")
            print("\nEsempi:")
            print("  python orchestrate.py 20251019")
            print("  python orchestrate.py 20251019 20251025")
            return

        # Parsa date
        if len(args) == 1:
            data_list = self.parse_date_range(args[0])
        else:
            data_list = self.parse_date_range(args[0], args[1])

        if not data_list:
            print("❌ Nessuna data da elaborare")
            return

        print(f"\n🚀 INIZIO ELABORAZIONE OREMUS")
        print(f"📅 Date: {len(data_list)} date")
        print(f"📜 Script: {len(self.SCRIPTS)} script")

        # Processa ogni data
        all_results = {}
        for data in data_list:
            results = self.process_date(data)
            all_results[data] = results

        # Stampa riepilogo
        self.print_summary(data_list, all_results)

        # Chiudi DB
        self.db.close()
        print("✅ Elaborazione completata!\n")


def main():
    orchestrator = OremusOrchestrator()
    orchestrator.run(sys.argv[1:])


if __name__ == "__main__":
    main()