from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from scripts.chroma_to_alpha import chroma_to_alpha


class ChromaToAlphaTest(unittest.TestCase):
    def test_green_edge_is_translucent_and_decontaminated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            output = root / "output.png"
            image = Image.new("RGB", (3, 1))
            image.putdata([(0, 255, 0), (50, 230, 10), (220, 150, 95)])
            image.save(source)

            chroma_to_alpha(source, output)
            pixels = list(Image.open(output).convert("RGBA").get_flattened_data())

            self.assertEqual(pixels[0][3], 0)
            self.assertLess(pixels[1][3], 100)
            self.assertGreater(pixels[1][3], 15)
            self.assertLess(pixels[1][1], 180)
            self.assertEqual(pixels[2][3], 255)

    def test_soft_green_fringe_is_not_left_mostly_opaque(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            output = root / "output.png"
            image = Image.new("RGB", (1, 1), (150, 220, 50))
            image.save(source)

            chroma_to_alpha(source, output)
            red, green, blue, alpha = Image.open(output).convert("RGBA").getpixel((0, 0))

            self.assertLess(alpha, 150)
            self.assertGreater(red, green)
            self.assertGreater(green, blue)

    def test_one_pixel_chroma_fringe_is_contracted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            output = root / "output.png"
            image = Image.new("RGB", (7, 7), (0, 255, 0))
            for y in range(1, 6):
                for x in range(1, 6):
                    image.putpixel((x, y), (150, 220, 50))
            for y in range(2, 5):
                for x in range(2, 5):
                    image.putpixel((x, y), (220, 150, 95))
            image.save(source)

            chroma_to_alpha(source, output)
            alpha = Image.open(output).convert("RGBA").getchannel("A")

            self.assertEqual(alpha.getpixel((1, 3)), 0)
            self.assertEqual(alpha.getpixel((3, 3)), 255)


if __name__ == "__main__":
    unittest.main(verbosity=2)
