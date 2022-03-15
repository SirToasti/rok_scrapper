import glob
import re
import pytesseract
from PIL import Image
from PIL import ImageOps

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

def ocr_parse(image):
    config_file = r'C:\Users\lawre\PycharmProjects\RoK\power\configs\gov_ids.user-patterns'
    configs = r'--psm 8 --oem 0 --user-patterns {}'.format(config_file)
    data = pytesseract.image_to_string(image, config=configs, output_type=pytesseract.Output.DICT)
    value = data['text'].strip()
    return value, data

def get_id(crop):
    id_cleaned = trim_to_bbox(ImageOps.invert(get_black_and_white(crop, thresh=130).convert('RGB')))
    # id_cleaned.show()
    id_raw, _ = ocr_parse(id_cleaned)
    match = re.search('.{3}: ?(\d+)\)', id_raw)
    if not match:
        print('Failed to parse governor id: {}'.format(id_raw))
        id_cleaned.show()
        return
    print(match.group(1))


def get_id_crop(raw_image):
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
    return id_crop


def scraper():
    basepath = r'E:\RoK\2020_KvK5\contribution\screenshots\2021-11-01'
    kills_pattern = re.compile('(\d+)_kills.png')
    for imagepath in iter(glob.glob(basepath + r'\*_kills.png')):
        kills_match = kills_pattern.search(imagepath)
        gov_id = kills_match.group(1)
        raw_image = Image.open(imagepath)
        id_crop = get_id_crop(raw_image)
        path = r'assets\id_samples\{}.png'.format(gov_id)
        id_crop.save(path)


def run_sample():
    for imagepath in iter(glob.glob('assets\id_samples\*.png')):
        crop = Image.open(imagepath)
        get_id(crop)


if __name__ == "__main__":
    scraper()
    run_sample()
