# main.py — Valorant Stats (self-healing views + CSV) + .env
import mysql.connector
import csv, os
from dotenv import load_dotenv

load_dotenv()  # подхватывает .env из корня

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "valorant_stats")

def run_and_save(cur, sql, filename, limit_print=10):
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    print("\n>>>", sql.strip().splitlines()[0][:70], "...")
    print("Columns:", cols)
    for i, r in enumerate(rows[:limit_print], 1):
        print(f"{i:>2}: {r}")
    print("Всего строк:", len(rows))
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cols); w.writerows(rows)
    print(f"CSV: {filename}")

def ensure_views(cur, conn):
    # покажем, куда подключились
    cur.execute("SELECT DATABASE(), @@port, @@hostname, VERSION()")
    db, port, host, ver = cur.fetchone()
    print(f"Connected to DB={db}, host={host}, port={port}, version={ver}")

    # создаём/обновляем вьюхи (идемпотентно)
    cur.execute("""
    CREATE OR REPLACE VIEW v_maps AS
    SELECT
      `Tournament`  AS tournament,
      `Stage`       AS stage,
      `Match Type`  AS match_type,
      `Match Name`  AS match_name,
      `Map`         AS map,
      `Team A`      AS team_a,
      `Team A Score`              AS team_a_score,
      `Team A Attacker Score`     AS team_a_attacker,
      `Team A Defender Score`     AS team_a_defender,
      `Team A Overtime Score`     AS team_a_ot,
      `Team B`      AS team_b,
      `Team B Score`              AS team_b_score,
      `Team B Attacker Score`     AS team_b_attacker,
      `Team B Defender Score`     AS team_b_defender,
      `Team B Overtime Score`     AS team_b_ot,
      `Duration`    AS duration_raw,
      CASE WHEN `Duration` LIKE '%:%:%'
           THEN TIME_TO_SEC(STR_TO_DATE(`Duration`, '%H:%i:%s'))
           ELSE TIME_TO_SEC(STR_TO_DATE(`Duration`, '%i:%s'))
      END AS duration_sec,
      CASE
        WHEN `Team A Score` > `Team B Score` THEN `Team A`
        WHEN `Team B Score` > `Team A Score` THEN `Team B`
        ELSE 'TIE'
      END AS winner_team,
      ABS(`Team A Score` - `Team B Score`) AS score_diff
    FROM maps_scores;
    """)
    cur.execute("""
    CREATE OR REPLACE VIEW v_kills AS
    SELECT
      `Tournament`   AS tournament,
      `Stage`        AS stage,
      `Match Type`   AS match_type,
      `Match Name`   AS match_name,
      `Map`          AS map,
      `Player Team`  AS player_team,
      `Player`       AS player,
      `Enemy Team`   AS enemy_team,
      `Enemy`        AS enemy,
      `Player Kills` AS player_kills,
      `Enemy Kills`  AS enemy_kills,
      `Difference`   AS difference,
      `Kill Type`    AS kill_type
    FROM kills;
    """)
    cur.execute("""
    CREATE OR REPLACE VIEW v_games AS
    SELECT
      `Tournament`   AS tournament,
      `Stage`        AS stage,
      `Match Type`   AS match_type,
      `Match Name`   AS match_name,
      `Map`          AS map,
      `Match ID`     AS match_id,
      `Game ID`      AS game_id
    FROM tournaments_stages_matches_games_ids;
    """)
    conn.commit()

def main():
    conn = mysql.connector.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASS,
        database=DB_NAME, charset="utf8mb4"
    )
    cur = conn.cursor()

    ensure_views(cur, conn)

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
        """, "query3_kd_leaderboard.csv"),
        ("""
        SELECT
          m.tournament, m.match_name, m.map,
          g.game_id, g.match_id,
          m.winner_team, m.score_diff
        FROM v_maps m
        JOIN v_games g
          ON g.tournament = m.tournament
         AND g.stage      = m.stage
         AND g.match_type = m.match_type
         AND g.match_name = m.match_name
         AND g.map        = m.map
        LIMIT 12;
        """, "query4_join_games.csv")
    ]
    for sql, filename in queries:
        run_and_save(cur, sql, filename)

    cur.close(); conn.close()

if __name__ == "__main__":
    main()
