import config
import common.ocr
import logging

logger = logging.getLogger(__name__)

coordinates = config.coordinates['1920x1080'].copy()

def calibrate_coordinates(profile_bbox, info_bbox):
    reference = config.coordinates['1920x1080'].copy()
    profile_transformer = common.ocr.make_transformer(reference['profile_bbox'], profile_bbox)
    info_transformer = common.ocr.make_transformer(reference['more_info_bbox'], info_bbox)
    profile_keys = [
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
    ]
    info_keys = [
        'power',
        'deads',
        'rss_gathered',
        'rss_assistance',
        'helps',
        'close_more_info',
        'search_button',
    ]
    for key in profile_keys:
        coordinates[key] = profile_transformer(reference[key])
    for key in info_keys:
        coordinates[key] = info_transformer(reference[key])


kill_reference_coordinates = {
    'total_kill_points': (167, 37, 404, 68),
    't1_kills': (94, 286, 304, 316),
    't2_kills': (94, 336, 304, 366),
    't3_kills': (94, 391, 304, 421),
    't4_kills': (94, 441, 304, 471),
    't5_kills': (94, 496, 304, 526)
}

def parse_stats(kills_image, more_info_image, governor_id, name):
    try:
        kills = parse_kill_image(kills_image)
        more_info = parse_more_info_image(more_info_image)
        result = {
            'governor_id': governor_id,
            'name': name,
        }
        result.update(kills)
        result.update(more_info)
        logger.info(result)
        return result
    except Exception as e:
        logger.error('failed to parse profile: {}'.format(e))
        logger.exception(e)
        return None

def get_kill_box(im):
    bw = common.ocr.get_black_and_white(im, 240).convert('RGB')
    bbox = bw.getbbox()
    bw = bw.crop(bbox)
    w, h = bw.size
    top = h - 15
    left = w - 15
    while bw.getpixel((w - 15, top)) == (255, 255, 255):
        top -= 1
    while bw.getpixel((left, h - 15)) == (255, 255, 255):
        left -= 1
    box_bottom = h - 15
    while bw.getpixel((w-50, box_bottom)) == (255, 255, 255):
        box_bottom -= 1
    kill_bbox = (bbox[2] - (w - left) + 1, bbox[3] - (h - top) + 1, bbox[2], bbox[3])
    return im.crop(kill_bbox), box_bottom - top + 1

def get_scaled_coordinates(hk, vk):
    coordinates = kill_reference_coordinates.copy()
    for key in coordinates:
        coordinates[key] = (coordinates[key][0]*hk, coordinates[key][1]*vk, coordinates[key][2]*hk, coordinates[key][3]*vk)
    return coordinates

def parse_kill_image(image):
    kill_box, box_bottom = get_kill_box(image)
    w, h = kill_box.size
    kill_coordinates = get_scaled_coordinates(w/800, box_bottom/537)
    total_crop = kill_box.crop(kill_coordinates['total_kill_points'])
    t1_crop = kill_box.crop(kill_coordinates['t1_kills'])
    t2_crop = kill_box.crop(kill_coordinates['t2_kills'])
    t3_crop = kill_box.crop(kill_coordinates['t3_kills'])
    t4_crop = kill_box.crop(kill_coordinates['t4_kills'])
    t5_crop = kill_box.crop(kill_coordinates['t5_kills'])
    total_kill_points = common.ocr.get_number(total_crop, label=None, dark_on_light=True)
    t1_kills = common.ocr.get_number(t1_crop, label=None, dark_on_light=True)
    t2_kills = common.ocr.get_number(t2_crop, label=None, dark_on_light=True)
    t3_kills = common.ocr.get_number(t3_crop, label=None, dark_on_light=True)
    t4_kills = common.ocr.get_number(t4_crop, label=None, dark_on_light=True)
    t5_kills = common.ocr.get_number(t5_crop, label=None, dark_on_light=True)
    calculated_points = t1_kills//5 + t2_kills*2 + t3_kills*4 + t4_kills*10 + t5_kills*20
    return {
        'kill_points': total_kill_points,
        't1_kills': t1_kills,
        't2_kills': t2_kills,
        't3_kills': t3_kills,
        't4_kills': t4_kills,
        't5_kills': t5_kills,
        'check_kills': calculated_points != total_kill_points
    }


def parse_more_info_image(image):
    power_crop = image.crop(coordinates['power'])
    dead_crop = image.crop(coordinates['deads'])
    rss_gathered_crop = image.crop(coordinates['rss_gathered'])
    rss_assistance_crop = image.crop(coordinates['rss_assistance'])
    helps_crop = image.crop(coordinates['helps'])
    power = common.ocr.get_number(power_crop)
    deads = common.ocr.get_number(dead_crop)
    rss_gathered = common.ocr.get_number(rss_gathered_crop)
    rss_assistance = common.ocr.get_number( rss_assistance_crop)
    helps = common.ocr.get_number(helps_crop)
    return {
        'power': power,
        'deads': deads,
        'rss_gathered': rss_gathered,
        'rss_assistance': rss_assistance,
        'helps': helps,
    }
