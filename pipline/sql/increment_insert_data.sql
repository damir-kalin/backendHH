insert into d_vacancies(vacancy_id, city_id, query_profession_id, profession, salary_currency, salary_from, salary_to, experience, schedule, published_at, dt)
select 
	distinct
	(sv.obj ->> 'id')::bigint as vacancy_id,
	(sv.obj -> 'area' ->> 'id')::int as city_id,
	dq.id as query_profession_id,
	(sv.obj ->> 'name')::varchar(100) as profession,
	(sv.obj -> 'salary' ->> 'currency')::varchar(10) as salary_currency,
	(sv.obj -> 'salary' ->> 'from')::float as salary_from,
	(sv.obj -> 'salary' ->> 'to')::float as salary_to,
	(sv.obj -> 'experience' ->> 'id')::varchar(20) as experience,
	(sv.obj -> 'schedule'->> 'id')::varchar(10) as schedule,
	(sv.obj ->> 'published_at')::timestamp as published_at,
	sv.query_dt::date as dt
from stg_vacancies as sv
	inner join d_query_profession as dq on sv.query_profession_name = dq.name
where sv.query_dt = (current_date - '1 day'::interval)::date
on conflict (vacancy_id, dt, query_profession_id) do update 
set 
	city_id = EXCLUDED.city_id,
	profession = EXCLUDED.profession,
	salary_currency = EXCLUDED.salary_currency,
	salary_from = EXCLUDED.salary_from,
	salary_to = EXCLUDED.salary_to,
	experience = EXCLUDED.experience,
	schedule = EXCLUDED.schedule,
	published_at =  EXCLUDED.published_at;

insert into d_skill(name)
select  l.name
from 
	(select 
		distinct
		name
	from stg_vacancies sv
		cross join lateral json_to_recordset(sv.obj -> 'key_skills') 
	as p(name varchar)) as l left join d_skill as d on d.name=l.name
where d.name is null;

insert into fct_skill_vacancy(skill_id, vacancy_id)
select
	ds.id as skill_id,
	dv.id as vacancy_id
from 
	(select 
		sv.id,
		sv.obj,
		sv.update_ts,
		p.name
	from stg_vacancies sv
		cross join lateral json_to_recordset(sv.obj -> 'key_skills') 
	as p(name varchar)
	where sv.query_dt = (current_date - '1 day'::interval)::date
	) as l 
	inner join d_skill as ds on ds.name=l.name
	inner join d_vacancies as dv on (l.obj->>'id')::bigint = dv.vacancy_id;


insert into d_exchange_rates(exchange_rates_id, num_code, char_code, nominal, name)
select distinct
	(js.value ->>'ID')::varchar(20) as exchange_rates_id,
	(js.value ->>'NumCode')::varchar(5) as num_code,
	(js.value ->>'CharCode')::varchar(5) as char_code,
	(js.value ->>'Nominal')::int as nominal,
	(js.value ->>'Name')::varchar(70) as name
from (select id, obj, (obj->>'Valute')::json as valute, update_ts from stg_exchange_rates) as se, 
	json_each(se.valute) as js
on conflict (char_code) do update 
set 
	exchange_rates_id = EXCLUDED.exchange_rates_id,
	num_code = EXCLUDED.num_code,
	nominal = EXCLUDED.nominal,
	name = EXCLUDED.name;

--Вставляем данные
insert into fct_exchange_rates (id_exchange_rates, value, previous, published_at, dt)
select 
	de.id,
	t.value,
	t.previous,
	t.published_at,
	t.dt
from
(select 
	(js.value ->>'CharCode')::varchar(5) as char_code,
	(js.value ->>'Value')::numeric(10,4) as value,
	(js.value ->>'Previous')::numeric(10,4) as previous,
	(se.obj->>'Date')::timestamp as published_at,
	se.query_dt::date as dt
from (select id, obj, (obj->>'Valute')::json as valute, query_dt, update_ts from stg_exchange_rates where query_dt = (current_date - '1 day'::interval)::date) as se, 
	json_each(se.valute) as js) as t
inner join d_exchange_rates de on t.char_code = de.char_code
;

--Вставляем данные
with tmp_vacancies as(
select distinct
	dv.id,
	dc.name as city_name,
	dq.name as query_profession_name,
	dv.dt,
	(((case when dv.salary_currency='RUR' then coalesce(dv.salary_from, dv.salary_to) 
		when dv.salary_currency!='RUR' then coalesce(dv.salary_from * fe.value, dv.salary_to * fe.value) end)::numeric(10,2) +
	(case when dv.salary_currency='RUR' then coalesce(dv.salary_to, dv.salary_from)
		when dv.salary_currency!='RUR' then coalesce(dv.salary_to * fe.value, dv.salary_from * fe.value) end)::numeric(10,2))/2)::numeric(10,2) avg_salary,
	dv.experience,
	dv.schedule
from d_vacancies dv 
	left join d_exchange_rates as de on dv.salary_currency = de.char_code 
	left join fct_exchange_rates as fe on de.id = fe.id_exchange_rates and dv.dt = fe.dt
	left join d_city as dc on dv.city_id = dc.id
	left join d_query_profession as dq on dv.query_profession_id = dq.id
where dv.dt = (current_date - '1 day'::interval)::date
)
insert into dm_metrics (city_name, 
	query_profession_name, 
	dt, 
	cnt, 
	no_experience_cnt, 
	between_1_and_3_cnt, 
	between_3_and_6_cnt, 
	more_than_6_cnt, 
	no_experience_avg_salary,
	between_1_and_3_avg_salary,
	between_3_and_6_avg_salary,
	more_than_6_avg_salary,
	flexible_schedule_cnt,
	remote_schedule_cnt,
	full_day_schedule_cnt,
	shift_schedule_cnt,
	fly_in_fly_out_schedule_cnt
	)
select distinct
	city_name, 
	query_profession_name,
	dt,
	count(id) over(partition by city_name, query_profession_name, dt) as cnt,
	count(id) filter(where experience='noExperience') over(partition by city_name, query_profession_name, dt) as no_experience_cnt,
	count(id) filter(where experience='between1And3') over(partition by city_name, query_profession_name, dt) as between_1_and_3_cnt,
	count(id) filter(where experience='between3And6') over(partition by city_name, query_profession_name, dt) as between_3_and_6_cnt,
	count(id) filter(where experience='moreThan6') over(partition by city_name, query_profession_name, dt) as more_than_6_cnt,
	coalesce(avg(avg_salary) filter(where experience='noExperience') over(partition by city_name, query_profession_name, dt)::numeric(10, 2),0) as no_experience_avg_salary,
	coalesce(avg(avg_salary) filter(where experience='between1And3') over(partition by city_name, query_profession_name, dt)::numeric(10, 2),0) as between_1_and_3_avg_salary,
	coalesce(avg(avg_salary) filter(where experience='between3And6') over(partition by city_name, query_profession_name, dt)::numeric(10, 2),0) as between_3_and_6_avg_salary,
	coalesce(avg(avg_salary) filter(where experience='moreThan6') over(partition by city_name, query_profession_name, dt)::numeric(10, 2),0) as more_than_6_avg_salary,
	count(id) filter(where schedule='flexible') over(partition by city_name, query_profession_name, dt) as flexible_schedule_cnt,
	count(id) filter(where schedule='remote') over(partition by city_name, query_profession_name, dt) as remote_schedule_cnt,
	count(id) filter(where schedule='fullDay') over(partition by city_name, query_profession_name, dt) as full_day_schedule_cnt,
	count(id) filter(where schedule='shift') over(partition by city_name, query_profession_name, dt) as shift_schedule_cnt,
	count(id) filter(where schedule='flyInFlyOut') over(partition by city_name, query_profession_name, dt) as fly_in_fly_out_schedule_cnt
from tmp_vacancies
on conflict (city_name, query_profession_name, dt) do update 
set 
	cnt = EXCLUDED.cnt,
	no_experience_cnt = EXCLUDED.no_experience_cnt,
	between_1_and_3_cnt = EXCLUDED.between_1_and_3_cnt,
	between_3_and_6_cnt = EXCLUDED.between_3_and_6_cnt,
	more_than_6_cnt = EXCLUDED.more_than_6_cnt,
	no_experience_avg_salary = EXCLUDED.no_experience_avg_salary,
	between_1_and_3_avg_salary = EXCLUDED.between_1_and_3_avg_salary,
	between_3_and_6_avg_salary = EXCLUDED.between_3_and_6_avg_salary,
	more_than_6_avg_salary = EXCLUDED.more_than_6_avg_salary,
	flexible_schedule_cnt = EXCLUDED.flexible_schedule_cnt,
	remote_schedule_cnt = EXCLUDED.remote_schedule_cnt,
	full_day_schedule_cnt = EXCLUDED.full_day_schedule_cnt,
	shift_schedule_cnt = EXCLUDED.shift_schedule_cnt,
	fly_in_fly_out_schedule_cnt = EXCLUDED.fly_in_fly_out_schedule_cnt;

--Вставляем данные в витрину
with tmp_skills as (
	select 
		dc.name as city_name,
		dqp.name as query_profession_name,
		dv.dt,
		row_number() over(partition by dc.name, dqp.name, dv.dt order by count(dv.vacancy_id) desc, ds.name) as top,
		ds.name as skill_name,
		count(dv.vacancy_id) as cnt
	from d_skill as ds
		inner join fct_skill_vacancy as fsv on ds.id = fsv.skill_id
		inner join d_vacancies as dv on fsv.vacancy_id = dv.id
		inner join d_city as dc on dv.city_id = dc.id
		inner join d_query_profession dqp on dqp.id = dv.query_profession_id
	where dv.dt = (current_date - '1 day'::interval)::date
	group by dc.name,
		dqp.name,
		dv.dt,
		ds.name
		)
insert into dm_skills(city_name, query_profession_name, skill_name, dt, top, cnt)
select 
	city_name,
	query_profession_name,
	skill_name,
	dt,
	top,
	cnt
from tmp_skills
where top <= 10
on conflict (city_name, query_profession_name, skill_name, dt) do update 
set 
	top = EXCLUDED.top,
	cnt = EXCLUDED.cnt;

delete from stg_vacancies where query_dt=(current_date - '1 day'::interval)::date;

delete from stg_exchange_rates where query_dt=(current_date - '1 day'::interval)::date;