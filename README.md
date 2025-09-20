# Vantage Esports Analytics (Valorant)

Аналитика матчей Valorant (VCT 2025): импорт данных в MySQL, ER-диаграмма, SQL-запросы и mini-скрипт на Python.

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
