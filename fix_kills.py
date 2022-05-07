from PIL import Image, ImageDraw
import config
import common.ocr

import boto3
import os
import db
from sqlalchemy.orm import Session
from sqlalchemy import select
import models

# reference_coordinates = {
#     'total_kill_points': (1113, 476, 1350, 507),
#     't1_kills': (1040, 725, 1250, 755),
#     't2_kills': (1040, 775, 1250, 805),
#     't3_kills': (1040, 830, 1250, 860),
#     't4_kills': (1040, 880, 1250, 910),
#     't5_kills': (1040, 935, 1250, 965),
# }

reference_coordinates = {
    'total_kill_points': (167, 37, 404, 68),
    't1_kills': (94, 286, 304, 316),
    't2_kills': (94, 336, 304, 366),
    't3_kills': (94, 391, 304, 421),
    't4_kills': (94, 441, 304, 471),
    't5_kills': (94, 496, 304, 526)
}
BUCKET_NAME = 'rok-2402-screenshots'
s3_client = boto3.resource('s3')
bucket = s3_client.Bucket(BUCKET_NAME)

def download_kills_image(pull_id, gov_id):
    dir_path = os.path.join(r'kills_to_fix', pull_id)
    os.makedirs(dir_path, exist_ok=True)
    key = '2402/{}/{}_kills.png'.format(pull_id, gov_id)
    filename = '{}_kills.png'.format(gov_id)
    save_location = os.path.join(dir_path, filename)
    s3_client.Object(BUCKET_NAME, key).download_file(save_location)
    return save_location

def draw_circle(draw, coordinate):
    draw.ellipse([coordinate[0]-5, coordinate[1]-5, coordinate[0]+5, coordinate[1]+5], fill='red')

def draw_kills_boxes(image, coordinates):
    draw = ImageDraw.Draw(image)
    # draw.rectangle(coordinates['governor_id'], fill=None, outline='red')
    # draw.rectangle(coordinates['mail'], fill=None, outline='red')
    draw.rectangle(coordinates['t1_kills'], fill=None, outline='red')
    draw.rectangle(coordinates['t2_kills'], fill=None, outline='red')
    draw.rectangle(coordinates['t3_kills'], fill=None, outline='red')
    draw.rectangle(coordinates['t4_kills'], fill=None, outline='red')
    draw.rectangle(coordinates['t5_kills'], fill=None, outline='red')
    draw.rectangle(coordinates['total_kill_points'], fill=None, outline='red')
    # draw_circle(draw, coordinates['name'])
    # draw_circle(draw, coordinates['expand_kill_points'])
    # draw_circle(draw, coordinates['more_info'])
    # draw_circle(draw, coordinates['close_profile'])
    image.show()

def get_kill_box(im):
    bw = common.ocr.get_black_and_white(im, 240).convert('RGB')
    bbox = bw.getbbox()
    bw = bw.crop(bbox)
    draw = ImageDraw.Draw(bw)
    w, h = bw.size
    top = h - 15
    left = w - 15
    while bw.getpixel((w - 15, top)) == (255, 255, 255):
        top -= 1
    while bw.getpixel((left, h - 15)) == (255, 255, 255):
        left -= 1
    box_bottom = h - 15
    while bw.getpixel((w-30, box_bottom)) == (255, 255, 255):
        box_bottom -= 1
    kill_bbox = (bbox[2] - (w - left) + 1, bbox[3] - (h - top) + 1, bbox[2], bbox[3])
    return im.crop(kill_bbox), box_bottom - top + 1

def parse_kill_image(image, coordinates):
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

def get_scaled_coordinates(hk, vk):
    coordinates = reference_coordinates.copy()
    for key in coordinates:
        coordinates[key] = (coordinates[key][0]*hk, coordinates[key][1]*vk, coordinates[key][2]*hk, coordinates[key][3]*vk)
    return coordinates

def main():
    # with Image.open('samples/a_profile_kills.png') as im:
    #     kill_box, box_bottom = get_kill_box(im)
    #     print(kill_box.size, box_bottom)
    #     draw_kills_boxes(kill_box, reference_coordinates)
    #     w, h = kill_box.size
    #     print(kill_box.getpixel((w-50, h-1)))
    #
    # with Image.open('kills_to_fix/9573565_kills.png') as im:
    #     kill_box, box_bottom = get_kill_box(im)
    #     print(kill_box.size, box_bottom)
    #     w, h = kill_box.size
    #     coordinates = get_scaled_coordinates(w/800, box_bottom/537)
    #     draw_kills_boxes(kill_box, coordinates)
    #     print(parse_kill_image(kill_box, coordinates))
    # return
    engine = db.init_db(config.databases['rds'])
    with Session(engine) as session:
        kill_parse_errors = session.execute(
            select(models.Governor_Data)
                .where(models.Governor_Data.kill_parse_error == True)
                .order_by(models.Governor_Data.t1_kills)
        )
        for row in kill_parse_errors:
            print(row.Governor_Data.pull_id, row.Governor_Data.governor_id)
            print(row.Governor_Data.kill_points,
                  row.Governor_Data.t1_kills,
                  row.Governor_Data.t2_kills,
                  row.Governor_Data.t3_kills,
                  row.Governor_Data.t4_kills,
                  row.Governor_Data.t5_kills,
            )
            filepath = download_kills_image(row.Governor_Data.pull_id, row.Governor_Data.governor_id)
            with Image.open(filepath) as im:
                kill_box, box_bottom = get_kill_box(im)
                w, h = kill_box.size
                coordinates = get_scaled_coordinates(w/800, box_bottom/537)
                try:
                    results = parse_kill_image(kill_box, coordinates)
                except Exception:
                    # im.show()
                    continue
                # draw_kills_boxes(kill_box, coordinates)
            print(results)
            governor_data = row.Governor_Data
            governor_data.kill_points = results['kill_points']
            governor_data.t1_kills = results['t1_kills']
            governor_data.t2_kills = results['t2_kills']
            governor_data.t3_kills = results['t3_kills']
            governor_data.t4_kills = results['t4_kills']
            governor_data.t5_kills = results['t5_kills']
            governor_data.kill_parse_error = results['check_kills']
            session.merge(governor_data)
            session.commit()


    pass



if __name__ == '__main__':
    main()