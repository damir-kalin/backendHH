#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL

  CREATE TABLE city (
city_id int,
name varchar(150)
,CONSTRAINT pk_city PRIMARY KEY (city_id)
);
CREATE TABLE count_vacancies (
city_id int,
cnt int,
dt date
,CONSTRAINT pk_count_vacancies PRIMARY KEY (city_id, dt)
);
CREATE TABLE avg_salary (
city_id int,
experience varchar(100),
avg_salary float,
dt date
,CONSTRAINT pk_avg_salary PRIMARY KEY (city_id, experience, dt)
);
CREATE TABLE skills (
city_id int,
skill varchar(150),
cnt int,
dt date
,CONSTRAINT pk_skills PRIMARY KEY (city_id, skill, dt)
);
CREATE TABLE type_vacancies (
city_id int,
type_vacancies varchar(100),
cnt int,
dt date
,CONSTRAINT pk_type_vacancies PRIMARY KEY (city_id, type_vacancies, dt)
);
CREATE TABLE shedule (
city_id int,
shedule varchar(100),
cnt int,
dt date
,CONSTRAINT pk_shedule PRIMARY KEY (city_id, shedule, dt)
);
  
EOSQL