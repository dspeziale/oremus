#!/usr/bin/env python3
"""
Script di debug per capire la struttura di vespri con antifone_salmi
"""
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DB_PATH = 'instance/oremus.db'


def debug_vespri_antifone_salmi():
    """Debug della struttura vespri + antifone_salmi"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print("\n" + "=" * 80)
        print("🔍 DEBUG: VESPRI + ANTIFONE_SALMI")
        print("=" * 80 + "\n")

        # 1. Statistiche per vespri_id
        print("📈 Statistiche per vespri_id:\n")
        cursor.execute('''
            SELECT vespri_id, COUNT(*) as conteggio, GROUP_CONCAT(tipo) as tipi
            FROM antifone_salmi
            WHERE vespri_id IS NOT NULL
            GROUP BY vespri_id
            LIMIT 5
        ''')

        stats = cursor.fetchall()
        if not stats:
            print("   ❌ Nessun vespri_id trovato!")
        else:
            for stat in stats:
                stat_dict = dict(stat)
                print(
                    f"   vespri_id: {stat_dict['vespri_id']} | Conteggio: {stat_dict['conteggio']} | Tipi: {stat_dict['tipi']}")

        print("\n" + "-" * 80 + "\n")

        # 2. Prova con un vespri_id specifico
        print("🧪 Test con un vespri_id specifico:\n")
        cursor.execute("SELECT MIN(vespri_id) FROM antifone_salmi WHERE vespri_id IS NOT NULL")
        result = cursor.fetchone()

        if result and result[0]:
            test_vespri_id = result[0]
            print(f"Usando vespri_id: {test_vespri_id}\n")

            # Recupera i vespri
            cursor.execute('SELECT * FROM vespri WHERE id = ?', (test_vespri_id,))
            vespri_row = cursor.fetchone()
            if vespri_row:
                vespri_dict = dict(vespri_row)
                print(f"Vespri trovati:")
                for key, value in vespri_dict.items():
                    val_str = str(value)[:60] if value else "NULL"
                    print(f"   {key}: {val_str}")
                print()

            # Recupera antifone_salmi per questo vespri
            cursor.execute('''
                SELECT * FROM antifone_salmi 
                WHERE vespri_id = ?
                ORDER BY antifona_numero
            ''', (test_vespri_id,))

            test_rows = cursor.fetchall()
            print(f"Trovati {len(test_rows)} record per vespri_id {test_vespri_id}:\n")

            for idx, row in enumerate(test_rows, 1):
                row_dict = dict(row)
                print(f"Record {idx}:")
                for key, value in row_dict.items():
                    val_str = str(value)[:50] if value else "NULL"
                    print(f"   {key}: {val_str}")
                print()
        else:
            print("   ❌ Nessun vespri_id trovato nella tabella antifone_salmi")

        conn.close()

        print("=" * 80)
        print("✅ Debug completato!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"❌ Errore durante debug: {e}")
        import traceback
        traceback.print_exc()


# ESEGUI DIRETTAMENTE
if __name__ == '__main__':
    print("\n🚀 SCRIPT DEBUG VESPRI + ANTIFONE_SALMI\n")
    debug_vespri_antifone_salmi()