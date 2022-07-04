import common.emulator
import common.windows_client
import common.storage
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
from sqlalchemy import select
import models
import db
from PIL import Image, ImageDraw
from datetime import datetime
import logging
import logging.handlers
import data_scan
import ast
import re
import time
import pyautogui

log = logging.getLogger(__name__)
handler = logging.handlers.WatchedFileHandler('scratchpad.log', encoding='utf-8')
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
root = logging.getLogger()
root.setLevel('INFO')
root.addHandler(handler)
root.addHandler(console_handler)

logging.basicConfig(level='INFO')

def upload_test():
    kingdom = 2402
    date = '2022-03-18-test2'
    storage = common.storage.FileStorage(prefix=r'{}\{}'.format(kingdom, date))
    storage.upload_to_s3()

def debug():
    # im = Image.open('samples/2022-03-23_profile_error_424_1.png')
    # mail_crop = im.crop(config.coordinates['1920x1080']['mail'])
    # text, _ = common.ocr.get_text(mail_crop)
    # print(text)
    im = Image.open('samples/83043874_more_info.png')
    result = contribution_parser.parse_more_info_image(im)
    print(result)
    image = Image.open('samples/2022-04-04_profile_error_36047006_3.png')
    mail_crop = image.crop(config.coordinates['1920x1080']['mail'])
    mail_crop.show()
    text, _ = common.ocr.get_text(mail_crop)
    result = text == 'Mail'
    print(text)
    print(result)

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

def test_materialzed_view():
    engine = db.init_db(config.databases['rds'])
    with Session(engine) as session:
        session.add(models.Pulls(pull_id='2022-03-27', timestamp=datetime(2022, 3, 27, 1, 34)))
        session.commit()
    with engine.connect() as con:
        con.execute('REFRESH MATERIALIZED VIEW latest_stats_pull')

def image_tuning():
    kills_pattern = re.compile('(\d+)_kills.png')
    still_failing_parses = {}
    for thresh in range(128,140):
        failures = []
        for count, kills_path in enumerate(iter(glob.glob(r'output/files/{}/{}/'.format(2402, '2022-03-30') + r'\*_kills.png'))):
            kills_match = kills_pattern.search(kills_path)
            governor_id = kills_match.group(1)
            im = Image.open(kills_path)
            result = contribution_parser.parse_kill_image(im, thresh)
            if (count % 60) == 0:
                print('{}: {} parsing person {:3d}: {}'.format(datetime.now().strftime('%H:%M:%S'), thresh, count + 1, governor_id))
            if result['check_kills']:
                temp = {'governor_id': governor_id}
                temp.update(result)
                failures.append(temp)
        still_failing_parses[thresh] = {
            "thresh": thresh,
            "num_failures": len(failures),
            "failures": failures
        }
        print("thresh={}; fails={}".format(thresh, len(failures)))
    print(still_failing_parses)

def startup_tuning():
    kingdom = 2402
    pull_label = 'startup_tuning'
    lk_emulator = common.emulator.Rok_Emulator(config.emulators['genymotion-2402-lk'])
    storage = common.storage.FileStorage(prefix=r'{}\{}'.format(kingdom, pull_label))
    lk_low_power_scraper = contribution_scraper.StatsScraper(lk_emulator, storage, '1920x1080', 0, kingdom, pull_label,
                                                             parse=True)
    lk_emulator.initialize()
    lk_emulator.start_rok()

def grab_screenshot():
    lk_emulator = common.emulator.Rok_Emulator(config.emulators['genymotion-2402'])
    lk_emulator.initialize()
    lk_emulator.get_screen()

def pc_test():
    pull_label = 'pc_test'
    kingdom = 2402
    emulator = common.windows_client.PC_Client()
    emulator.initialize()
    storage = common.storage.FileStorage(prefix=r'{}\{}'.format(kingdom, pull_label))
    gov_ids = [
        70180227,
        # 43967354,
        # 17686028,
        # 42265113,
        # 42243152,
        # 7626978,

    ]
    scraper = contribution_scraper.StatsScraper(emulator, storage, '1920x1080', 0, kingdom, pull_label, parse=True)
    for gov_id in gov_ids:
        scraper.search_for_governor_by_id(gov_id)
        pass

    while True:
        x, y = pyautogui.position()
        positionStr = 'X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4)
        print(positionStr)
        time.sleep(1)

def kill_parse_debug():
    with Image.open('output/files/2402/pc_test/70180227_kills.png') as im:
        contribution_parser.parse_kill_image(im)

def main():
    pc_test()
    # kill_parse_debug()
    pass

def backfill():
    pull_label = '2022-05-09_03_before_altar_1'
    engine = db.init_db(config.databases['rds'])
    with Session(engine) as session:
        governors_to_find = {str(row.Governors.governor_id): row.Governors.last_known_name for row in
                             session.execute(select(models.Governors).where(models.Governors.last_seen != pull_label,
                                                                            models.Governors.ignore == False))}
        print(len(governors_to_find))
        data_scan.find_specific_governors(governors_to_find, 2402, pull_label, 'lasfdjfd-dev-5')

def get_window_bounds(image):
    thresh = 40
    fn = lambda x: 255 if x > thresh else 0
    mask = image.convert('L').point(fn, mode='1')
    black = Image.new('RGB', image.size)
    masked = Image.composite(image, black, mask)
    return masked.getbbox()

def draw_circle(draw, coordinate):
    draw.ellipse([coordinate[0]-5, coordinate[1]-5, coordinate[0]+5, coordinate[1]+5], fill='red')

def draw_kills_boxes(image, coordinates):
    draw = ImageDraw.Draw(image)
    draw.rectangle(coordinates['governor_id'], fill=None, outline='red')
    draw.rectangle(coordinates['mail'], fill=None, outline='red')
    draw.rectangle(coordinates['t1_kills'], fill=None, outline='red')
    draw.rectangle(coordinates['t2_kills'], fill=None, outline='red')
    draw.rectangle(coordinates['t3_kills'], fill=None, outline='red')
    draw.rectangle(coordinates['t4_kills'], fill=None, outline='red')
    draw.rectangle(coordinates['t5_kills'], fill=None, outline='red')
    draw.rectangle(coordinates['total_kill_points'], fill=None, outline='red')
    draw_circle(draw, coordinates['name'])
    draw_circle(draw, coordinates['expand_kill_points'])
    draw_circle(draw, coordinates['more_info'])
    draw_circle(draw, coordinates['close_profile'])
    image.show()

def draw_info_boxes(image, coordinates):
    draw = ImageDraw.Draw(image)
    draw.rectangle(coordinates['power'], fill=None, outline='red')
    draw.rectangle(coordinates['deads'], fill=None, outline='red')
    draw.rectangle(coordinates['rss_gathered'], fill=None, outline='red')
    draw.rectangle(coordinates['rss_assistance'], fill=None, outline='red')
    draw.rectangle(coordinates['helps'], fill=None, outline='red')
    draw_circle(draw, coordinates['close_more_info'])
    image.show()

def make_transformer(reference_bbox, actual_bbox):
    def transform_point(x,  y):
        x -= reference_bbox[0]
        y -= reference_bbox[1]
        x /= reference_bbox[2] - reference_bbox[0]
        y /= reference_bbox[3] - reference_bbox[1]
        x *= actual_bbox[2] - actual_bbox[0]
        y *= actual_bbox[3] - actual_bbox[1]
        x += actual_bbox[0]
        y += actual_bbox[1]
        return x, y
    def transform(tuple):
        if len(tuple) == 2:
            x, y = transform_point(tuple[0], tuple[1])
            return x,y
        if len(tuple) == 4:
            x0, y0 = transform_point(tuple[0], tuple[1])
            x1, y1 = transform_point(tuple[2], tuple[3])
            return x0, y0, x1, y1
    return transform

def transform_profile(actual_bbox):
    coordinates = {}
    transform = make_transformer(config.coordinates['1920x1080']['profile_bbox'], actual_bbox)
    keys_to_transform = [
        'governor_id',
        'name',
        'more_info',
        'expand_kill_points',
        'close_profile',
        'mail',
        'total_kill_points',
        't1_kills',
        't2_kills',
        't3_kills',
        't4_kills',
        't5_kills',
        'profile_bbox'
    ]
    for key in keys_to_transform:
        coordinates[key] = transform(config.coordinates['1920x1080'][key])
    return coordinates


def check_boxes():
    with Image.open('samples/a_profile.png') as im:
        profile_bbox = get_window_bounds(im)
    with Image.open('samples/a_profile_more_info.png') as im:
        more_info_bbox = get_window_bounds(im)
    contribution_parser.calibrate_coordinates(profile_bbox, more_info_bbox)
    print(contribution_parser.coordinates)
    # with Image.open('samples/a_profile.png') as im:
    #     draw_kills_boxes(im, contribution_parser.coordinates)
    with Image.open('samples/a_profile_kills.png') as im:
        draw_kills_boxes(im, contribution_parser.coordinates)
    with Image.open('samples/a_profile_more_info.png') as im:
        draw_info_boxes(im, contribution_parser.coordinates)

    with Image.open('samples/b_profile.png') as im:
        profile_bbox = get_window_bounds(im)
    with Image.open('samples/b_profile_more_info.png') as im:
        more_info_bbox = get_window_bounds(im)
    contribution_parser.calibrate_coordinates(profile_bbox, more_info_bbox)
    print(contribution_parser.coordinates)
    # with Image.open('samples/b_profile.png') as im:
    #     draw_kills_boxes(im, contribution_parser.coordinates)
    with Image.open('samples/b_profile_kills.png') as im:
        draw_kills_boxes(im, contribution_parser.coordinates)
    with Image.open('samples/b_profile_more_info.png') as im:
        draw_info_boxes(im, contribution_parser.coordinates)

    with Image.open('samples/c_profile.png') as im:
        profile_bbox = get_window_bounds(im)
    with Image.open('samples/c_profile_more_info.png') as im:
        more_info_bbox = get_window_bounds(im)
    contribution_parser.calibrate_coordinates(profile_bbox, more_info_bbox)
    print(contribution_parser.coordinates)
    # with Image.open('samples/c_profile.png') as im:
    #     draw_kills_boxes(im, contribution_parser.coordinates)
    with Image.open('samples/c_profile_kills.png') as im:
        draw_kills_boxes(im, contribution_parser.coordinates)
    with Image.open('samples/c_profile_more_info.png') as im:
        draw_info_boxes(im, contribution_parser.coordinates)



def fill_governors():
    engine = db.init_db(config.databases['rds'])
    with Session(engine) as session:
        with open('samples/low_power_governor_input.csv', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                print(row)
                session.merge(models.Governors(
                    governor_id=row['id'],
                    last_known_name=row['name'],
                    last_seen='manual',
                    ignore=False
                ))
        stmt = select(models.Governor_Data).where(models.Governor_Data.pull_id == '2022-04-02')
        for row in session.execute(stmt):
            session.merge(models.Governors(
                governor_id=row.Governor_Data.governor_id,
                last_known_name=row.Governor_Data.governor_name,
                last_seen=row.Governor_Data.pull_id,
                ignore=False
            ))

        session.commit()
    pass

def mock_sets():
    engine = db.init_db(config.databases['rds'])
    with Session(engine) as session:
        governors_to_find = {str(row.Governors.governor_id): row.Governors.last_known_name for row in session.execute(select(models.Governors).where(models.Governors.ignore == False))}
        for key, value in governors_to_find.items():
            print(key, value)

def test_logging():
    log.info('Hello World')

def test_low_power_tracking():
    kingdom = 2402
    pull_label = 'low_power_test_2022-04-03'
    engine = db.init_db(config.databases['rds'])
    lk_emulator = common.emulator.Rok_Emulator(config.emulators['genymotion-2402-lk'])
    storage = common.storage.FileStorage(prefix=r'{}\{}'.format(kingdom, pull_label))

    with Session(engine) as session:
        governors_to_find = {str(row.Governors.governor_id): row.Governors.last_known_name for row in
                             session.execute(select(models.Governors).where(models.Governors.ignore == False))}

        governors_in_last_scan = [str(row.Governor_Data.governor_id) for row in session.execute(
            select(models.Governor_Data).where(models.Governor_Data.pull_id=='2022-04-03'))]

        for id in governors_in_last_scan:
            del governors_to_find[id]
        print(len(governors_to_find))

        lk_emulator.initialize()
        lk_emulator.start_rok()
        lk_low_power_scraper = contribution_scraper.StatsScraper(lk_emulator, storage, '1920x1080', 0, kingdom, pull_label,
                                                                 parse=True)
        lk_low_power_scraper.setup_governor_search()
        for governor_id, last_known_name in governors_to_find.items():
            lk_low_power_scraper.search_for_governor(last_known_name, governor_id)
        lk_emulator.close_rok()
        lk_emulator.stop()

        for stat in lk_low_power_scraper.parsed_data:
            print(stat)


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
    date = '2022-04-06'

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
