import argparse
import db
import config
import common
import contribution_scraper
from sqlalchemy.orm import Session
import models
from datetime import datetime

parser = argparse.ArgumentParser(description='Do a RoK data scan.')
parser.add_argument('kingdom')
parser.add_argument('pull_label')
parser.add_argument('emulator_id')


def run_scraper(kingdom, pull_label, emulator_id):
    limit = 990
    engine = db.init_db(config.databases['rds'])
    emulator = common.emulator.Rok_Emulator(config.emulators[emulator_id])
    storage = common.storage.FileStorage(prefix=r'{}\{}'.format(kingdom, pull_label))
    timestamp = datetime.now()
    emulator.initialize()
    emulator.start_rok()
    scraper = contribution_scraper.StatsScraper(emulator, storage, '1920x1080', limit, kingdom, pull_label, parse=True)
    scraper.setup_leaderboard_scraper()
    scraper.grab_screenshots()
    scraper.close_leaderboard_scraper()
    emulator.close_rok()
    emulator.stop()

    with Session(engine) as session:
        session.add(models.Pulls(pull_id=pull_label, timestamp=timestamp))
        for stat in scraper.parsed_data:
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
        session.commit()
    with engine.connect() as con:
        con.execute('REFRESH MATERIALIZED VIEW latest_stats_pull')

    storage.upload_to_s3()


def main():
    args = parser.parse_args()
    run_scraper(args.kingdom, args.pull_label, args.emulator_id)


if __name__ == '__main__':
    main()
