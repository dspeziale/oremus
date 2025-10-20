#!/usr/bin/env python3
"""
Query utility per database Oremus
Consente di interrogare il database in modo semplice
"""
import sys
from database import OremusDB
from datetime import datetime


class OremusQuery:
    """Utilità per query al database"""

    def __init__(self):
        self.db = OremusDB()

    def get_santo(self, data):
        """Ottiene santo del giorno"""
        try:
            cursor = self.db.conn.cursor()

            cursor.execute('''
                SELECT s.santo_principale, s.numero_santi, d.data_formattata
                FROM santo_giorno s
                JOIN date d ON s.data_id = d.id
                WHERE d.data = ?
            ''', (data,))

            row = cursor.fetchone()
            if row:
                santo_principale, numero_santi, data_fmt = row

                # Ottieni santi commemorati
                cursor.execute('''
                    SELECT testo FROM santo_commemorato
                    WHERE santo_giorno_id = (
                        SELECT id FROM santo_giorno 
                        WHERE data_id = (SELECT id FROM date WHERE data = ?)
                    )
                    ORDER BY ordine
                ''', (data,))

                santi_commemorati = [r[0] for r in cursor.fetchall()]

                return {
                    'data': data,
                    'data_formattata': data_fmt,
                    'santo_principale': santo_principale,
                    'numero_santi': numero_santi,
                    'santi_commemorati': santi_commemorati
                }
        except Exception as e:
            print(f"❌ Errore: {e}")

        return None

    def get_lodi(self, data):
        """Ottiene Lodi Mattutine"""
        try:
            cursor = self.db.conn.cursor()

            cursor.execute('''
                SELECT id, introduzione, inno, responsorio_breve, orazione, conclusione, url
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

            salmodia = [dict(numero=r[0], antifona=r[1], titolo=r[2], testo=r[3][:100])
                        for r in cursor.fetchall()]

            # Lettura breve
            cursor.execute('''
                SELECT riferimento, testo FROM lettura_breve_lodi
                WHERE lodi_mattutine_id = ?
            ''', (lodi_id,))

            lettura_row = cursor.fetchone()
            lettura_breve = dict(
                riferimento=lettura_row[0],
                testo_preview=lettura_row[1][:100]
            ) if lettura_row else None

            return {
                'data': data,
                'introduzione_preview': row[1][:100] if row[1] else "",
                'inno_preview': row[2][:100] if row[2] else "",
                'salmodia': salmodia,
                'lettura_breve': lettura_breve,
                'responsorio_breve_preview': row[3][:100] if row[3] else "",
                'orazione_preview': row[4][:100] if row[4] else "",
                'url': row[6]
            }
        except Exception as e:
            print(f"❌ Errore: {e}")

        return None

    def get_vespri(self, data):
        """Ottiene Vespri"""
        try:
            cursor = self.db.conn.cursor()

            cursor.execute('''
                SELECT id, introduzione, inno, responsorio_breve, orazione, conclusione, url
                FROM vespri
                WHERE data_id = (SELECT id FROM date WHERE data = ?)
            ''', (data,))

            row = cursor.fetchone()
            if not row:
                return None

            vespri_id = row[0]

            # Salmodia
            cursor.execute('''
                SELECT numero, titolo FROM salmodia_vespri
                WHERE vespri_id = ?
                ORDER BY numero
            ''', (vespri_id,))

            salmodia = [dict(numero=r[0], titolo=r[1]) for r in cursor.fetchall()]

            # Magnificat
            cursor.execute('''
                SELECT sottotitolo, testo FROM cantico_vespri
                WHERE vespri_id = ?
            ''', (vespri_id,))

            cant_row = cursor.fetchone()
            magnificat = dict(
                sottotitolo=cant_row[0],
                testo_preview=cant_row[1][:100]
            ) if cant_row else None

            return {
                'data': data,
                'inno_preview': row[2][:100] if row[2] else "",
                'salmodia': salmodia,
                'magnificat': magnificat,
                'responsorio_breve_preview': row[3][:100] if row[3] else "",
                'orazione_preview': row[4][:100] if row[4] else "",
                'url': row[6]
            }
        except Exception as e:
            print(f"❌ Errore: {e}")

        return None

    def get_liturgia(self, data):
        """Ottiene Liturgia del Giorno"""
        try:
            cursor = self.db.conn.cursor()

            cursor.execute('''
                SELECT id, url FROM liturgia_giorno
                WHERE data_id = (SELECT id FROM date WHERE data = ?)
            ''', (data,))

            row = cursor.fetchone()
            if not row:
                return None

            liturgia_id = row[0]

            # Letture
            cursor.execute('''
                SELECT tipo, riferimento, testo FROM lettura_liturgica
                WHERE liturgia_giorno_id = ?
                ORDER BY ordine
            ''', (liturgia_id,))

            letture = []
            for r in cursor.fetchall():
                letture.append(dict(
                    tipo=r[0],
                    riferimento=r[1],
                    testo_preview=r[2][:100] if r[2] else ""
                ))

            return {
                'data': data,
                'letture': letture,
                'url': row[1]
            }
        except Exception as e:
            print(f"❌ Errore: {e}")

        return None

    def get_day_complete(self, data):
        """Ottiene tutto per una data completa"""
        print(f"\n{'=' * 80}")
        print(f"📅 GIORNO COMPLETO: {data}")
        print(f"{'=' * 80}\n")

        # Santo
        santo = self.get_santo(data)
        if santo:
            print(f"🎉 SANTO: {santo['santo_principale']}")
            print(f"   Data: {santo['data_formattata']}")
            print(f"   Commemorazioni: {santo['numero_santi']}\n")

        # Lodi
        lodi = self.get_lodi(data)
        if lodi:
            print(f"☀️  LODI MATTUTINE:")
            print(f"   Salmi: {len(lodi['salmodia'])}")
            for salmo in lodi['salmodia']:
                print(f"     • Salmo {salmo['numero']}: {salmo['titolo']}")
            if lodi['lettura_breve']:
                print(f"   Lettura: {lodi['lettura_breve']['riferimento']}\n")

        # Vespri
        vespri = self.get_vespri(data)
        if vespri:
            print(f"🌙 VESPRI:")
            print(f"   Salmi: {len(vespri['salmodia'])}")
            for salmo in vespri['salmodia']:
                print(f"     • Salmo {salmo['numero']}: {salmo['titolo']}")
            if vespri['magnificat']:
                print(f"   Magnificat: {vespri['magnificat']['sottotitolo']}\n")

        # Liturgia
        liturgia = self.get_liturgia(data)
        if liturgia:
            print(f"📖 LITURGIA DEL GIORNO:")
            print(f"   Letture: {len(liturgia['letture'])}")
            for lettura in liturgia['letture']:
                print(f"     • {lettura['tipo']}")

        print(f"\n{'=' * 80}\n")

    def list_dates(self, limit=10):
        """Lista date nel database"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT data, data_formattata FROM date
                ORDER BY data DESC
                LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()
            if not rows:
                print("❌ Nessuna data nel database")
                return

            print(f"\n📅 Ultime {limit} date nel database:\n")
            for i, (data, data_fmt) in enumerate(rows, 1):
                print(f"  {i}. {data} - {data_fmt}")

            print()
        except Exception as e:
            print(f"❌ Errore: {e}")

    def stats(self):
        """Mostra statistiche database"""
        try:
            cursor = self.db.conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM date')
            total_dates = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM santo_giorno')
            santi_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM lodi_mattutine')
            lodi_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM vespri')
            vespri_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM liturgia_giorno')
            liturgia_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM extraction_log')
            logs_count = cursor.fetchone()[0]

            print(f"\n{'=' * 50}")
            print(f"📊 STATISTICHE DATABASE OREMUS")
            print(f"{'=' * 50}\n")
            print(f"📅 Date totali:       {total_dates}")
            print(f"🎉 Santi:             {santi_count}")
            print(f"☀️  Lodi Mattutine:     {lodi_count}")
            print(f"🌙 Vespri:             {vespri_count}")
            print(f"📖 Liturgie:           {liturgia_count}")
            print(f"📝 Log estrazioni:     {logs_count}")
            print(f"\n{'=' * 50}\n")
        except Exception as e:
            print(f"❌ Errore: {e}")

    def close(self):
        self.db.close()


def main():
    if len(sys.argv) < 2:
        print("📖 OREMUS - Query Database")
        print("────────────────────────────")
        print("\nUso:")
        print("  python query.py YYYYMMDD              # Giorno completo")
        print("  python query.py --santo YYYYMMDD      # Solo santo")
        print("  python query.py --lodi YYYYMMDD       # Solo lodi")
        print("  python query.py --vespri YYYYMMDD     # Solo vespri")
        print("  python query.py --liturgia YYYYMMDD   # Solo liturgia")
        print("  python query.py --list                # Ultime date")
        print("  python query.py --stats               # Statistiche")
        print("\nEsempi:")
        print("  python query.py 20251019")
        print("  python query.py --santo 20251019")
        print("  python query.py --stats")
        return

    query = OremusQuery()

    if sys.argv[1] == '--stats':
        query.stats()
    elif sys.argv[1] == '--list':
        query.list_dates(20)
    elif sys.argv[1] == '--santo' and len(sys.argv) > 2:
        santo = query.get_santo(sys.argv[2])
        if santo:
            print(json.dumps(santo, indent=2, ensure_ascii=False))
    elif sys.argv[1] == '--lodi' and len(sys.argv) > 2:
        lodi = query.get_lodi(sys.argv[2])
        if lodi:
            import json
            print(json.dumps(lodi, indent=2, ensure_ascii=False))
    elif sys.argv[1] == '--vespri' and len(sys.argv) > 2:
        vespri = query.get_vespri(sys.argv[2])
        if vespri:
            import json
            print(json.dumps(vespri, indent=2, ensure_ascii=False))
    elif sys.argv[1] == '--liturgia' and len(sys.argv) > 2:
        liturgia = query.get_liturgia(sys.argv[2])
        if liturgia:
            import json
            print(json.dumps(liturgia, indent=2, ensure_ascii=False))
    else:
        # Data singola - mostra tutto
        query.get_day_complete(sys.argv[1])

    query.close()


if __name__ == "__main__":
    main()