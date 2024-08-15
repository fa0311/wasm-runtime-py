import io
import os
import sys

import numpy as np
import pygame  # type: ignore # noqa


class Screen:
    def __init__(self) -> None:
        os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "true"
        self.img_size = (320, 200)

        self.f_scr = io.BytesIO()
        self.f_pal = io.BytesIO()

        (img_w, img_h) = self.img_size
        self.scr_size = (img_w * 2, img_h * 2)
        pygame.init()
        self.surface = pygame.display.set_mode(self.scr_size)
        pygame.display.set_caption("DOOM")
        self.clock = pygame.time.Clock()

    def update_screen(self):
        for event in pygame.event.get():
            quit_key = event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            if event.type == pygame.QUIT or quit_key:
                pygame.quit()
                sys.exit()

        if len(self.f_pal.getbuffer()) != 3 * 256 or len(self.f_scr.getbuffer()) != 320 * 200:
            return

        scr = np.frombuffer(self.f_scr.getbuffer(), dtype=np.uint8)
        pal = np.frombuffer(self.f_pal.getbuffer(), dtype=np.uint8).reshape((256, 3))

        # Convert indexed color to RGB
        arr = pal[scr]

        data = arr.astype(np.uint8).tobytes()

        img = pygame.image.frombuffer(data, self.img_size, "RGB")

        img_scaled = pygame.transform.scale(img, self.scr_size)
        self.surface.blit(img_scaled, (0, 0))
        pygame.display.flip()

        self.clock.tick(60)
