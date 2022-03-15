from PIL import Image
from PIL import ImageStat
from PIL import ImageOps
import pytesseract
import glob
import locale

locale.setlocale(locale.LC_NUMERIC, locale.getlocale())


def get_black_and_white(image, thresh=150):
    fn = lambda  x : 255 if x > thresh else 0
    return image.convert('L').point(fn, mode='1').convert('RGB')

def get_mail_window(image):
    thresh = 50
    fn = lambda x: 255 if x > thresh else 0
    mask = image.convert('L').point(fn, mode='1')

    black = Image.new('RGB', image.size)
    masked = Image.composite(image, black, mask)
    return masked.crop(masked.getbbox())

def clean_record(image):
    bands = image.convert('RGB').split()
    bounds = bands[2].point(lambda x: 255 if x > 200 else 0).getbbox()
    return image.crop(bounds)

def trim(image, left=0, top=0, right=0, bottom=0):
    width, height = image.size
    return image.crop((0 + left, 0 + top, width - right, height - bottom))

def parse_record(record):
    result = {
        'Name': '',
        'Timestamp': '',
        'Food': 0,
        'Wood': 0,
        'Stone': 0,
        'Gold': 0,
    }
    width, height = record.size
    name_box = record.crop((0, 0, width * .75, height * .29))
    timestamp_box = record.crop((width * .75, 0, width, height * .29))
    for i in range(4):
        rss_section = record.crop((width * i/4, height * .30, width * (i+1)/4, height))
        rss_type, value = parse_resources(rss_section)
        if not rss_type:
            break
        result[rss_type] = value

    prefix = 'From Ally: '
    name = ocr_parse(name_box)
    name = name[len(prefix):] if name.startswith(prefix) else name
    result['Name'] = name
    timestamp = ocr_parse(timestamp_box)
    result['Timestamp'] = timestamp

    print(result)
    pass

def parse_resources(rss_section):
    # rss_section.show()
    value_text = get_black_and_white(rss_section, thresh=240).convert('RGB')
    value_bbox = value_text.getbbox()
    if not value_bbox:
        return None, None
    value = ocr_parse(ImageOps.invert(value_text))
    text_height = value_bbox[3] - value_bbox[1]
    icon_height = text_height * 2.8
    icon_section = rss_section.crop((value_bbox[0] - 5 - icon_height ,value_bbox[3] - text_height * .25 - icon_height/2,value_bbox[0] - 5, value_bbox[3] - text_height * .25 + icon_height/2))
    rss_type = guess_rss_type(icon_section)
    return rss_type, locale.atoi(value)

def ocr_parse(image):
    data = pytesseract.image_to_string(image, output_type=pytesseract.Output.DICT)
    return data['text'].strip()

def guess_rss_type(image):
    extrema = ImageStat.Stat(image).extrema
    red, green, blue = 0, 1, 2
    low, high = 0, 1
    if extrema[blue][high] > 230:
        return 'Stone'
    if extrema[red][low] < 40:
        return 'Food'
    if extrema[green][low] > 50:
        return 'Gold'
    if extrema[green][low] < 50:
        return 'Wood'
    return None

def isolate_records(image):
    mail_window = get_mail_window(image)
    # mail_window.show()

    mail_width, mail_height = mail_window.size
    report = mail_window.crop((mail_width * .36, mail_height * .14, mail_width * .96, mail_height * .89))
    # report.show()

    records_per_page = 4
    records = []
    report_width, report_height = report.size
    for i in range(records_per_page):
        record_rough = report.crop((0, report_height*i/records_per_page, report_width, report_height*(i+1)/records_per_page))
        record = clean_record(record_rough)
        records.append(parse_record(record))


def main():
    for filename in glob.glob(r'assets\liverbird_samples\*.png'):
        screenshot = Image.open(filename)
        isolate_records(screenshot)
        pass

if __name__== '__main__':
    main()