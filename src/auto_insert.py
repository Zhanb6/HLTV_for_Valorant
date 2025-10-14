import os, time, random
from dotenv import load_dotenv
import mysql.connector as mysql

load_dotenv()

CFG = dict(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME", "valorant_stats"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASS", ""),
    autocommit=True,
)

# --- фиксированный список игроков ---
PLAYERS = ["aspas", "f0rsakeN", "Derke", "BuZz"]

def main(interval_sec=5):
    conn = mysql.connect(**CFG)
    cur = conn.cursor()

    # создаём таблицу, если нет
    cur.execute("""
        CREATE TABLE IF NOT EXISTS live_kills (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          player VARCHAR(128) NOT NULL,
          kills INT NOT NULL,
          deaths INT NOT NULL
        );
    """)

    print(f"[auto_insert] writing every {interval_sec}s. Ctrl+C to stop.")
    try:
        while True:
            player = random.choice(PLAYERS)  # ← вот здесь выбор из списка
            kills  = random.randint(5, 30)
            deaths = random.randint(0, 20)
            cur.execute(
                "INSERT INTO live_kills (player, kills, deaths) VALUES (%s,%s,%s);",
                (player, kills, deaths),
            )
            print(f"inserted: {player} k={kills} d={deaths}")
            time.sleep(interval_sec)
    except KeyboardInterrupt:
        print("\n[auto_insert] stopped.")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main(5)  # интервал 5 секунд
