# 2. uygulalmanın patlaması halinde nasıl bir yol izlenecek? işlemlerin yarım kalmaması 
# veya yapılan işlemin kökten iptali ile tersine dönderilmesi gerek.
# 6. web tarafına bir güvenlik koy url olan herkes gidemesin veya url de token olanlar gidebilsin
# 7. bütün kodu refactor. okuma, anlama ve bakımı kolaylaştır
# # 8. ortak bir log mekanizması ekle. db üzerinde tutulsun üzerine ekle.işlemlerin aldığı süresiyi de logda tut

from PIL import Image
from io import BytesIO

class PhotoOperations(object):
    def __init__(self):
        super().__init__()

    def resize_image(self, path, wC=0.25, hC=0.25):
        img = Image.open(path)
        
        w, h = img.size
        width = int(w*wC)
        height = int(h*hC)

        img = img.resize((width, height), Image.LANCZOS)
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