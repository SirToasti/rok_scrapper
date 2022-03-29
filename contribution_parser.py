import config
import common.ocr
import logging

logger = logging.getLogger(__name__)

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


def parse_kill_image(image):
    w, h = image.size
    coordinates = config.coordinates['{}x{}'.format(w, h)]
    total_crop = image.crop(coordinates['total_kill_points'])
    t1_crop = image.crop(coordinates['t1_kills'])
    t2_crop = image.crop(coordinates['t2_kills'])
    t3_crop = image.crop(coordinates['t3_kills'])
    t4_crop = image.crop(coordinates['t4_kills'])
    t5_crop = image.crop(coordinates['t5_kills'])
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
    w, h = image.size
    coordinates = config.coordinates['{}x{}'.format(w, h)]
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
