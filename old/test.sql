select * from metrics m;

select * from skills s; 

truncate metrics; 

truncate skills;

drop table skills;

SELECT count(*) FROM vacancies;

select * from city c 

select * from profession p 

truncate vacancies 



select * from get_metric(1,2)

select * from get_metric(1,1,'2023-11-13', '2023-11-14');

drop function get_metric

select * from get_skills(1, 1)


select dt, count(1) from vacancies v group by dt;
