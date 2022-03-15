from PIL import Image
from PIL import ImageOps

def get_black_and_white(image, thresh=120):
    fn = lambda  x : 255 if x > thresh else 0
    return image.convert('L').point(fn, mode='1').convert('RGB')

image = Image.open(r'assets\rss\crystal.png')
print(image.size)
image = image.crop((900, 400, 1100, 600))
image.show()

bw = get_black_and_white(image, thresh=210)

width, height = image.size
left, top, right, bottom = bw.getbbox()
new_width = right - left
new_height = bottom - top
new_width = max(new_height, new_width)
new_height = max(new_height, new_width)

center_x = (left + right)/2
center_y = (top + bottom)/2
left = center_x - new_width/2
right = center_x + new_width/2
top = center_y - new_height/2
bottom = center_y + new_height/2
mini = image.crop((max(left - 5, 0), max(top - 5, 0), min(right + 5, width), min(bottom + 5, height)))
mini.show()
mini.save(r'assets\rss\crystal_mini.png')