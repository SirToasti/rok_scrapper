from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
import db
import config
import models
import json
import ast

def main():
    engine = db.init_db(config.databases['rds'])
    pull_label = '2022-05-02_02_after_ruins_20'
    with Session(engine) as session:
        session.add(models.Pulls(pull_id=pull_label, timestamp=datetime.now()))
        def add_governor_data_to_session(stat):
            session.merge(models.Governor_Data(
                pull_id=pull_label,
                governor_id=stat['governor_id'],
                governor_name=stat['name'],
                power=stat['power'],
                deads=stat['deads'],
                kill_points=stat['kill_points'],
                t1_kills=stat['t1_kills'],
                t2_kills=stat['t2_kills'],
                t3_kills=stat['t3_kills'],
                t4_kills=stat['t4_kills'],
                t5_kills=stat['t5_kills'],
                rss_gathered=stat['rss_gathered'],
                rss_assistance=stat['rss_assistance'],
                helps=stat['helps'],
                kill_parse_error=stat['check_kills']
            ))
            session.merge(models.Governors(
                governor_id=stat['governor_id'],
                last_known_name=stat['name'],
                last_seen=pull_label,
                ignore=False
            ))
        with open('output/files/2402/2022-05-02_02_after_ruins_2.csv', 'r', encoding='utf-8') as f:
            s = f.read()
            data = ast.literal_eval(s)
            print(len(data))

        for stat in data:
            add_governor_data_to_session(stat)
            print(stat)
        session.commit()

if __name__ == '__main__':
    main()
