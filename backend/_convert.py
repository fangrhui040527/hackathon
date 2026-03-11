from PIL import Image
import os
img = Image.open("image/40214206-2_1-kelloggs-original-potato-crisps.webp")
img.convert("RGB").save("image/test_kelloggs.jpg", "JPEG", quality=95)
print(f"Saved as JPEG: {os.path.getsize('image/test_kelloggs.jpg')} bytes")
