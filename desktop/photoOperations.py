# 1. parallel upload ve parallel delete
# 2. şablon getirmede lazy loading
# 3. yükleme işleminde file dialoga tekrar gidilince ekran yenilemesini yap
# 4. müşteri seçimlerini silme işlemi ekle
# 5. uygulalmanın patlaması halinde nasıl bir yol izlenecek?
# 7. ortak bir log mekanizması ekle. db üzerinde tutulsun üzerine ekle.işlemlerin aldığı süresiyi de logda tut
# 8. bütün kodu refactor. okuma, anlama ve bakımı kolaylaştır

from PIL import Image
from io import BytesIO

class PhotoOperations(object):
    def __init__(self):
        super().__init__()

    # resizing without cropping
    def resize_original_image(self, path):
        img = Image.open(path)
        
        w, h = img.size
        width = int(w*0.25)
        height = int(h*0.25)

        img = img.resize((width, height), Image.LANCZOS)
        img = self.ensure_rgb(img=img)

        buf = BytesIO()
        img.save(buf, format="JPEG", quality=100, optimize=True)
        return buf.getvalue()

    def resize_thumb_image(self, path):
        w, h = img.size
        width = int(w*0.6)
        height = int(h*0.6)

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
    def crop_center_square(self, img: Image.Image, width=200, height=200):
        w, h = img.size
        min_side = min(w, h)

        left = (w - min_side) // 2
        top = (h - min_side) // 2
        right = left + min_side
        bottom = top + min_side

        img = img.crop((left, top, right, bottom))
        return img.resize((width, height), Image.LANCZOS)