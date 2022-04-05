import common.emulator
import config
import common.storage
import common.ocr
import re
import hashlib
import time
import contribution_parser
from PIL import Image

import logging

logger = logging.getLogger(__name__)

def get_window_bounds(image):
    thresh = 40
    fn = lambda x: 255 if x > thresh else 0
    mask = image.convert('L').point(fn, mode='1')
    black = Image.new('RGB', image.size)
    masked = Image.composite(image, black, mask)
    return masked.getbbox()

class StatsScraper:
    def __init__(self, emulator, storage, resolution, limit, kingdom, date, parse=False):
        self.coordinates = config.coordinates[resolution]
        self.storage = storage
        self.limit = limit
        self.emulator = emulator
        self.kingdom = kingdom
        self.date = date
        self.parse_inline = parse
        self.parsed_data = []

    def grab_screenshots(self):
        # TODO special case ranks 1,2,3
        self.emulator.tap_location(self.coordinates['row_1'])
        self.process_profile()
        self.emulator.tap_location(self.coordinates['row_2'])
        self.process_profile()
        self.emulator.tap_location(self.coordinates['row_3'])
        self.process_profile()
        i = 3
        while i < self.limit:
            self.emulator.tap_location(self.coordinates['row_4'])
            i += 1
            if self.is_on_profile(i):
                self.process_profile()
                continue
            logger.warning('profile {} failed to load'.format(i))
            self.emulator.tap_location(self.coordinates['row_5'])
            i += 1
            if self.is_on_profile(i):
                self.process_profile()
                continue
            logger.warning('profile {} failed to load'.format(i))
            self.emulator.tap_location(self.coordinates['row_6'])
            i += 1
            if self.is_on_profile(i):
                self.process_profile()
            else:
                logger.warning('profile {} failed to load'.format(i))
                raise Exception('Too many unparsable profiles')

    def setup_leaderboard_scraper(self):
        self.emulator.start_rok()
        self.emulator.tap_location(self.coordinates['own_profile'])
        self.emulator.tap_location(self.coordinates['rankings'])
        self.emulator.tap_location(self.coordinates['individual_power'])

    def calibrate(self):
        self.emulator.tap_location(self.coordinates['row_1'])
        profile = self.emulator.get_screen()
        profile_bbox = get_window_bounds(profile)
        self.emulator.tap_location(self.coordinates['more_info'])
        more_info = self.emulator.get_screen()
        more_info_bbox = get_window_bounds(more_info)
        contribution_parser.calibrate_coordinates(profile_bbox, more_info_bbox)
        self.storage.save_image(profile, '../errors/{}_{}_calibration_a.png'.format(self.date, self.emulator.name))
        self.storage.save_image(more_info, '../errors/{}_{}_calibration_b.png'.format(self.date, self.emulator.name))
        self.coordinates = contribution_parser.coordinates.copy()
        self.emulator.tap_location(self.coordinates['close_more_info'])
        self.emulator.tap_location(self.coordinates['close_profile'])

    def close_leaderboard_scraper(self):
        self.emulator.tap_location(self.coordinates['close_big_window'])
        self.emulator.tap_location(self.coordinates['close_big_window'])
        self.emulator.tap_location(self.coordinates['close_profile'])

    def setup_governor_search(self):
        self.emulator.tap_location(self.coordinates['own_profile'])
        self.emulator.tap_location(self.coordinates['settings'])

    def search_for_governor(self, governor_name, governor_id):
        self.emulator.tap_location(self.coordinates['search_governor'])
        self.emulator.tap_location(self.coordinates['search_bar'])
        self.emulator.set_clipboard(governor_name)
        self.emulator.paste()
        self.emulator.tap_location(self.coordinates['search_button'])  # exit text entry
        self.emulator.tap_location(self.coordinates['search_button'])
        time.sleep(2)
        self.emulator.tap_location(self.coordinates['view_profile'])
        if not self.is_on_profile(governor_id):
            logger.warning('unable to find {}'.format(governor_name))
        else:
            found_id = self.process_profile()
            if str(governor_id) != found_id:
                logger.warning('did not find the correct profile for id:{} name:{}'.format(governor_id, governor_name))
        self.emulator.tap_location(self.coordinates['close_big_window'])

    def process_profile(self):
        self.emulator.tap_location(self.coordinates['name'])
        self.emulator.tap_location(self.coordinates['expand_kill_points'])
        kills = self.emulator.get_screen()
        governor_id = self.extract_governor_id(kills)
        name = self.emulator.get_clipboard()
        self.emulator.tap_location(self.coordinates['more_info'])
        more_info = self.emulator.get_screen()
        self.storage.save_text(name, '{}_name.txt'.format(governor_id))
        self.storage.save_image(kills, '{}_kills.png'.format(governor_id))
        self.storage.save_image(more_info, '{}_more_info.png'.format(governor_id))
        self.emulator.tap_location(self.coordinates['close_more_info'])
        self.emulator.tap_location(self.coordinates['close_profile'])
        if not governor_id.isnumeric():
            logger.error('unrecognized governor id that was hashed: {}'.format(governor_id))
        if self.parse_inline and governor_id.isnumeric():
            data = contribution_parser.parse_stats(kills, more_info, governor_id, name)
            self.parsed_data.append(data)
        return governor_id

    def is_on_profile(self, i, depth=1):
        if depth > 3:
            return False
        image = self.emulator.get_screen()
        mail_crop = image.crop(self.coordinates['mail'])
        try:
            text, _ = common.ocr.get_text(mail_crop)
            result = text == 'Mail'
            if not result:
                self.storage.save_image(image, '../errors/{}_profile_error_{}_{}.png'.format(self.date, i, depth))
                time.sleep(1)
                return self.is_on_profile(i, depth+1)
            return True
        except TypeError:
            self.storage.save_image(image, '../errors/{}_profile_error_{}_{}.png'.format(self.date, i, depth))
            time.sleep(1)
            return self.is_on_profile(i, depth+1)

    def extract_governor_id(self, image):
        id_crop = image.crop(self.coordinates['governor_id'])
        text, raw = common.ocr.get_text(id_crop)
        match = re.search('.{3}: ?(\d+)(#.{4})?\)', text)
        if not match:
            logger.warning('Failed to parse governor id: {}'.format(text))
            return hashlib.sha1(text.encode('utf-8')).hexdigest()
        if match.group(2):
            logger.warning('Governor {} has migrated to KD{}'.format(match.group(1), match.group(2)))
        return match.group(1)

def run_stats_scraper(kingdom, date, emulator, storage, limit):
    scraper = StatsScraper(emulator, storage, '1920x1080', limit, kingdom, date)
    scraper.grab_screenshots()

