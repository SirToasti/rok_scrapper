import argparse
import db
import config
import common
import contribution_scraper
from sqlalchemy.orm import Session
from sqlalchemy import select
import models
from datetime import datetime
import logging
import logging.handlers

parser = argparse.ArgumentParser(description='Do a RoK data scan.')
parser.add_argument('kingdom')
parser.add_argument('pull_label')
parser.add_argument('hk_emulator_id')
parser.add_argument('lk_emulator_id')

logger = logging.getLogger(__name__)

def run_scraper(kingdom, pull_label, home_kd_emulator_id, lk_emulator_id):
    limit = 990
    engine = db.init_db(config.databases['rds'])
    home_kd_emulator = common.emulator.Rok_Emulator(config.emulators[home_kd_emulator_id])
    lk_emulator = common.emulator.Rok_Emulator(config.emulators[lk_emulator_id])
    storage = common.storage.FileStorage(prefix=r'{}\{}'.format(kingdom, pull_label))
    timestamp = datetime.now()

    with Session(engine) as session:
        session.add(models.Pulls(pull_id=pull_label, timestamp=timestamp))
        governors_to_find = {str(row.Governors.governor_id): row.Governors.last_known_name for row in session.execute(select(models.Governors).where(models.Governors.ignore == False))}

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
            del governors_to_find[stat['governor_id']]

        home_kd_emulator.initialize()
        home_kd_emulator.start_rok()
        scraper = contribution_scraper.StatsScraper(home_kd_emulator, storage, '1920x1080', limit, kingdom, pull_label,
                                                    parse=True)
        scraper.setup_leaderboard_scraper()
        scraper.calibrate()
        scraper.grab_screenshots()
        scraper.close_leaderboard_scraper()
        home_kd_emulator.close_rok()

        for stat in scraper.parsed_data:
            add_governor_data_to_session(stat)

        lk_emulator.initialize()
        lk_emulator.start_rok()
        lk_low_power_scraper = contribution_scraper.StatsScraper(lk_emulator, storage, '1920x1080', 0, kingdom, pull_label, parse=True)
        lk_low_power_scraper.setup_leaderboard_scraper()
        lk_low_power_scraper.calibrate()
        lk_low_power_scraper.close_leaderboard_scraper()
        lk_low_power_scraper.setup_governor_search()
        for governor_id, last_known_name in governors_to_find.items():
            lk_low_power_scraper.search_for_governor(last_known_name, governor_id)
        lk_emulator.close_rok()
        lk_emulator.stop()

        for stat in lk_low_power_scraper.parsed_data:
            add_governor_data_to_session(stat)

        hk_low_power_scraper = contribution_scraper.StatsScraper(home_kd_emulator, storage, '1920x1080', 0, kingdom, pull_label, parse=True)
        home_kd_emulator.start_rok()
        hk_low_power_scraper.setup_leaderboard_scraper()
        hk_low_power_scraper.calibrate()
        hk_low_power_scraper.close_leaderboard_scraper()
        hk_low_power_scraper.setup_governor_search()
        for governor_id, last_known_name in governors_to_find.items():
            hk_low_power_scraper.search_for_governor(last_known_name, governor_id)
        home_kd_emulator.close_rok()
        home_kd_emulator.stop()

        session.commit()
    with engine.connect() as con:
        con.execute('REFRESH MATERIALIZED VIEW latest_stats_pull')

    storage.upload_to_s3()


def main():
    args = parser.parse_args()
    root_logger = logging.getLogger()
    console_handler = logging.StreamHandler()
    handler = logging.handlers.WatchedFileHandler('logs/{}.log'.format(args.pull_label), encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    handler.setFormatter(formatter)
    root_logger.setLevel('INFO')
    root_logger.addHandler(handler)
    root_logger.addHandler(console_handler)

    try:
        run_scraper(args.kingdom, args.pull_label, args.hk_emulator_id, args.lk_emulator_id)
    except Exception as e:
        logger.exception(e)
        hk_emulator = common.emulator.Rok_Emulator(config.emulators[args.hk_emulator_id])
        hk_emulator.stop()
        lk_emulator = common.emulator.Rok_Emulator(config.emulators[args.lk_emulator_id])
        lk_emulator.stop()


if __name__ == '__main__':
    main()
