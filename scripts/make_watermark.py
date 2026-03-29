from PIL import Image, ImageDraw, ImageFont
import os

img = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
try:
    fnt = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 50)
except Exception as e:
    fnt = ImageFont.load_default()

text = "PhatDaPhoTe.com"
bbox = d.textbbox((0,0), text, font=fnt)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]

x = (1080 - tw) / 2
y = 1920 - 100 - th

# white with 0.8 alpha (204)
d.text((x, y), text, font=fnt, fill=(255, 255, 255, 204))
img.save('watermark.png')
print("Watermark created!")
