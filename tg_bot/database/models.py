from sqlalchemy import String, Column, Integer, Date, Numeric
from sqlalchemy.ext.declarative import declarative_base


base = declarative_base()
class DMMetrics(base):
    __tablename__ = "dm_metrics"
    id = Column(Integer,primary_key=True)
    city_name = Column(String)
    query_profession_name = Column(String)
    dt = Column(Date)
    cnt = Column(Integer)
    no_experience_cnt = Column(Integer)
    between_1_and_3_cnt = Column(Integer)
    between_3_and_6_cnt = Column(Integer)
    more_than_6_cnt = Column(Integer)
    no_experience_avg_salary = Column(Numeric(10, 2))
    between_1_and_3_avg_salary = Column(Numeric(10, 2))
    between_3_and_6_avg_salary = Column(Numeric(10, 2))
    more_than_6_avg_salary = Column(Numeric(10, 2))
    flexible_schedule_cnt = Column(Integer)
    remote_schedule_cnt = Column(Integer)
    full_day_schedule_cnt = Column(Integer)
    shift_schedule_cnt = Column(Integer)
    fly_in_fly_out_schedule_cnt = Column(Integer)