import io

import numpy as np
from PIL import Image  # type: ignore # noqa


class Screen:
    def __init__(self) -> None:
        self.img_size = (320, 200)

        self.f_scr = io.BytesIO()
        self.f_pal = io.BytesIO()

        (img_w, img_h) = self.img_size
        self.scr_size = (img_w * 2, img_h * 2)

    def update_screen(self):
        if len(self.f_pal.getbuffer()) != 3 * 256 or len(self.f_scr.getbuffer()) != 320 * 200:
            return
        scr = np.frombuffer(self.f_scr.getbuffer(), dtype=np.uint8)
        pal = np.frombuffer(self.f_pal.getbuffer(), dtype=np.uint8).reshape((256, 3))

        arr = pal[scr]

        data = arr.astype(np.uint8).tobytes()

        img = Image.frombytes("RGB", self.img_size, data)
        img.save("output.png")
