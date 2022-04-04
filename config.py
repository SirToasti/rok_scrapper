emulators = {
    'lasfdjfd-dev-0': {
        'type': 'bluestacks',
        'name': 'lasfdjfd-dev-0',
        'address': '127.0.0.1:5576'
    },
    'lasfdjfd-dev-1': {
        'type': 'bluestacks',
        'name': 'lasfdjfd-dev-1',
        'address': '127.0.0.1:5645'
    },
    'lasfdjfd-dev-3': {
        'type': 'bluestacks',
        'name': 'lasfdjfd-dev-3',
        'address': '127.0.0.1:5665'
    },
    'lasfdjfd-dev-4': {
        'type': 'bluestacks',
        'name': 'lasfdjfd-dev-4',
        'address': '127.0.0.1:5675'
    },
    'genymotion-2402':{
        'type': 'genymotion',
        'name': 'i-0fe13b13f22bd209e',
        'address': '172.31.56.199:5555',
    },
    'genymotion-2402-lk':{
        'type': 'genymotion',
        'name': 'i-013e97ad5e051c647',
        'address': '172.31.62.3:5555',
    }
}

coordinates = {
    '1920x1080': {
        'own_profile': (75,60),
        'rankings': (665, 790),
        'individual_power': (465, 615),
        'close_big_window': (1675, 65),
        'settings': (1470, 800),
        'search_governor': (1390, 280),
        'search_bar': (550, 165),
        'search_button': (1600, 165),
        'view_profile': (1485, 910),
        'row_1': (960, 328),
        'row_2': (960, 450),
        'row_3': (960, 572),
        'row_4': (960, 694),
        'row_5': (960, 816),
        'row_6': (960, 938),
        'governor_id': (892, 284, 1200, 320),
        'name': (840, 340),
        'more_info': (470, 800),
        'expand_kill_points': (1342, 421),
        'close_profile': (1637, 125),
        'close_more_info': (1675, 65),
        'mail': (1235, 875, 1300, 905),
        'power': (980, 170, 1200, 205),
        'total_kill_points': (1113, 476, 1350, 507),
        't1_kills': (1040, 725, 1250, 755),
        't2_kills': (1040, 775, 1250, 805),
        't3_kills': (1040, 830, 1250, 860),
        't4_kills': (1040, 880, 1250, 910),
        't5_kills': (1040, 935, 1250, 965),
        'deads': (1330, 535, 1580, 585),
        'rss_gathered': (1330, 740, 1580, 790),
        'rss_assistance': (1330, 810, 1580, 860),
        'helps': (1330, 885, 1580, 935),

    }
}

databases = {
    "rds": {
        "username": "rok_scraper",
        "host": "rok-scraper-dev-free.cnnvfpj4dpp0.us-west-2.rds.amazonaws.com",
        "port": 5432,
        "database": "rok_scraper_test",
        "password_parameter_name": "rok_scraper_db_password"
    }
}