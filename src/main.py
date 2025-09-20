#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Valorant analytics (simplified): run PURE SQL queries for global, team, nemesis, per_map, mvp, tournament_stars
"""

import os
import sys
import argparse
import datetime as dt
from typing import Optional, Sequence

import pandas as pd
import mysql.connector as mysql
import getpass

# ---------- Utils ----------

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

# ---------- DB helpers ----------

def get_conn(host: str, port: int, user: str, password: str, db: str):
    return mysql.connect(host=host, port=port, user=user, password=password, database=db)

def run_query(conn, sql: str, params: Optional[Sequence] = None) -> pd.DataFrame:
    return pd.read_sql(sql, conn, params=params or [])

# ---------- CLI ----------

def parse_args(argv: Optional[Sequence[str]] = None):
    p = argparse.ArgumentParser(description="Valorant analytics from MySQL 'kills' table (pure SQL)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=3306)
    p.add_argument("--user", default="root")
    p.add_argument("--password", default="", help="MySQL password")
    p.add_argument("--db", default="valorant_stats")

    # what to run
    p.add_argument(
        "--run",
        default="global,team,nemesis,per_map,mvp,tournament_stars",
        help="Comma-separated: global,team,nemesis,per_map,mvp,tournament_stars (per_map/tournament_stars top-K uses --top-n)"
    )

    # knobs
    p.add_argument("--min-matches", type=int, default=2, help="min matches for global ranking & per_map/tournament_stars")
    p.add_argument("--top-n", type=int, default=20, help="LIMIT for global/nemesis, top-K per map/tournament_stars")

    # output
    p.add_argument("--outdir", default="outputs", help="Root output directory for CSVs")
    return p.parse_args(argv)

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    # open connection
    conn = get_conn(
        host=args.host,
        port=args.port,
        user=args.user,
        password=(args.password or getpass.getpass("MySQL password: ")),
        db=args.db,
    )

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_root = os.path.join(args.outdir, ts)
    ensure_dir(out_root)

    to_run = [x.strip().lower() for x in args.run.split(",") if x.strip()]

    def save_df(df: pd.DataFrame, name: str):
        if df is None or df.empty:
            print(f"\n== {name} ==\n<empty>")
            return
        print(f"\n== {name} ==")
        print(df.head(30).to_string(index=False))
        path = os.path.join(out_root, f"{name}.csv")
        df.to_csv(path, index=False, encoding="utf-8")
        print(f"[saved] {path}")

    # ---------- SQL queries ----------

    min_matches = int(args.min_matches)
    top_n = int(args.top_n)

    # 1) GLOBAL KD
    sql_global = f"""
        WITH agg AS (
          SELECT
            `Player` AS player,
            COUNT(DISTINCT `Match Name`)      AS matches_played,
            SUM(COALESCE(`Player Kills`,0))   AS kills_total,
            SUM(COALESCE(`Enemy Kills`,0))    AS deaths_total
          FROM kills
          GROUP BY `Player`
        )
        SELECT
          player, matches_played, kills_total, deaths_total,
          ROUND(kills_total / NULLIF(deaths_total, 0), 3) AS kd
        FROM agg
        WHERE matches_played >= {min_matches}
        ORDER BY kd DESC, kills_total DESC
        LIMIT {top_n};
    """

    # 2) TEAM KD
    sql_team = """
        SELECT
          `Player Team` AS Team,
          SUM(COALESCE(`Player Kills`,0)) AS team_kills,
          SUM(COALESCE(`Enemy Kills`,0))  AS team_deaths,
          ROUND(SUM(COALESCE(`Player Kills`,0)) / NULLIF(SUM(COALESCE(`Enemy Kills`,0)), 0), 3) AS team_kd
        FROM kills
        WHERE `Player Team` IS NOT NULL AND `Player Team` <> ''
        GROUP BY `Player Team`
        ORDER BY team_kd DESC, team_kills DESC;
    """

    # 3) NEMESIS
    sql_nemesis = f"""
        SELECT
          `Player` AS player,
          `Enemy`  AS enemy,
          SUM(COALESCE(`Enemy Kills`,0))  AS deaths_from_enemy,
          SUM(COALESCE(`Player Kills`,0)) AS kills_on_enemy
        FROM kills
        GROUP BY `Player`, `Enemy`
        ORDER BY deaths_from_enemy DESC
        LIMIT {top_n};
    """

    # 4) PER MAP KD
    sql_per_map = f"""
        WITH per_map AS (
          SELECT
            `Map`                        AS map_name,
            `Player`                     AS player,
            COUNT(DISTINCT `Match Name`) AS matches_played,
            SUM(COALESCE(`Player Kills`,0)) AS kills_total,
            SUM(COALESCE(`Enemy Kills`,0))  AS deaths_total,
            SUM(COALESCE(`Player Kills`,0)) / NULLIF(SUM(COALESCE(`Enemy Kills`,0)), 0) AS kd
          FROM kills
          WHERE `Map` IS NOT NULL AND `Map` <> ''
          GROUP BY `Map`, `Player`
        ),
        ranked AS (
          SELECT
            per_map.*,
            ROW_NUMBER() OVER (PARTITION BY map_name ORDER BY kd DESC, kills_total DESC) AS rk
          FROM per_map
          WHERE matches_played >= {min_matches}
        )
        SELECT map_name, player, matches_played, kills_total, deaths_total, ROUND(kd,3) AS kd
        FROM ranked
        WHERE rk <= {top_n}
        ORDER BY map_name, rk;
    """

    # 5) MATCH MVP
    sql_mvp = """
        WITH per_match AS (
          SELECT
            `Match Name` AS match_name,
            `Player`     AS player,
            MAX(`Player Team`) AS team,
            SUM(COALESCE(`Player Kills`,0)) AS kills_in_match,
            SUM(COALESCE(`Enemy Kills`,0))  AS deaths_in_match,
            SUM(COALESCE(`Player Kills`,0)) / NULLIF(SUM(COALESCE(`Enemy Kills`,0)), 0) AS kd
          FROM kills
          WHERE `Match Name` IS NOT NULL AND `Match Name` <> ''
          GROUP BY `Match Name`, `Player`
        ), ranked AS (
          SELECT
            per_match.*,
            ROW_NUMBER() OVER (
              PARTITION BY match_name
              ORDER BY kills_in_match DESC, deaths_in_match ASC, player ASC
            ) AS rk
          FROM per_match
        )
        SELECT match_name, player, team, kills_in_match, deaths_in_match, ROUND(kd,3) AS kd
        FROM ranked
        WHERE rk = 1
        ORDER BY match_name;
    """

    # 6) TOURNAMENT STARS
    sql_tournament_stars = f"""
        WITH per_t AS (
          SELECT
            `Tournament` AS tournament,
            `Player`     AS player,
            COUNT(DISTINCT `Match Name`)     AS matches_played,
            SUM(COALESCE(`Player Kills`,0))  AS kills_total,
            SUM(COALESCE(`Enemy Kills`,0))   AS deaths_total,
            SUM(COALESCE(`Player Kills`,0)) / NULLIF(SUM(COALESCE(`Enemy Kills`,0)),0) AS kd
          FROM kills
          WHERE `Tournament` IS NOT NULL AND `Tournament` <> ''
          GROUP BY `Tournament`, `Player`
        ), ranked AS (
          SELECT
            per_t.*,
            ROW_NUMBER() OVER (PARTITION BY tournament ORDER BY kd DESC, kills_total DESC) AS rk
          FROM per_t
          WHERE matches_played >= {min_matches}
        )
        SELECT tournament, player, matches_played, kills_total, deaths_total, ROUND(kd,3) AS kd
        FROM ranked
        WHERE rk <= {top_n}
        ORDER BY tournament, rk;
    """

    # ---------- Execute selected ----------
    if "global" in to_run:
        save_df(run_query(conn, sql_global), "global_kd")

    if "team" in to_run:
        save_df(run_query(conn, sql_team), "team_kd")

    if "nemesis" in to_run:
        save_df(run_query(conn, sql_nemesis), "nemesis")

    if "per_map" in to_run:
        save_df(run_query(conn, sql_per_map), "per_map_kd")

    if "mvp" in to_run:
        save_df(run_query(conn, sql_mvp), "match_mvp")

    if "tournament_stars" in to_run:
        save_df(run_query(conn, sql_tournament_stars), "tournament_stars")

    conn.close()
    print(f"\nDone. CSVs saved to: {out_root}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
