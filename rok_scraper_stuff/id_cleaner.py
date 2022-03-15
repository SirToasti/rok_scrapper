import os
import csv
import glob


def main(kingdom, kvk, date):
    base_path = r'E:\Rok\{}_{}\contribution\screenshots\{}'.format(kingdom, kvk, date)
    with open(r'E:\Rok\{}_{}\contribution\screenshots\id_parse_map.csv'.format(kingdom, kvk), 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            for filepath in iter(glob.glob(base_path + r'\{}_*.*'.format(row['ocr_hashed_id']))):
                new_filepath = filepath.replace(row['ocr_hashed_id'], row['actual_id'])
                os.rename(filepath, new_filepath)



if __name__ == "__main__":
    main('2020', 'KvK5', '2021-11-01')