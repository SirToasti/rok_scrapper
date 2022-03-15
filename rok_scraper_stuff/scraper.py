import re
import io
import os
import sys
import time
import datetime
from ppadb.client import Client as AdbClient
from PIL import Image
from PIL import ImageDraw
from PIL import ImageOps
import pytesseract
import tkinter
import hashlib

coordinates = {
    'row_1': (0, 0),
    'row_2': (0, 0),
    'row_3': (0, 0),
    'row_4': (0, 0),
    'row_5': (0, 0),
    'row_6': (0, 0),
    'governor_id': (0, 0),
    'name': (0, 0),
    'more_info': (0, 0),
    'kill_points': (0, 0),
    'close_profile': (0, 0),
    'close_more_info': (0, 0),
    'mail': (0, 0),
}

def grab_screen(device):
    device.shell("screencap -p /sdcard/screen.png")
    device.pull("/sdcard/screen.png", "screen.png")
    im = Image.open("screen.png")
    # im = Image.open(io.BytesIO(screencap))
    return im


def save_image(image, filename):
    path = r'{}\{}\{}'.format(base_path, date, filename)
    image.save(path)


def tap_location(device, coords):
    device.shell("input tap {} {}".format(coords[0], coords[1]))
    time.sleep(1)


def get_clipboard(device):
    raw = device.shell('am broadcast -n "ch.pete.adbclipboard/.ReadReceiver"')
    data_matcher = re.compile("^.*\n.*data=\"(.*)\"$", re.DOTALL)
    data_match = data_matcher.match(raw)
    return data_match.group(1)


def prepare_directory():
    folder_path = r'{}\{}'.format(base_path, date)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def get_window_bounds(image):
    thresh = 40
    fn = lambda x: 255 if x > thresh else 0
    mask = image.convert('L').point(fn, mode='1')
    black = Image.new('RGB', image.size)
    masked = Image.composite(image, black, mask)
    return masked.getbbox()


def determine_click_locations(device):
    im = grab_screen(device)
    window_bounds = get_window_bounds(im)
    print(window_bounds)
    x_coord = (window_bounds[0] + window_bounds[2]) // 2
    height = (window_bounds[3] - window_bounds[1])
    vertical_unit = height // 17
    coordinates['row_1'] = (x_coord, window_bounds[1] + 5 * vertical_unit)
    coordinates['row_2'] = (x_coord, window_bounds[1] + 7 * vertical_unit)
    coordinates['row_3'] = (x_coord, window_bounds[1] + 9 * vertical_unit)
    coordinates['row_4'] = (x_coord, window_bounds[1] + 11 * vertical_unit)
    coordinates['row_5'] = (x_coord, window_bounds[1] + 13 * vertical_unit)
    coordinates['row_6'] = (x_coord, window_bounds[1] + 15 * vertical_unit)
    tap_location(device, coordinates['row_1'])
    profile = grab_screen(device)
    profile_bounds = get_window_bounds(profile)
    profile_width = profile_bounds[2] - profile_bounds[0]
    profile_height = profile_bounds[3] - profile_bounds[1]
    coordinates['close_profile'] = (profile_bounds[0] + profile_width * .96, profile_bounds[1] + profile_height * .05)
    coordinates['governor_id'] = (profile_bounds[0] + profile_width * .47, profile_bounds[1] + profile_height * .23)
    coordinates['name'] = (profile_bounds[0] + profile_width * .45, profile_bounds[1] + profile_height * .28)
    coordinates['kill_points'] = (profile_bounds[0] + profile_width * .76, profile_bounds[1] + profile_height * .37)
    coordinates['mail'] = (profile_bounds[0] + profile_width * .71, profile_bounds[1] + profile_height * .88)
    coordinates['more_info'] = (profile_bounds[0] + profile_width * .17, profile_bounds[1] + profile_height * .77)
    tap_location(device, coordinates['more_info'])
    more_info = grab_screen(device)
    more_info_bounds = get_window_bounds(more_info)
    more_info_width = more_info_bounds[2] - more_info_bounds[0]
    more_info_height = more_info_bounds[3] - more_info_bounds[1]
    coordinates['close_more_info'] = (more_info_bounds[0] + more_info_width * .96, more_info_bounds[1] + more_info_height * .05)
    tap_location(device, coordinates['close_more_info'])
    tap_location(device, coordinates['close_profile'])


def debug_coordinates(device):
    im = grab_screen(device)
    out = ImageDraw.Draw(im)
    for label, location in coordinates.items():
        out.ellipse([(location[0] - 5, location[1] - 5), (location[0] + 5, location[1] + 5)], 'yellow')
    im.show()


def grab_screenshots(device, limit=800):
    #TODO special case ranks 1, 2, 3
    tap_location(device, coordinates['row_1'])
    process_profile(device, 1)
    tap_location(device, coordinates['row_2'])
    process_profile(device, 2)
    tap_location(device, coordinates['row_3'])
    process_profile(device, 3)
    i = 3
    while i < limit:
        tap_location(device, coordinates['row_4'])
        i += 1
        if is_profile(device):
            process_profile(device, i)
            continue
        tap_location(device, coordinates['row_5'])
        i += 1
        if is_profile(device):
            process_profile(device, i)
            continue
        i += 1
        tap_location(device, coordinates['row_6'])
        if is_profile(device):
            process_profile(device, i)
        else:
            raise Exception('Too many unparsable profiles')

def ocr_parse(image):
    data = pytesseract.image_to_string(image, config=r'--psm 8 --oem 0', output_type=pytesseract.Output.DICT)
    value = data['text'].strip()
    return value, data


def get_black_and_white(image, thresh=120):
    fn = lambda  x : 255 if x > thresh else 0
    return image.convert('L').point(fn, mode='1')


def trim_to_bbox(image):
    width, height = image.size
    try:
        left, top, right, bottom = ImageOps.invert(image).getbbox()
    except TypeError as e:
        print(e)
        print(width, height)
        image.show()
    return image.crop((max(left - 5, 0), max(top - 5, 0), min(right + 5, width), min(bottom + 5, height)))


def get_governor_id(raw_image):
    raw_w, raw_h = raw_image.size
    if raw_w == 1920 and raw_h == 1080:
        window = raw_image.crop((228, 83, 1692, 1006))
    elif raw_w == 2800 and raw_h == 1752:
        # bounds = get_window_bounds(raw_image)
        # print(get_window_bounds(raw_image))
        window = raw_image.crop((332, 209, 2468, 1556))
    else:
        raise Exception("unsupported image size {}".format(raw_image.size))
    width, height = window.size
    id_crop = window.crop((width * .452, height * .22, width * .58, height * .255))
    # id_crop.show()
    id_cleaned = trim_to_bbox(ImageOps.invert(get_black_and_white(id_crop, thresh=130).convert('RGB')))
    id_raw, _ = ocr_parse(id_cleaned)
    match = re.search('.{3}: ?(\d+)\)', id_raw)
    if not match:
        print('Failed to parse governor id: {}'.format(id_raw))
        return hashlib.sha1(id_raw.encode('utf-8')).hexdigest()
    return match.group(1)

def process_profile(device, i):
    tap_location(device, coordinates['name'])

    tap_location(device, coordinates['kill_points'])
    kills = grab_screen(device)
    # kills.show()
    # save_image(kills, 'kill_test.png')
    # name = tk.clipboard_get()
    name = ''
    gov_id = get_governor_id(kills)
    tap_location(device, coordinates['more_info'])
    more_info = grab_screen(device)
    # more_info.show()
    # save_image(more_info, 'info_test.png')
    tap_location(device, coordinates['close_more_info'])
    tap_location(device, coordinates['close_profile'])
    print(i, gov_id, name)
    # name_path = r'{}\{}\{}_name.txt'.format(base_path, date, gov_id)
    # with open(name_path, 'w', encoding='utf-8') as f:
    #     f.write(name)
    save_image(kills, "{}_kills.png".format(gov_id))
    save_image(more_info, "{}_moreinfo.png".format(gov_id))


def is_profile(device):
    im = grab_screen(device)
    raw_w, raw_h = im.size
    if raw_w == 1920 and raw_h == 1080:
        window = im.crop((228, 83, 1692, 1006))
    elif raw_w == 2800 and raw_h == 1752:
        # bounds = get_window_bounds(raw_image)
        # print(get_window_bounds(raw_image))
        window = im.crop((332, 209, 2468, 1556))
        # window.show()
    else:
        raise Exception("unsupported image size {}".format(im.size))
    width, height = window.size
    mail_crop = window.crop((width * .68, height * .85, width * .74, height * .90))
    mail_cleaned = trim_to_bbox(ImageOps.invert(get_black_and_white(mail_crop, thresh=130).convert('RGB')))
    text, _ = ocr_parse(mail_cleaned)
    return text == 'Mail'


base_path = ''
tk = tkinter.Tk()
date = datetime.date.today().isoformat()
 

def main(kingdom, kvk, number):
    global base_path
    # serial = '127.0.0.1:5555'
    # serial = 'adb-R52NB017TKF-8k2LJv._adb-tls-connect._tcp.'
    serial = '35.84.189.47:5555'
    base_path = r'E:\Rok\{}_{}\contribution\screenshots'.format(kingdom, kvk)

    prepare_directory()
    client = AdbClient(host="127.0.0.1", port=5037)
    device = client.device(serial)
    print('Connected to ', device.serial)
    determine_click_locations(device)
    print(coordinates)
    # debug_coordinates(device)
    grab_screenshots(device, number)

if __name__ == '__main__':
    # main('2042', 'KvK1', 900)
    main('2020', 'KvK6', 100)


# PS E:\RoK\2020_KvK4\platform-tools> .\adb.exe start-server
# * daemon not running; starting now at tcp:5037
# * daemon started successfully
# PS E:\RoK\2020_KvK4\platform-tools> .\adb.exe connect 127.0.0.1:5645