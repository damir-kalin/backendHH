create table if not exists stg_vacancies (
	id serial not null,
	obj json not null,
	query_profession_name varchar(100) not null,
	query_dt date not null,
	update_ts timestamp not null,
	constraint stg_vacancies_pkey primary key (id)
);

create table if not exists d_city (
	id int not null,
	name varchar(100) not null,
	constraint cdm_areas_pkey primary key (id)
);

create table if not exists d_query_profession(
	id serial not null,
	name varchar(100) not null,
	constraint d_query_profession_pkey primary key (id)
);
insert into d_query_profession(name) values('Data engineer');
insert into d_query_profession(name) values('Data analyst');

create table if not exists stg_exchange_rates(
	id serial not null,
	obj json not null,
	query_dt date not null,
	update_ts timestamp NULL,
	constraint stg_exchange_rates_pkey primary key (id)
);

create table if not exists d_vacancies (
	id serial not null,
	vacancy_id bigint not null,
	city_id bigint not null,
	query_profession_id bigint not null,
	profession varchar(100) ,
	salary_currency varchar(10),
	salary_from float(2),
	salary_to float(2),
	experience varchar(20),
	schedule varchar(20),
	published_at timestamp,
	dt date,
constraint pk_d_vacancies primary key (id),
constraint fk_d_vacancies_city foreign key (city_id) references d_city(id),
constraint fk_d_vacancies_query_profession foreign key (query_profession_id) references d_query_profession(id),
constraint uq_d_vacancies_vacancy_id_dt unique (vacancy_id, dt, query_profession_id)
);

create table if not exists d_skill(
	id serial,
	name varchar(150)
	,constraint pk_skill primary key (id)
);

create table if not exists fct_skill_vacancy(
	id serial,
	skill_id bigint,
	vacancy_id bigint,
	constraint pk_fct_skill_vacancy primary key (id),
	constraint fk_fct_skill_vacancy_d_skill foreign key (skill_id) references d_skill(id),
	constraint fk_fct_skill_vacancy_d_vacancies foreign key (vacancy_id) references d_vacancies(id)
);

create table if not exists d_exchange_rates(
	id serial not null,
	exchange_rates_id varchar(20) not null,
	num_code varchar(5) not null,
	char_code varchar(5) not null,
	name varchar(70) not null,
	constraint d_exchange_rates_pkey primary key (id),
	constraint uq_d_exchange_rates_char_code unique (char_code)
);

create table if not exists fct_exchange_rates(
	id serial not null,
	id_exchange_rates bigint not null,
	value numeric(10, 4) not null,
	previous numeric(10, 4) not null,
	nominal int not null,
	published_at timestamp not null,
	dt date,
	constraint fct_exchange_rates_pkey primary key (id)
);

create table if not exists dm_metrics(
	id serial not null,
	city_name varchar(100) not null,
	query_profession_name varchar(100) not null,
	dt date not null,
	cnt int not null,
	no_experience_cnt int not null,
	between_1_and_3_cnt int not null,
	between_3_and_6_cnt int not null,
	more_than_6_cnt int not null,
	no_experience_avg_salary numeric(10, 2) not null,
	between_1_and_3_avg_salary numeric(10, 2) not null,
	between_3_and_6_avg_salary numeric(10, 2) not null,
	more_than_6_avg_salary numeric(10, 2) not null,
	flexible_schedule_cnt int not null,
	remote_schedule_cnt int not null,
	full_day_schedule_cnt int not null,
	shift_schedule_cnt int not null,
	fly_in_fly_out_schedule_cnt int not null,
constraint dm_metrics_pkey primary key (id),
constraint dm_metrics_city_id_query_profession_id_dt unique(city_name, query_profession_name, dt)
);

create table if not exists dm_skills(
	id serial not null,
	city_name varchar(100) not null,
	query_profession_name varchar(100) not null,
	skill_name varchar(150) not null,
	dt date not null,
	top int not null,
	cnt int not null,
constraint dm_skills_pkey primary key (id),
constraint dm_skills_uq unique(city_name, query_profession_name, skill_name, dt)
);

copy d_city from '/app/city.csv' with delimiter '|' csv header;