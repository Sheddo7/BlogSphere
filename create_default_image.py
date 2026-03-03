# create_default_image.py
from PIL import Image, ImageDraw, ImageFont
import os

# Create the image
img = Image.new('RGB', (800, 600), color='#2c3e50')
draw = ImageDraw.Draw(img)

# Add text
try:
    font = ImageFont.truetype("arial.ttf", 40)
except:
    font = ImageFont.load_default()

text = "BlogSphere"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (800 - text_width) / 2
y = (600 - text_height) / 2
draw.text((x, y), text, fill='#ecf0f1', font=font)

# Save the image
os.makedirs("media/blog_images", exist_ok=True)
img.save("media/blog_images/default.jpg")
print("Default image created at media/blog_images/default.jpg")