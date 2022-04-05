from PIL import ImageOps
import pytesseract
import locale
import logging

logger = logging.getLogger(__name__)

locale.setlocale(locale.LC_NUMERIC, locale.getlocale())


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
            return x, y
        if len(tuple) == 4:
            x0, y0 = transform_point(tuple[0], tuple[1])
            x1, y1 = transform_point(tuple[2], tuple[3])
            return x0, y0, x1, y1
    return transform

def get_black_and_white(image, thresh=130):
    fn = lambda  x : 255 if x > thresh else 0
    return image.convert('L').point(fn, mode='1')

def trim_to_bbox(image):
    width, height = image.size
    try:
        left, top, right, bottom = ImageOps.invert(image).getbbox()
        return image.crop((max(left - 5, 0), max(top - 5, 0), min(right + 5, width), min(bottom + 5, height)))
    except TypeError as e:
        logger.exception(e)
        logger.debug('image.size: {}, {}'.format(width, height))
        # image.show()


def get_text(image, label=None, dark_on_light=False):
    # image.show()
    if dark_on_light:
        cleaned_image = trim_to_bbox(get_black_and_white(image, thresh=132).convert('RGB'))
    else:
        cleaned_image = trim_to_bbox(ImageOps.invert(get_black_and_white(image).convert('RGB')))
    data = pytesseract.image_to_string(cleaned_image, config=r'--psm 8 --oem 0', output_type=pytesseract.Output.DICT)
    value = data['text'].strip()
    return value, data

replacement_dict = {
    'l': 0,
    ',': 0
}

def get_number(image, label=None, dark_on_light=False):
    value, data = get_text(image, label, dark_on_light)
    while 'l' in value:
        value = value.replace('l', '1', 1)
        replacement_dict['l'] += 1
    while '.' in value:
        value = value.replace('.', ',', 1)
        replacement_dict[','] += 1
    try:
        return locale.atoi(value)
    except ValueError as e:
        if dark_on_light:
            cleaned_image = ImageOps.invert(trim_to_bbox(get_black_and_white(image).convert('RGB')))
        else:
            cleaned_image = trim_to_bbox(ImageOps.invert(get_black_and_white(image).convert('RGB')))
        logger.exception(e)
        logger.warning('failed to parse as a number: {}'.format(data))
        return -1
