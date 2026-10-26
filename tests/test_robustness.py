import csv
import tempfile
import unittest
from pathlib import Path
import torch
from PIL import Image, ImageDraw
from docguard.baseline import Documents
from docguard.robustness import CONDITIONS, degrade


class RobustnessChecks(unittest.TestCase):
    def test_conditions_are_deterministic_and_preserve_geometry(self):
        image = Image.new('RGB', (101, 137), 'white')
        ImageDraw.Draw(image).rectangle((30, 50, 60, 70), fill='black')
        for condition in CONDITIONS:
            first = degrade(image, condition)
            self.assertEqual(first.size, image.size)
            self.assertEqual(first.mode, 'RGB')
            self.assertEqual(first.tobytes(), degrade(image, condition).tobytes())
        self.assertEqual(degrade(image, 'clean').tobytes(), image.tobytes())
        self.assertNotEqual(degrade(image, 'resize25').tobytes(), image.tobytes())
        with self.assertRaises(ValueError):
            degrade(image, 'typo')

    def test_degradation_does_not_change_ground_truth(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            Image.new('RGB', (80, 100), 'white').save(root/'image.png')
            mask = Image.new('L', (80, 100), 0)
            ImageDraw.Draw(mask).rectangle((30, 40, 50, 60), fill=255)
            mask.save(root/'mask.png')
            with (root/'manifest.csv').open('w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['image', 'mask', 'split'])
                writer.writeheader()
                writer.writerow(dict(image='image.png', mask='mask.png', split='test'))
            original = Documents(root, 'test', 50, 40)[0][1]
            for condition in CONDITIONS:
                transformed = Documents(root, 'test', 50, 40, image_transform=lambda im: degrade(im, condition))
                self.assertTrue(torch.equal(original, transformed[0][1]))
