# main.py — Valorant Stats (Assignment #1)
# Python 3 + mysql-connector-python

import mysql.connector

# ⚡ Укажи свои данные для подключения
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"          # или твой пользователь
DB_PASS = "asikerka1024!" # замени на свой пароль
DB_NAME = "valorant_stats"

def run_query(cur, sql, limit=10):
    """Выполнить запрос и вывести первые строки"""
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    print("\n>>>", sql.strip().splitlines()[0][:60], "...")
    print("Columns:", cols)
    for i, r in enumerate(rows[:limit], start=1):
        print(f"{i:>2}: {r}")
    print("Всего строк:", len(rows))

def main():
    conn = mysql.connector.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASS,
        database=DB_NAME, charset="utf8mb4"
    )
    cur = conn.cursor()

    # Примеры запросов
    q1 = "SELECT * FROM v_maps LIMIT 10;"
    q2 = """
    SELECT tournament, match_name, map,
           ROUND(duration_sec/60,1) AS duration_min,
           winner_team, score_diff
    FROM v_maps
    WHERE map <> 'All Maps'
    ORDER BY duration_sec DESC
    LIMIT 10;
    """
    q3 = """
    SELECT player,
           SUM(player_kills) AS kills,
           SUM(enemy_kills)  AS deaths,
           ROUND(SUM(player_kills) / NULLIF(SUM(enemy_kills),0), 2) AS kd
    FROM v_kills
    GROUP BY player
    HAVING SUM(player_kills) >= 50
    ORDER BY kd DESC, kills DESC
    LIMIT 15;
    """

    for q in [q1, q2, q3]:
        run_query(cur, q)

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
