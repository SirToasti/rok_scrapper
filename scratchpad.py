import common.emulator
import config
import contribution_scraper
import contribution_parser
import csv
import common.ocr
import glob
from PIL import Image
import re
from datetime import datetime
import csv
from sqlalchemy.orm import Session
import models
import db
from PIL import Image


def upload_test():
    kingdom = 2402
    date = '2022-03-18-test2'
    storage = common.storage.FileStorage(prefix=r'{}\{}'.format(kingdom, date))
    storage.upload_to_s3()

def debug():
    im = Image.open('samples/2022-03-23_profile_error_424_1.png')
    mail_crop = im.crop(config.coordinates['1920x1080']['mail'])
    text, _ = common.ocr.get_text(mail_crop)
    print(text)

def debug_migrated():
    im = Image.open('samples/migrated_kills.png')
    id_crop = im.crop(config.coordinates['1920x1080']['governor_id'])
    text, raw = common.ocr.get_text(id_crop)
    print(text)
    print(raw)
    match = re.search('.{3}: ?(\d+)(#.{4})?\)', text)
    if not match:
        print('Failed to parse governor id: {}'.format(text))
    print(match.group(1))
    print(match.group(2))

def main():
    # get_low_power_governors()
    # db_test()
    debug_migrated()
    pass


def db_test():
    engine = db.init_db(config.databases['rds'])
    stats = parse_stats()

    with Session(engine) as session:
        for stat in stats:
            session.merge(models.Governor_Data(
                pull_id='2022-03-21',
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


def aws_test():
    kingdom = 2402
    date = '2022-03-21'
    limit = 990
    emulator = common.emulator.Rok_Emulator(config.emulators['genymotion-2402'])
    storage = common.storage.FileStorage(prefix=r'{}\{}'.format(kingdom, date))
    emulator.initialize()
    emulator.start_rok()
    scraper = contribution_scraper.StatsScraper(emulator, storage, '1920x1080', limit, kingdom, date, parse=True)
    scraper.setup_leaderboard_scraper()
    scraper.grab_screenshots()
    scraper.close_leaderboard_scraper()
    # scraper.setup_governor_search()
    # with open('samples/manually_tracked_governors.csv', 'r', encoding='utf-8', newline='') as csvfile:
    #     reader = csv.DictReader(csvfile)
    #     for row in reader:
    #         scraper.search_for_governor(row['Name'], row['ID'])
    emulator.close_rok()
    emulator.stop()
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
        for record in scraper.parsed_data:
            writer.writerow(record)

    engine = db.init_db(config.databases['rds'])

    with Session(engine) as session:
        records = [
            models.Governor_Data(
                pull_id=date,
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
            ) for stat in scraper.parsed_data ]
        session.add_all(records)
        session.commit()

    storage.upload_to_s3()

def get_low_power_governors():
    kingdom = 2402
    date = '2022-03-18a'
    emulator = common.emulator.Rok_Emulator(config.emulators['lasfdjfd-dev-0'])
    storage = common.storage.FileStorage()
    emulator.initialize()

    scraper = contribution_scraper.StatsScraper(emulator, storage, '1920x1080', 990, kingdom, date)
    scraper.setup_governor_search()

    with open('samples/manually_tracked_governors.csv', 'r', encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            scraper.search_for_governor(row['Name'], row['ID'])

def get_top_power_govnernors():
    kingdom = 2402
    date = '2022-03-18'
    emulator = common.emulator.Rok_Emulator(config.emulators['genymotion-2402'])
    storage = common.storage.FileStorage()
    emulator.initialize()
    emulator.start_rok()
    emulator.tap_location(config.coordinates['1920x1080']['own_profile'])
    emulator.tap_location(config.coordinates['1920x1080']['rankings'])
    emulator.tap_location(config.coordinates['1920x1080']['individual_power'])

    contribution_scraper.run_stats_scraper(kingdom, date, emulator, storage, 990)

    emulator.close_rok()


def parse_stats():
    kingdom = 2402
    date = '2022-03-21'

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


if __name__ == '__main__':
    main()
