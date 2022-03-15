from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps
import pytesseract
import glob
import locale

locale.setlocale(locale.LC_NUMERIC, locale.getlocale())
raw_image = Image.open(r'assets\sample.jpg')

failed = 0

def get_black_and_white(image):
    thresh = 150
    fn = lambda  x : 255 if x > thresh else 0
    return image.convert('L').point(fn, mode='1')

def get_leaderboard_window(image):
    # image = trim(image, left=20, top=50, right=80, bottom=50) # beyeujzme
    image = trim(image, left=0, top=0, right=50, bottom=0)  # neko orange dot
    thresh = 50
    fn = lambda x: 255 if x > thresh else 0
    mask = image.convert('L').point(fn, mode='1')

    black = Image.new('RGB', image.size)
    masked = Image.composite(image, black, mask)
    return masked.crop(masked.getbbox())

def trim(image, left=0, top=0, right=0, bottom=0):
    width, height = image.size
    return image.crop((0 + left, 0 + top, width - right, height - bottom))

def parse_screenshot(raw_image):
    powers = []

    leaderboard = get_leaderboard_window(raw_image)
    # leaderboard.show()
    width, height = leaderboard.size
    left = width * 0.80
    right = width * 0.92
    top = height * 0.25
    bottom = height * 0.95
    power_crop = leaderboard.crop((left, top, right, bottom))
    black_and_white = get_black_and_white(power_crop.filter(ImageFilter.SMOOTH_MORE))
    # black_and_white.show()

    width2, height2 = black_and_white.size

    for i in range(6):
        image = black_and_white.crop((0, height2*i/6, width2, height2*(i+1)/6))
        bbox = image.getbbox()
        bounds = (bbox[0] - 5, bbox[1] - 5, bbox[2] + 5, bbox[3] + 5)
        image = image.crop(bounds)
        image = ImageOps.invert(image.convert('RGB'))
        powers.append(ocr_parse(image))
    return powers

def ocr_parse(image):
    global failed
    data = pytesseract.image_to_string(image, config=r'--psm 8', output_type=pytesseract.Output.DICT)
    value = data['text'].strip().strip('.')
    try:
        power = locale.atoi(value)
    except ValueError:
        image.show()
        print(value)
        power = input('Enter power for image:')
    return power


def process_kd(kingdom, date):
    powers = []
    page = 0
    base = r'E:\RoK\2402_KvK3'
    path = r'{}\{}\{}'.format(base, kingdom, date)
    for filename in glob.glob(path + r'\*.*'):
        page += 1
        print('Starting page: ' + str(page) + ' ' + filename)
        powers.extend(parse_screenshot(Image.open(filename)))
    if len(powers) > 0:
        with open(r'{}\output\{}\{}_{}.csv'.format(base, date, kingdom, date), 'w') as output:
            output.writelines(str(power) + '\n' for power in powers)


potential_imperiums = [
    2336,
    # 2338,
    # 2341,
    # 2345,
    # 2347,
    2361,
    # 2367,
    2375,
    # 2402
]

for kd in (str(x) for x in potential_imperiums):
    process_kd(kd, '2022-03-13')
