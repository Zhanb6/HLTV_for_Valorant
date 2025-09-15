# main.py — Valorant Stats (Assignment #1)  |  uses .env
import mysql.connector
import csv, os
from dotenv import load_dotenv

# load .env from project root
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "valorant_stats")

def run_and_save(cur, sql, filename, limit_print=10):
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    print("\n>>>", sql.strip().splitlines()[0][:60], "...")
    print("Columns:", cols)
    for i, r in enumerate(rows[:limit_print], start=1):
        print(f"{i:>2}: {r}")
    print("Всего строк:", len(rows))
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cols); w.writerows(rows)
    print(f"Сохранено в {filename}")

def main():
    conn = mysql.connector.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASS,
        database=DB_NAME, charset="utf8mb4"
    )
    cur = conn.cursor()
    queries = [
        ("SELECT * FROM v_maps LIMIT 10;", "query1_maps_sample.csv"),
        ("""
        SELECT tournament, match_name, map,
               ROUND(duration_sec/60,1) AS duration_min,
               winner_team, score_diff
        FROM v_maps
        WHERE map <> 'All Maps'
        ORDER BY duration_sec DESC
        LIMIT 10;
        """, "query2_longest_maps.csv"),
        ("""
        SELECT player,
               SUM(player_kills) AS kills,
               SUM(enemy_kills)  AS deaths,
               ROUND(SUM(player_kills) / NULLIF(SUM(enemy_kills),0), 2) AS kd
        FROM v_kills
        GROUP BY player
        HAVING SUM(player_kills) >= 50
        ORDER BY kd DESC, kills DESC
        LIMIT 15;
        """, "query3_kd_leaderboard.csv")
    ]
    for sql, filename in queries:
        run_and_save(cur, sql, filename)
    cur.close(); conn.close()

if __name__ == "__main__":
    main()
