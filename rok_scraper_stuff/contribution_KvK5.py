from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps
from PIL import ImageDraw
import pytesseract
import glob
import locale
import csv
import re
from datetime import datetime


locale.setlocale(locale.LC_NUMERIC, locale.getlocale())

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
    print(masked.getbbox())
    return masked.crop(masked.getbbox())

def trim(image, left=0, top=0, right=0, bottom=0):
    width, height = image.size
    return image.crop((0 + left, 0 + top, width - right, height - bottom))

def clean_id(text):
    match = re.search('(\(ID: \d+\))', text)
    if not match:
        print('Failed to parse governor id: {}'.format(text))
    return match.group()

def parse_name_screenshot(raw_image):
    # window = get_window(raw_image)
    raw_w, raw_h = raw_image.size
    assert raw_w == 1920 and raw_h == 1080
    window = raw_image.crop((228, 83, 1692, 1006))
    # window.show()
    width, height = window.size
    id_crop = window.crop((width * .455, height * .22, width * .58, height * .265))
    id_cleaned = trim_to_bbox(ImageOps.invert(get_black_and_white(id_crop, thresh=130).convert('RGB')))
    # id_cleaned.show()
    id_raw, _ = ocr_parse(id_cleaned)
    gov_id = clean_id(id_raw)
    name_crop = window.crop((width * .37, height * .26, width * .75, height * .3))
    name_crop = ImageOps.invert(get_black_and_white(name_crop, 200).convert('RGB'))
    # name_crop.show()
    name, _ = ocr_parse(name_crop)

    return name, gov_id


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


def parse_more_info_screenshot(raw_image):
    raw_w, raw_h = raw_image.size
    if raw_w == 2800 and raw_h == 1752:
        window = raw_image.crop((277, 121, 2523, 1634))
    else:
        window = get_window(raw_image)
    # window.show()
    width, height = window.size
    left2 = width * .75
    right2 = width * .9
    black_and_white2 = ImageOps.invert(get_black_and_white(window, thresh=130).convert('RGB'))
    # black_and_white2.show()
    power_crop = trim_to_bbox(black_and_white2.crop((width * .512, height * .12, width * .65, height * .17)))
    # power_crop.show()

    dead_crop = trim_to_bbox(black_and_white2.crop((left2, height * .49, right2, height * .54)))
    # dead_crop.show()
    gather_crop = trim_to_bbox(black_and_white2.crop((left2, height * .69, right2, height * .74)))
    # gather_crop.show()
    assist_crop = trim_to_bbox(black_and_white2.crop((left2, height * .76, right2, height * .81)))
    # assist_crop.show()
    help_crop = trim_to_bbox(black_and_white2.crop((left2, height * .83, right2, height * .88)))
    # help_crop.show()

    return {
        "power": ocr_parse_number(power_crop, 'power'),
        "deads": ocr_parse_number(dead_crop, 'deads'),
        "rss gathered": ocr_parse_number(gather_crop, 'gathering'),
        "rss assistance": ocr_parse_number(assist_crop, 'rss assistance'),
        "helps": ocr_parse_number(help_crop, 'helps'),
    }

def parse_kills_screenshot(raw_image):
    pass

def parse_profile_with_kills_screenshot(raw_image):
    raw_w, raw_h = raw_image.size
    if raw_w == 1920 and raw_h == 1080:
        window = raw_image.crop((228, 83, 1747, 980))
    elif raw_w == 2800 and raw_h == 1752:
        window = raw_image.crop((332, 209, 2549, 1500))
        # window.show()
    else:
        raise Exception("unsupported image size {}".format(raw_image.size))

    width, height = window.size
    # window.show()
    kills_crop = get_black_and_white(window.crop((width * .48, height *.4, width, height))).convert('RGB')
    # kills_crop.show()

    width2, height2, = kills_crop.size
    total_crop = trim_to_bbox(kills_crop.crop((width2 * 0.19, 0, width2 * .5, height2 * 0.12)))
    # ImageOps.invert(total_crop).show()
    # path = r'E:\RoK\2020_KvK5\test_sample.png'
    # total_crop.save(path)
    t1_crop = trim_to_bbox(kills_crop.crop((width2 * 0.105, height2 * .5, width2 * .50, height2 * 0.6)))
    # ImageOps.invert(t1_crop).show()
    t2_crop = trim_to_bbox(kills_crop.crop((width2 * 0.105, height2 * .6, width2 * .50, height2 * 0.68)))
    # ImageOps.invert(t2_crop).show()
    t3_crop = trim_to_bbox(kills_crop.crop((width2 * 0.105, height2 * .69, width2 * .50, height2 * 0.77)))
    # ImageOps.invert(t3_crop).show()
    t4_crop = trim_to_bbox(kills_crop.crop((width2 * 0.105, height2 * .78, width2 * .50, height2 * 0.87)))
    # ImageOps.invert(t4_crop).show()
    t5_crop = trim_to_bbox(kills_crop.crop((width2 * 0.105, height2 * .87, width2 * .50, height2 * 0.97)))
    # ImageOps.invert(t5_crop).show()

    return {
        "kill points": ocr_parse_number(total_crop, 'total kills'),
        "t1 kills": ocr_parse_number(t1_crop, 't1 kills'),
        "t2 kills": ocr_parse_number(t2_crop, 't2 kills'),
        "t3 kills": ocr_parse_number(t3_crop, 't3 kills'),
        "t4 kills": ocr_parse_number(t4_crop, 't4 kills'),
        "t5 kills": ocr_parse_number(t5_crop, 't5 kills'),
    }

def pairwise(iterable):
    return zip(*[iter(iterable)]*2)

def ocr_parse_number(image, label=None):
    value, data = ocr_parse(image)
    try:
        match = re.search('[1-9][0-9,.]*',value.strip().replace('$', '5').replace(' ', ',').replace('.', ','))
        power = locale.atoi(match.group())
    except (ValueError, AttributeError):
        print(data)
        if label:
            print('Error parsing {}'.format(label))
        if label.endswith('kills') or label.endswith('deads') or label.endswith('rss assistance'):
            power = 0
        else:
            image.show()
            power = locale.atoi(input('Enter value for image:'))
    return power


def ocr_parse(image):
    # image.show()
    w, h = image.size
    data = pytesseract.image_to_string(image, config=r'--psm 8', output_type=pytesseract.Output.DICT)
    boxes = pytesseract.image_to_boxes(image, config=r'--psm 8', output_type=pytesseract.Output.DICT)
    # print(boxes)
    # draw = ImageDraw.Draw(image)
    # for i in range(len(boxes['char'])):
    #     draw.rectangle([boxes['left'][i], h - boxes['top'][i], boxes['right'][i], h - boxes['bottom'][i]], fill=None, outline='red')
    # ImageOps.invert(image).show()
    value = data['text'].strip()
    return value, data


def process(kingdom, kvk, date, start=1, end=800):
    # path = r'C:\Users\lawre\PycharmProjects\RoK\power\assets\contribution_samples\new'
    path = r'E:\RoK\{}_{}\contribution\screenshots\{}'.format(kingdom, kvk, date)
    output_file = path + '.csv'

    kills_pattern = re.compile('(\d+)_kills.png')
    moreinfo_pattern = re.compile('(\d+)_moreinfo.png')

    with open(output_file, 'a', encoding='utf-8', newline='') as csvfile:
        fieldnames = ['needs_review', 'id', 'power', 'kill points', 't5 kills', 't4 kills', 't3 kills', 't2 kills', 't1 kills', 'deads', 'rss gathered', 'rss assistance', 'helps']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for count, (kills_path, more_info_path) in enumerate(zip(*[iter(glob.glob(path + r'\*.*'))]*2)):
            if count < start - 1:
                continue
            if count >= end:
                break
            kills_match = kills_pattern.search(kills_path)
            moreinfo_match = moreinfo_pattern.search(more_info_path) 
            assert kills_match and moreinfo_match
            assert kills_match.group(1) == moreinfo_match.group(1)
            gov_id = kills_match.group(1)
            print('{}: parsing person {:3d}: {}'.format(datetime.now().strftime('%H:%M:%S'), count + 1, gov_id))
            kills = parse_profile_with_kills_screenshot(Image.open(kills_path))
            other = parse_more_info_screenshot(Image.open(more_info_path))
            calculated_points = kills['t1 kills']//5 + kills['t2 kills']*2 + kills['t3 kills']*4 + kills['t4 kills']*10 + kills['t5 kills']*20
            needs_review = kills['kill points'] != calculated_points
            needs_review |= other['deads'] == -1
            needs_review |= other['rss gathered'] == -1
            needs_review |= other['rss assistance'] == -1
            needs_review |= other['helps'] == -1
            results = {
                'needs_review': needs_review,
                'id': gov_id,
            }
            results.update(kills)
            results.update(other)
            writer.writerow(results)
            # print(results)


def main():
    process('2020', 'KvK6', '2022-02-26', start=1, end=600)


if __name__ == '__main__':
    main()




def test():
    pass
    # print(parse_name_screenshot(Image.open(r'assets\contribution_samples\new\profile_with_kills.png')))
    # print(parse_more_info_screenshot(Image.open(r'assets\contribution_samples\new\more_info.png')))
    # parse_kills_screenshot(Image.open(r'assets\contribution_samples\new\kill_Breakdown.png'))
    # print(parse_profile_with_kills_screenshot(Image.open(r'assets\contribution_samples\new\profile_with_kills.png')))

# test()