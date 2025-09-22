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

