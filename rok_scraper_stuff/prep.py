import os
import glob

# for i in range(2001, 2041):
#     os.mkdir(os.path.join(r'E:\RoK\2020_KvK3', str(i)))

for folder_path in glob.glob(r'E:\RoK\2402_KvK3\*'):
    os.mkdir(os.path.join(folder_path, '2022-03-13'))