from PIL import Image, ImageDraw

# Create icon
img = Image.new('RGB', (256, 256), color='#0f172a')
draw = ImageDraw.Draw(img)

# Draw shield
draw.polygon([(128,30), (210,70), (210,180), (128,220), (46,180), (46,70)], 
             fill='#3b82f6')
draw.text((95, 100), 'FG', fill='white')
img.save('icon.ico')