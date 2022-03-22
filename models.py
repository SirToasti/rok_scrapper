from sqlalchemy import Column, BigInteger, Integer, String, Boolean, TIMESTAMP
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Pulls(Base):
    __tablename__ = "pulls"

    pull_id = Column(String, primary_key=True)
    timestamp = Column(TIMESTAMP)

class Governor_Data(Base):
    __tablename__ = "governor_data"

    pull_id = Column(String, primary_key=True)
    governor_id = Column(Integer, primary_key=True)
    governor_name = Column(String(20))
    power = Column(BigInteger)
    deads = Column(BigInteger)
    kill_points = Column(BigInteger)
    t1_kills = Column(BigInteger)
    t2_kills = Column(BigInteger)
    t3_kills = Column(BigInteger)
    t4_kills = Column(BigInteger)
    t5_kills = Column(BigInteger)
    rss_gathered = Column(BigInteger)
    rss_assistance = Column(BigInteger)
    helps = Column(BigInteger)
    kill_parse_error = Column(Boolean)
