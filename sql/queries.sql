-- queries.sql — Valorant Analytics (Assignment #1)
-- DB: valorant_stats

/* ---------------------------------------------------------
   0) Views to normalize column names (clean aliases)
--------------------------------------------------------- */
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
  CASE
    WHEN `Duration` LIKE '%:%:%'
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

CREATE OR REPLACE VIEW v_games AS
SELECT
  tournament, tournament_id,
  stage, stage_id,
  match_type, match_name,
  map, match_id, game_id
FROM tournaments_stages_matches_games_ids;

/* ---------------------------------------------------------
   1) Basic SELECT + LIMIT
--------------------------------------------------------- */
SELECT * FROM v_maps LIMIT 10;

/* ---------------------------------------------------------
   2) WHERE + ORDER BY: top-10 longest maps
--------------------------------------------------------- */
SELECT tournament, match_name, map,
       ROUND(duration_sec/60, 1) AS duration_min,
       winner_team, score_diff
FROM v_maps
WHERE map <> 'All Maps'
ORDER BY duration_sec DESC
LIMIT 10;

/* ---------------------------------------------------------
   3) GROUP BY: total maps played by each team
--------------------------------------------------------- */
SELECT team, SUM(cnt) AS maps_total
FROM (
  SELECT team_a AS team, COUNT(*) AS cnt FROM v_maps GROUP BY team_a
  UNION ALL
  SELECT team_b AS team, COUNT(*) AS cnt FROM v_maps GROUP BY team_b
) t
GROUP BY team
ORDER BY maps_total DESC
LIMIT 15;

/* ---------------------------------------------------------
   4) JOIN: link maps to game_id
--------------------------------------------------------- */
SELECT
  m.tournament, m.stage, m.match_type, m.match_name, m.map,
  g.match_id, g.game_id, m.winner_team, m.score_diff
FROM v_maps m
JOIN v_games g
  ON g.tournament = m.tournament
 AND g.stage      = m.stage
 AND g.match_type = m.match_type
 AND g.match_name = m.match_name
 AND g.map        = m.map
LIMIT 12;

/* ---------------------------------------------------------
   5) JOIN: attach team IDs
--------------------------------------------------------- */
SELECT m.map, m.match_name,
       tA.team_id AS team_a_id,
       tB.team_id AS team_b_id
FROM v_maps m
LEFT JOIN teams_ids tA ON tA.team = m.team_a
LEFT JOIN teams_ids tB ON tB.team = m.team_b
LIMIT 12;

/* ---------------------------------------------------------
   6) Aggregation on kills: top-15 by kill difference
--------------------------------------------------------- */
SELECT player, SUM(difference) AS total_diff
FROM v_kills
GROUP BY player
ORDER BY total_diff DESC
LIMIT 15;

/* ---------------------------------------------------------
   7) K/D leaderboard (kills / deaths)
--------------------------------------------------------- */
SELECT player,
       SUM(player_kills) AS kills,
       SUM(enemy_kills)  AS deaths,
       ROUND(SUM(player_kills) / NULLIF(SUM(enemy_kills),0), 2) AS kd
FROM v_kills
GROUP BY player
HAVING SUM(player_kills) >= 50
ORDER BY kd DESC, kills DESC
LIMIT 15;

/* ---------------------------------------------------------
   8) Who dominates against whom (player vs enemy)
--------------------------------------------------------- */
SELECT player, enemy,
       SUM(difference) AS diff_vs_enemy
FROM v_kills
GROUP BY player, enemy
HAVING SUM(difference) >= 10
ORDER BY diff_vs_enemy DESC
LIMIT 15;

/* ---------------------------------------------------------
   9) Stage breakdown: number of maps per stage
--------------------------------------------------------- */
SELECT tournament, stage, COUNT(*) AS maps_cnt
FROM v_maps
GROUP BY tournament, stage
ORDER BY tournament,
         FIELD(stage, 'Swiss Stage','Play-In','Quarterfinals','Semifinals','Final','Grand Final'),
         stage;

/* ---------------------------------------------------------
   10) Map winrates for teams
--------------------------------------------------------- */
WITH all_maps AS (
  SELECT map, team_a AS team,
         CASE WHEN team_a_score > team_b_score THEN 1 ELSE 0 END AS win
  FROM v_maps
  UNION ALL
  SELECT map, team_b AS team,
         CASE WHEN team_b_score > team_a_score THEN 1 ELSE 0 END AS win
  FROM v_maps
)
SELECT map, team,
       COUNT(*) AS games,
       ROUND(AVG(win)*100, 1) AS winrate_pct
FROM all_maps
WHERE map <> 'All Maps'
GROUP BY map, team
HAVING COUNT(*) >= 3
ORDER BY winrate_pct DESC, games DESC
LIMIT 30;
