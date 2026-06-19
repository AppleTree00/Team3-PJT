from PIL import Image, ImageDraw
import os

# Create OG image (1200x630)
width, height = 1200, 630
img = Image.new('RGB', (width, height), color='#f9f9ff')
draw = ImageDraw.Draw(img)

# Draw gradient background
for y in range(height):
    ratio = y / height
    r = int(249 - (249 - 77) * ratio)
    g = int(249 - (249 - 68) * ratio)
    b = int(255 - (255 - 227) * ratio)
    draw.line([(0, y), (width, y)], fill=(r, g, b))

# Add circles
draw.ellipse([(80, 100), (280, 300)], fill=(255, 255, 255), outline='#c3c0ff', width=3)
draw.ellipse([(920, 200), (1100, 380)], fill=(255, 255, 255), outline='#4d44e3', width=2)
draw.ellipse([(500, 50), (700, 250)], fill=(255, 255, 255), outline='#6bd8cb', width=2)

# Save
os.makedirs('static', exist_ok=True)
img.save('static/og-image.png')
print('OG image created')
