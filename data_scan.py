import argparse
import db
import config
import common
import contribution_scraper
import contribution_parser
from sqlalchemy.orm import Session
from sqlalchemy import select
import models
from datetime import datetime
import logging
import logging.handlers
import re
import csv
import glob
from PIL import Image


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
            governors_to_find.pop(stat['governor_id'], None)

        home_kd_emulator.initialize()
        home_kd_emulator.start_rok()
        scraper = contribution_scraper.StatsScraper(home_kd_emulator, storage, '1920x1080', limit, kingdom, pull_label, parse=True)
        scraper.setup_leaderboard_scraper()
        scraper.calibrate()
        scraper.grab_screenshots()
        scraper.close_leaderboard_scraper()
        home_kd_emulator.close_rok()

        result = scraper.parsed_data
        # result = load_stats(kingdom, pull_label)
        print(len(result))
        
        for stat in result:
            add_governor_data_to_session(stat)

        print(len(governors_to_find))
        logger.info('Starting Governor Search LK Pass 1: {} to find'.format(governors_to_find))
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

        for stat in lk_low_power_scraper.parsed_data:
            add_governor_data_to_session(stat)

        print(len(governors_to_find))
        logger.info('Starting Governor Search HK Pass 1: {} to find'.format(governors_to_find))
        hk_low_power_scraper = contribution_scraper.StatsScraper(home_kd_emulator, storage, '1920x1080', 0, kingdom, pull_label, parse=True)
        home_kd_emulator.initialize()
        home_kd_emulator.start_rok()
        hk_low_power_scraper.setup_leaderboard_scraper()
        hk_low_power_scraper.calibrate()
        hk_low_power_scraper.close_leaderboard_scraper()
        hk_low_power_scraper.setup_governor_search()
        for governor_id, last_known_name in governors_to_find.items():
            hk_low_power_scraper.search_for_governor(last_known_name, governor_id)
        home_kd_emulator.close_rok()

        for stat in hk_low_power_scraper.parsed_data:
            add_governor_data_to_session(stat)

        lk_low_power_scraper.parsed_data = []
        logger.info('Starting Governor Search LK Pass 2: {} to find'.format(governors_to_find))
        lk_emulator.start_rok()
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

        hk_low_power_scraper.parsed_data = []
        logger.info('Starting Governor Search HK Pass 2: {} to find'.format(governors_to_find))
        home_kd_emulator.start_rok()
        hk_low_power_scraper.setup_leaderboard_scraper()
        hk_low_power_scraper.calibrate()
        hk_low_power_scraper.close_leaderboard_scraper()
        hk_low_power_scraper.setup_governor_search()
        for governor_id, last_known_name in governors_to_find.items():
            hk_low_power_scraper.search_for_governor(last_known_name, governor_id)
        home_kd_emulator.close_rok()
        home_kd_emulator.stop()

        for stat in hk_low_power_scraper.parsed_data:
            add_governor_data_to_session(stat)

        session.commit()
    with engine.connect() as con:
        con.execute('REFRESH MATERIALIZED VIEW latest_stats_pull')

    storage.upload_to_s3()

def parse_stats(kingdom, date):
    kills_pattern = re.compile('(\d+)_kills.png')
    moreinfo_pattern = re.compile('(\d+)_more_info.png')
    names_pattern = re.compile('(\d+)_name.txt')
    result = []

    output_file = r'output/files/{}/{}.csv'.format(kingdom, date)
    with open(output_file, 'a', encoding='utf-8', newline='') as csvfile:
        fieldnames = [
            'governor_id',
            'name',
            'power',
            'kill_points',
            't1_kills',
            't2_kills',
            't3_kills',
            't4_kills',
            't5_kills',
            'deads',
            'rss_gathered',
            'rss_assistance',
            'helps',
            'check_kills',
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for count, (kills_path, more_info_path, name_path) in enumerate(zip(*[iter(glob.glob(r'output/files/{}/{}/'.format(kingdom, date) + r'\*.*'))]*3)):
            kills_match = kills_pattern.search(kills_path)
            moreinfo_match = moreinfo_pattern.search(more_info_path)
            name_file_match = names_pattern.search(name_path)
            assert kills_match and moreinfo_match and name_file_match
            assert kills_match.group(1) == moreinfo_match.group(1)
            assert kills_match.group(1) == name_file_match.group(1)
            governor_id = kills_match.group(1)
            print('{}: parsing person {:3d}: {}'.format(datetime.now().strftime('%H:%M:%S'), count + 1, governor_id))

            name = ''
            with open(name_path, 'r', encoding='utf-8') as f:
                name = f.read().strip()
            kills_image = Image.open(kills_path)
            more_info_image = Image.open(more_info_path)
            governor_data = contribution_parser.parse_stats(kills_image, more_info_image, governor_id, name)
            result.append(governor_data)
            writer.writerow(governor_data)

        print(common.ocr.replacement_dict)
        return result

def load_stats(kingdom, pull_label):
    output_file = r'output/files/{}/{}.csv'.format(kingdom, pull_label)
    def cast_types(row):
        return {
              'governor_id': row['governor_id'],
              'name': row['name'],
              'power': int(row['power']),
              'kill_points': int(row['kill_points']),
              't1_kills': int(row['t1_kills']),
              't2_kills': int(row['t2_kills']),
              't3_kills': int(row['t3_kills']),
              't4_kills': int(row['t4_kills']),
              't5_kills': int(row['t5_kills']),
              'deads': int(row['deads']),
              'rss_gathered': int(row['rss_gathered']),
              'rss_assistance': int(row['rss_assistance']),
              'helps': int(row['helps']),
              'check_kills': row['check_kills'] == 'True'
            }
    with open(output_file, 'r', encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return [cast_types(row) for row in reader]

def find_specific_governors(governors_to_find, kingdom, pull_label, home_kd_emulator_id):
    engine = db.init_db(config.databases['rds'])
    home_kd_emulator = common.emulator.Rok_Emulator(config.emulators[home_kd_emulator_id])
    storage = common.storage.FileStorage(prefix=r'{}\{}'.format(kingdom, pull_label))

    with Session(engine) as session:
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

        home_kd_emulator.initialize()
        home_kd_emulator.start_rok()
        hk_low_power_scraper = contribution_scraper.StatsScraper(home_kd_emulator, storage, '1920x1080', 0, kingdom, pull_label, parse=True)
        hk_low_power_scraper.setup_leaderboard_scraper()
        hk_low_power_scraper.calibrate()
        hk_low_power_scraper.close_leaderboard_scraper()

        hk_low_power_scraper.setup_governor_search()
        for governor_id, last_known_name in governors_to_find.items():
            hk_low_power_scraper.search_for_governor(last_known_name, governor_id)
        home_kd_emulator.close_rok()
        home_kd_emulator.stop()

        for stat in hk_low_power_scraper.parsed_data:
            add_governor_data_to_session(stat)

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
