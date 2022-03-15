from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps
import pytesseract
import glob
import locale
import csv
import re
from datetime import datetime


locale.setlocale(locale.LC_NUMERIC, locale.getlocale())
raw_image = Image.open(r'assets\sample.jpg')

failed = 0

def get_black_and_white(image, thresh=120):
    fn = lambda  x : 255 if x > thresh else 0
    return image.convert('L').point(fn, mode='1')

def get_window(image):
    # image = trim(image, left=20, top=50, right=80, bottom=50) # beyeujzme
    # image = trim(image, left=0, top=0, right=50, bottom=0)  # neko orange dot
    thresh = 40
    fn = lambda x: 255 if x > thresh else 0
    mask = image.convert('L').point(fn, mode='1')

    black = Image.new('RGB', image.size)
    masked = Image.composite(image, black, mask)
    return masked.crop(masked.getbbox())

def trim(image, left=0, top=0, right=0, bottom=0):
    width, height = image.size
    return image.crop((0 + left, 0 + top, width - right, height - bottom))

def clean_id(text):
    match = re.search('(\(ID: \d+\))', text)
    if not match:
        print('Failed to parse governor id: {}'.format(text))
    return match.group()

tag_map = {
    "[20Jf]japanese fighters":      '20Jf',
    "(20TSJABRFE":                  '20TS',
    "[20X0]ZodiaX-NSFW":            '20XO',
    "(20VK]44e]~!":                 '20VK',
    r"(20GS])\v¥ > 38":             '20GS',
    "[20VS]2020 Valkyries":         '20VS',
    "(20PG]P's group":              '20PG',
    "(20VK]VIKING 2020":            '20VK',
    "[20FF]Farmer Farmer 2020":     '20FF',
    "(20Ss]4mel~!":                 '20SS',
    "-":                            '-',
    "[VKNK]AIL ea'vksp":            'VKNK',
    "[20TS]JABRFE":                 '20TS',
    "[20FF] Friday Fish 2020":      '20FF',
    "{20FC]NationalFarmAlliance":   '20FC',
    "[20Jf] Japanese fighters":     '20Jf',
    "[20Jf]Japanese fighters":      '20Jf',
    "[20FF] Flying Sp Farmers":     '20FF',
    "(20xo]Celestial X":            '2Oxo',
    "(DFBC) Bi eat Fee":            'DFBC',
    "[20xo]Fram Aoo 2020":          '20xo',
    "(20ts] BZBee ise":             '20ts',
    "[20GJ]PENGUINSD#E":            '20GJ',
    "[VKWU]Vk_World_Union":         'VKWU',
    "{TSRIJREPUBLIK INDONESIA":     'TSRI',
    "(JFSB] JF At Iw":              'JFSB',
    "[00X1]Zodiax Academy":         'OOX1',
    "(TSRIJREPUBLIK INDONESIA":     'TSRI',
    "(20Tc]! SR AF!":               '20Tc',
    "[ALF 2]tieOAIE":               'ALF2',
    "[20LL]japanese fighters":      '20LL',
    "[VK_A]VK Family Academy":      'VK_A',
    "[VNIx] Luxembourg":            'VNlx',
    "(TSN3]FamilyMart":             'TSN3',
    "(20tS]Bankaii":                '20tS',
    "[TIR] FATIH 1453 TURK":        'T!R',
    "{TSN8]INDO BROTHERHOOD.":      'TSN8',
    "(NKIG] BU eat":                'NKJG',
    "[VKF4]Viking Farm4":           'VKF4',
    "[20FC]NationalAlliance":       '20FC',
    "(20ts] Sse":                   '20ts',
    "[xof]xo farm":                 'xof',
    "[VS_F]Valkyries Farm":         'VS_F',
    "[VKIBJINDONESIA BISA":         'VKIB',
    "[TFSI] Tribo dos Maninhos":    'TFSI',
    "[VK_N] Nintendo Army":         'VK_N',
    "(VnD]~Dai Viét~":              'VnD',
    "(VKF1]VK2020":                 'VKF1',
    '[20GJ] PENGUINS':              '20GJ',
    '(VKsdJALIEN':                  'VKsd',
    '[AO20]Ark Team2020':           'AO20',
    r'(20GS])\v +> 38':              '20GS',
    '(20TS]JABRE':                  '20TS',
    '(20Wh]Walhalla':               '20Wh',
    '(20TR]REPUBLIK INDONESIA':     '20TR',
    '(DFBC) 6 aa% Fei':             'DFBC',
    '{20TR]REPUBLIK INDONESIA':     '20TR',
    "[VKNK]AL ea'vksp":             'VKNK',
    '(JFSB] JF 7 tI w':             'JFSB',
    r'(20GS]\v +> 38':              '20GS',
    '[VKF5]Vinland Knights':        'VKF5',
    '(20Eh]Einherjar':              '20Eh',
    '[20TR]REPUBLIK INDONESIA':     '20TR',
}

def clean_alliance(text, image):
    if text in tag_map:
        return tag_map[text]
    else:
        image.show()
        print(text)
        tag = input('Enter tag for image:')
        tag_map[text] = tag
        return tag

def parse_name_screenshot(raw_image):
    # window = get_window(raw_image)
    raw_w, raw_h = raw_image.size
    assert raw_w == 1920 and raw_h == 1080
    window = raw_image.crop((228, 83, 1692, 1006))
    # window.show()
    width, height = window.size
    id_crop = window.crop((width * .455, height * .22, width * .58, height * .265))
    id_cleaned = trim_to_bbox(ImageOps.invert(get_black_and_white(id_crop).convert('RGB')))
    # id_cleaned.show()
    id_raw, _ = ocr_parse(id_cleaned)
    gov_id = clean_id(id_raw)
    name_crop = window.crop((width * .37, height * .26, width * .75, height * .3))
    name_crop = ImageOps.invert(get_black_and_white(name_crop, 200).convert('RGB'))
    # name_crop.show()
    name, _ = ocr_parse(name_crop)
    power_crop = trim_to_bbox(ImageOps.invert(get_black_and_white(window.crop((width * .58, height * .38, width * .75, height * .45))).convert('RGB')))
    power = ocr_parse_number(power_crop, 'power')

    alliance_crop = trim_to_bbox(ImageOps.invert(get_black_and_white(window.crop((width * .36, height * .38, width * .58, height * .45)), thresh=200).convert('RGB')))
    alliance_raw, data = ocr_parse(alliance_crop)
    alliance_tag = clean_alliance(alliance_raw, alliance_crop)
    return name, gov_id, power, alliance_tag


def trim_to_bbox(image):
    width, height = image.size
    left, top, right, bottom = ImageOps.invert(image).getbbox()
    return image.crop((max(left - 5, 0), max(top - 5, 0), min(right + 5, width), min(bottom + 5, height)))


def parse_stats_screenshot(raw_image):
    window = get_window(raw_image)
    # window.show()
    width, height = window.size
    left = width * 0.59
    right = width * 0.84
    top = height * 0.18
    bottom = height * 0.435
    kills_crop = get_black_and_white(window.crop((left, top, right, bottom))).convert('RGB')
    # kills_crop.show()
    width2, height2, = kills_crop.size
    total_crop = trim_to_bbox(kills_crop.crop((width2 * 0.265, 0, width2 * .6, height2 * 0.15)))
    # total_crop.show()
    t1_crop = trim_to_bbox(kills_crop.crop((width2 * 0.125, height2 * .37, width2 * .50, height2 * 0.6)))
    # t1_crop.show()
    t2_crop = trim_to_bbox(kills_crop.crop((width2 * 0.60, height2 * .37, width2, height2 * 0.6)))
    # t2_crop.show()
    t3_crop = trim_to_bbox(kills_crop.crop((width2 * 0.125, height2 * .6, width2 * .50, height2 * 0.75)))
    # t3_crop.show()
    t4_crop = trim_to_bbox(kills_crop.crop((width2 * 0.60, height2 * .6, width2, height2 * 0.75)))
    # t4_crop.show()
    t5_crop = trim_to_bbox(kills_crop.crop((width2 * 0.125, height2 * .75, width2 * .50, height2)))
    # t5_crop.show()

    left2 = width * .75
    right2 = width * .9
    black_and_white2 = ImageOps.invert(get_black_and_white(window).convert('RGB'))
    dead_crop = trim_to_bbox(black_and_white2.crop((left2, height * .49, right2, height * .54)))
    # dead_crop.show()
    gather_crop = trim_to_bbox(black_and_white2.crop((left2, height * .69, right2, height * .74)))
    # gather_crop.show()
    assist_crop = trim_to_bbox(black_and_white2.crop((left2, height * .76, right2, height * .81)))
    # assist_crop.show()
    help_crop = trim_to_bbox(black_and_white2.crop((left2, height * .83, right2, height * .88)))
    # help_crop.show()

    return {
        "total kills": ocr_parse_number(total_crop, 'total kills'),
        "t1 kills": ocr_parse_number(t1_crop, 't1 kills'),
        "t2 kills": ocr_parse_number(t2_crop, 't2 kills'),
        "t3 kills": ocr_parse_number(t3_crop, 't3 kills'),
        "t4 kills": ocr_parse_number(t4_crop, 't4 kills'),
        "t5 kills": ocr_parse_number(t5_crop, 't5 kills'),
        "deads": ocr_parse_number(dead_crop, 'deads'),
        "rss gathered": ocr_parse_number(gather_crop, 'gathering'),
        "rss assistance": ocr_parse_number(assist_crop, 'rss assistance'),
        "helps": ocr_parse_number(help_crop, 'helps'),
    }

def pairwise(iterable):
    return zip(*[iter(iterable)]*2)

def ocr_parse_number(image, label=None):
    value, data = ocr_parse(image)
    try:
        match = re.search('[1-9][0-9,]*',value.strip().replace('$', '5').replace(' ', ','))
        power = locale.atoi(match.group())
    except (ValueError, AttributeError):
        print(data)
        # ImageOps.invert(image.convert('RGB')).show()
        if label:
            print('Error parsing {}'.format(label))
        if label.endswith('kills') or label.endswith('deads') or label.endswith('rss assistance'):
            power = 0
        else:
            image.show()
            power = locale.atoi(input('Enter power for image:'))
    return power


def ocr_parse(image):
    # image.show()
    data = pytesseract.image_to_string(image, config=r'--psm 8', output_type=pytesseract.Output.DICT)
    value = data['text'].strip()
    return value, data


def process(date):
    # base = r'E:\RoK\2020_KvK2'
    # path = r'{}\{}\{}'.format(base, kingdom, date)
    # path = r'C:\Users\lawre\PycharmProjects\RoK\power\assets\contribution_samples'
    path = r'E:\RoK\2020_KvK2\contribution\{}'.format(date)
    output_file = path + '.csv'
    with open(output_file, 'a', newline='') as csvfile:
        fieldnames = ['needs_review', 'parsed_name', 'id', 'tag', 'power', 'total kills', 't5 kills', 't4 kills', 't3 kills', 't2 kills', 't1 kills', 'deads', 'rss gathered', 'rss assistance', 'helps', 'source']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for count, (first, second) in enumerate(zip(*[iter(glob.glob(path + r'\*.*'))]*2)):
            if count < 42:
                continue
            if count > 43:
                break
            print('{}: parsing person {:3d}: {} {}'.format(datetime.now().strftime('%H:%M:%S'), count + 1, first, second))
            name, id, power, tag = parse_name_screenshot(Image.open(first))
            results = parse_stats_screenshot(Image.open(second))
            needs_review = results['total kills'] != results['t1 kills'] + results['t2 kills'] + results['t3 kills'] + results['t4 kills'] + results['t5 kills']
            needs_review |= results['deads'] == -1
            needs_review |= results['rss gathered'] == -1
            needs_review |= results['rss assistance'] == -1
            needs_review |= results['helps'] == -1
            results['needs_review'] = needs_review
            results['parsed_name'] = name
            results['id'] = id
            results['power'] = power
            results['tag'] = tag
            results['source'] = second
            writer.writerow(results)


process('2021-04-08')