CREATE TABLE public.stg_vacancies (
	id serial NOT NULL,
	obj json NULL,
	update_ts timestamp NULL,
	CONSTRAINT stg_vacancies_pkey PRIMARY KEY (id)
);

CREATE TABLE public.cdm_areas (
	id int NOT NULL,
	parent_id int NULL,
	name varchar(100) NULL,
	CONSTRAINT cdm_areas_pkey PRIMARY KEY (id)
);

----------------------------------------------------------------------
CREATE TABLE profession (
profession_id serial,
name varchar(100) not null,
en_name varchar(100),
words varchar(100) array
,CONSTRAINT pk_profession PRIMARY KEY (profession_id)
);

CREATE TABLE city (
city_id serial,
name varchar(100) not null
,CONSTRAINT pk_city PRIMARY KEY (city_id)
);

CREATE TABLE vacancies (
vacancy_id serial,
city_id serial,
profession varchar(100),
salary_currency varchar(10),
experience varchar(20),
salary_from float(2),
salary_to float(2),
schedule varchar(20),
skills varchar(100) array,
dt date
,CONSTRAINT pk_vacancies PRIMARY KEY (vacancy_id)
,constraint fk_vacancies_city foreign key(city_id) references city(city_id)
);


CREATE TABLE metrics (
city_id serial,
profession_id serial,
dt date,
cnt int,
no_experience_cnt int,
between_1_and_3_cnt int,
between_3_and_6_cnt int,
more_than_6_cnt int,
avg_salary float(2),
no_experience_avg_salary float(2),
between_1_and_3_avg_salary float(2),
between_3_and_6_avg_salary float(2),
more_than_6_avg_salary float(2),
flexible_schedule_cnt int,
remote_schedule_cnt int,
full_day_schedule_cnt int,
shift_schedule_cnt int,
fly_in_fly_out_schedule_cnt int
,CONSTRAINT pk_metrics PRIMARY KEY (city_id, profession_id, dt)
,constraint fk_metrics_city foreign key(city_id) references city(city_id)
,constraint fk_metrics_profession foreign key (profession_id) references profession(profession_id)
);


CREATE TABLE skills (
city_id serial,
profession_id serial,
dt date,
name varchar(100),
cnt int
,constraint pk_skills primary key (city_id, profession_id, name, dt)
,constraint fk_skills_city foreign key(city_id) references city(city_id)
,constraint fk_skills_profession foreign key (profession_id) references profession(profession_id)
);

create or replace procedure insert_vacancies(
		p_vacancy_id int,
		p_city_id int,
		p_profession varchar(100),
		p_salary_currency varchar(10),
		p_salary_from float(2),
		p_salary_to float(2),
		p_experience varchar(20),
		p_schedule varchar(20),
		p_skills varchar(100) array,
		p_dt date
		)
as
$$
declare 
	db_city_id int;
	db_profession varchar(100);
	db_salary_currency varchar(10);
	db_salary_from float(2);
	db_salary_to float(2);
	db_experience varchar(20);
	db_schedule varchar(20);
	db_skills varchar(100) array;
	db_dt date;
begin 
	create table if not exists vacancies (
		vacancy_id serial,
		city_id serial,
		profession varchar(100),
		salary_currency varchar(10),
		experience varchar(20),
		salary_from float(2),
		salary_to float(2),
		schedule varchar(20),
		skills varchar(100) array,
		dt date
		,constraint pk_vacancies primary key (vacancy_id)
		,constraint fk_vacancies_city foreign key(city_id) references city(city_id)
	);	
	if exists(select vacancy_id from vacancies where vacancy_id=p_vacancy_id) then
		select into db_city_id city_id, 
			db_profession profession,
			db_salary_currency salary_currency,
			db_salary_from salary_from,
			db_salary_to salary_to,
			db_experience experience,
			db_schedule schedule,
			db_skills skills,
			db_dt dt
		from vacancies where vacancy_id=p_vacancy_id;
		update vacancies set city_id = p_city_id where vacancy_id=p_vacancy_id and db_city_id != p_city_id;
		update vacancies set profession = p_profession where vacancy_id=p_vacancy_id and db_profession != p_profession;
		update vacancies set salary_currency = p_salary_currency where vacancy_id=p_vacancy_id and (db_salary_currency != p_salary_currency or db_salary_currency is null or p_salary_currency is null);
		update vacancies set salary_from = p_salary_from where vacancy_id=p_vacancy_id and (db_salary_from != p_salary_from or db_salary_from is null or p_salary_from is null);
		update vacancies set salary_to = p_salary_to where vacancy_id=p_vacancy_id and (db_salary_to != p_salary_to or db_salary_to is null or p_salary_to is null);
		update vacancies set experience = p_experience where vacancy_id=p_vacancy_id and (db_experience != p_experience or db_experience is null or p_experience is null);
		update vacancies set schedule = p_schedule where vacancy_id=p_vacancy_id and (db_schedule != p_schedule or db_schedule is null or p_schedule is null);
		update vacancies set skills = p_skills where vacancy_id=p_vacancy_id and (db_skills != p_skills or db_skills is null or p_skills is null);
		update vacancies set dt = p_dt where vacancy_id=p_vacancy_id and (db_dt != p_dt or db_dt is null or p_dt is null);
	else
		insert into vacancies(
			vacancy_id,
			city_id,
			profession,
			salary_currency,
			salary_from,
			salary_to,
			experience,
			schedule,
			skills,
			dt
			)
		values(p_vacancy_id, p_city_id, p_profession, p_salary_currency, p_salary_from, p_salary_to, p_experience, p_schedule, p_skills, p_dt);
	end if;
end;
$$ language plpgsql;

create or replace function get_metric(
  p_city_id int,
  p_profession_id int,
  p_date_from date default (current_date - interval '1 day') :: date,
  p_date_to date default current_date
) 
	returns table (
		db_city_id int,
		db_profession_id int,
		db_dt date,
		db_cnt int,
		db_no_experience_cnt int,
		db_between_1_and_3_cnt int,
		db_between_3_and_6_cnt int,
		db_more_than_6_cnt int,
		db_avg_salary float(2),
		db_no_experience_avg_salary float(2),
		db_between_1_and_3_avg_salary float(2),
		db_between_3_and_6_avg_salary float(2),
		db_more_than_6_avg_salary float(2),
		db_flexible_schedule_cnt int,
		db_remote_schedule_cnt int,
		db_full_day_schedule_cnt int,
		db_shift_schedule_cnt int,
		db_fly_in_fly_out_schedule_cnt int
	) 
	language plpgsql
as $$
begin
	return query
		select
			city_id,
			profession_id,
			dt,
			cnt,
			no_experience_cnt,
			between_1_and_3_cnt,
			between_3_and_6_cnt,
			more_than_6_cnt,
			avg_salary,
			no_experience_avg_salary,
			between_1_and_3_avg_salary,
			between_3_and_6_avg_salary,
			more_than_6_avg_salary,
			flexible_schedule_cnt,
			remote_schedule_cnt,
			full_day_schedule_cnt,
			shift_schedule_cnt,
			fly_in_fly_out_schedule_cnt
		from
			metrics
		where
			city_id = p_city_id
			and profession_id = p_profession_id
			and dt between p_date_from and p_date_to;
end;$$;


create or replace function get_skills(
  p_city_id int,
  p_profession_id int,
  p_date_from date default (current_date - interval '1 day') :: date,
  p_date_to date default current_date
) 
	returns table (
		db_city_id int,
		db_profession_id int,
		db_dt date,
		db_name varchar(100),
		db_cnt int
	) 
	language plpgsql
as $$
begin
	return query
		select
			city_id,
			profession_id,
			dt,
			name,
			cnt
		from
			skills
		where
			city_id = p_city_id
			and profession_id = p_profession_id
			and dt between p_date_from and p_date_to
		order by cnt desc
		limit 30;
end;$$;

insert into profession(name, en_name, words)
values('аналитик', 'analyst','{"аналитик"}');

insert into profession(name, en_name, words)
values('дата инженер', 'data engineer', '{"дата инженер"}');

