# Vantage Esports Analytics (Valorant)

Аналитика матчей Valorant (VCT 2025): импорт данных в MySQL, ER-диаграмма, SQL-запросы и mini-скрипт на Python.
ER-diagram -> <img width="1280" height="803" alt="image" src="https://github.com/user-attachments/assets/7cb6a174-eba9-4a68-bf7a-039ceaf5bdb9" />



## Стек
- MySQL 8.0, MySQL Workbench
- Python 3.11, mysql-connector-python

## Датасет
VCT 2025 (матчи, карты, киллы, эко-раунды). Файлы импортированы из локальной папки (не публикую из-за размера). Структура таблиц — в ER-диаграмме.

## Как развернуть
1. Создать БД:
   ```sql
   CREATE DATABASE valorant_stats DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
   USE valorant_stats;
   ```
 ## How to connect to database
 ```sql
\sql
\connect root@localhost:3306
show databases;
use valorant_stats;
```


## 10 Analytical queries
1.Быстрый топ по K/D без порога
```sql
WITH agg AS (
  SELECT
    `Player` AS player,
    COUNT(DISTINCT `Match Name`) AS matches_played,
    SUM(COALESCE(`Player Kills`,0)) AS kills_total,
    SUM(COALESCE(`Enemy Kills`,0))  AS deaths_total
  FROM kills
  GROUP BY `Player`
)
SELECT
  player, matches_played, kills_total, deaths_total,
  ROUND(kills_total / NULLIF(deaths_total, 0), 3) AS kd
FROM agg
ORDER BY kd DESC, kills_total DESC
LIMIT 20;
```
2.
```sql

```

3.
```sql

```
4.
```sql

```
5.
```sql

```
6.
```sql

```
7.
```sql

```
8.
```sql

```
9.
```sql

```
10.
```sql

```
