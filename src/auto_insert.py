import time, random, mysql.connector
from datetime import datetime

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    port="3306",
    password="asikerka1024!",
    database="valorant_stats",
    autocommit=True
)
cur = conn.cursor()

players = ["Jett", "Raze", "Phoenix", "Sova", "Reyna"]
maps = ["Ascent", "Bind", "Haven", "Split", "Icebox"]
weapons = ["Vandal", "Phantom", "Operator", "Spectre", "Sheriff"]

match_id = random.randint(1000, 9999)
round_no = 1

while True:
    player = random.choice(players)
    map_name = random.choice(maps)
    weapon = random.choice(weapons)

    base = 1 if player in ["Jett", "Reyna"] else 0
    kills = base + random.randint(0, 3)
    deaths = max(0, random.randint(0, 3 - base))

    cur.execute("""
        INSERT INTO live_kills (player, kills, deaths, map_name, weapon, ts)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (player, kills, deaths, map_name, weapon, datetime.now()))

    print(f"[{datetime.now():%H:%M:%S}] {player} ({weapon}) on {map_name}: {kills}K/{deaths}D")

    time.sleep(8)
