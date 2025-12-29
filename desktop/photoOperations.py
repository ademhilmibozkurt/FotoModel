# 1. c: diskine uygulama hafızası tut
# 2. fotoğrafları buraya ve veri tabanına yükle
# 3. link oluşturma tabi yaz
# 4. app de bir section ile bu fotoları göster lokalden göster
# 5. app e eklenecek alan ile veri tabanına ve lokale seçilen fotoları yükle.
# 6. formda bu fotoları göster veri tabanından

from PIL import Image
from io import BytesIO

class PhotoOperations(object):
    def __init__(self):
        super().__init__()

    def resize_image(self, path, width, height):
        img = Image.open(path)
        img = self.crop_center_square(img, width=width, height=height)
        img = self.ensure_rgb(img=img)

        buf = BytesIO()
        img.save(buf, format="JPEG", quality=100, optimize=True)
        return buf.getvalue()

    def ensure_rgb(self, img: Image.Image, bg_color=(255, 255, 255)):
        if img.mode in ("RGBA", "LA"):
            background = Image.new("RGB", img.size, bg_color)
            background.paste(img, mask=img.split()[-1])
            return background
        return img.convert("RGB")

    # cropping image
    def crop_center_square(self, img: Image.Image, width=200, height=150):
        w, h = img.size
        min_side = min(w, h)

        left = (w - min_side) // 2
        top = (h - min_side) // 2
        right = left + min_side
        bottom = top + min_side

        img = img.crop((left, top, right, bottom))
        return img.resize((width, height), Image.LANCZOS)