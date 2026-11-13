"""Regressions for clipped legs, small shoes and missing transition frames."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import png
from build_sheet import prepare_cell
from layout import CELLS, DECOR


class NaturalMotionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_width_fit_keeps_shoe_width_without_stretching_leg(self):
        # A tall source should crop its upper leg, rather than shrink its shoe.
        rgba = png.blank(80, 400)
        for y in range(400):
            for x in range(40 if y < 360 else 0, 60 if y < 360 else 80):
                rgba[(y * 80 + x) * 4:(y * 80 + x) * 4 + 4] = bytes((70, 80, 90, 255))
        source = self.root / 'leg.png'
        png.write_png(str(source), 80, 400, rgba)
        cell = prepare_cell(source, 160, 256, 'none', 38, True, 2,
                            grounded=True, paw_fit='width')
        self.assertEqual(png.bottom_gap(cell, 160, 256), 2)
        self.assertGreater(sum(cell[(240 * 160 + x) * 4 + 3] > 12 for x in range(160)), 150)
        # The 20px-wide calf scales uniformly by 1.95 to 39px, never stretches.
        self.assertAlmostEqual(sum(cell[x * 4 + 3] > 12 for x in range(160)), 39, delta=2)

    def test_auto_background_preserves_white_tights_in_transparent_art(self):
        # With transparent margins only the white leg touches the sampled
        # border. Treating it as the background would erase the entire calf.
        pixels = png.blank(80, 128)
        for y in range(110):
            for x in range(34, 55):
                pixels[(y * 80 + x) * 4:(y * 80 + x) * 4 + 4] = bytes((255, 255, 255, 255))
        for y in range(100, 127):
            for x in range(80):
                pixels[(y * 80 + x) * 4:(y * 80 + x) * 4 + 4] = bytes((20, 20, 20, 255))
        source = self.root / 'tights.png'
        png.write_png(str(source), 80, 128, pixels)
        cell = prepare_cell(source, 160, 256, 'auto', 38, True, 2,
                            grounded=True, paw_fit='width')
        self.assertGreater(sum(cell[(y * 160 + x) * 4 + 3] > 12
                               for y in range(8, 64) for x in range(160)), 2000)

    def test_auto_background_still_removes_opaque_white_backdrop(self):
        pixels = bytearray(bytes((255, 255, 255, 255)) * (80 * 128))
        for y in range(128):
            for x in range(30, 50):
                pixels[(y * 80 + x) * 4:(y * 80 + x) * 4 + 4] = bytes((60, 70, 80, 255))
        source = self.root / 'opaque.png'
        png.write_png(str(source), 80, 128, pixels)
        cell = prepare_cell(source, 160, 256, 'auto', 38, True, 2)
        self.assertEqual(cell[3], 0)
        self.assertGreater(cell[(128 * 160 + 80) * 4 + 3], 240)

    def build(self, omit=None, motion='natural', tall_front=False):
        frames = self.root / 'frames'
        frames.mkdir()
        for i, name in enumerate(CELLS):
            if name == omit:
                continue
            w, h = (80, 128) if name.startswith(('front_', 'back_')) else (64, 64)
            if tall_front and name == 'front_0':
                h = 400
            pixels = png.blank(w, h)
            for y in range(h):
                if name.startswith(('front_', 'back_')):
                    left, right = (w // 2, w * 3 // 4) if y < h * 0.8 else (0, w)
                else:
                    # Rounded portrait silhouette, not an opaque background plate.
                    inset = int(abs(y - h / 2) / 3)
                    left, right = w // 4 + inset, w * 3 // 4 - inset
                for x in range(left, right):
                    pixels[(y * w + x) * 4:(y * w + x) * 4 + 4] = bytes((30 + i, 70, 120, 255))
            if tall_front and name == 'front_0':
                # Mark a visible knee high in a tall source. Width cropping
                # removes it; preserving the complete silhouette must keep it.
                for y in range(40, 56):
                    for x in range(40, 60):
                        pixels[(y * w + x) * 4:(y * w + x) * 4 + 4] = bytes((240, 20, 20, 255))
            png.write_png(str(frames / (name + '.png')), w, h, pixels)
        base = png.blank(1024, 1024)
        for x, y, w, h in DECOR.values():
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    base[(yy * 1024 + xx) * 4:(yy * 1024 + xx) * 4 + 4] = bytes((7, 8, 9, 255))
        png.write_png(str(self.root / 'base.png'), 1024, 1024, base)
        command = [sys.executable, '-B', str(ROOT / 'scripts/build_sheet.py'),
                   '--frames', str(frames), '--base', str(self.root / 'base.png'),
                   '--out', str(self.root / 'custom.png'), '--bg', 'none', '--motion', motion]
        return subprocess.run(command, capture_output=True, text=True), base

    def test_natural_mode_rejects_missing_transition_before_writing_output(self):
        result, _ = self.build(omit='front_1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('front_1', result.stdout + result.stderr)
        self.assertFalse((self.root / 'custom.png').exists())

    def test_natural_build_records_mode_and_preserves_ui(self):
        result, base = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((self.root / 'custom.report.json').read_text(encoding='utf-8'))
        self.assertEqual(report['options']['motion'], 'natural')
        self.assertEqual(report['options']['paw_fit'], 'contain')
        self.assertTrue(report['must_generate']['front_1'])
        self.assertTrue(report['must_generate']['front_2'])
        self.assertTrue(report['must_generate']['front_4'])
        w, h, sheet = png.read_png(str(self.root / 'custom.png'))
        for rect in DECOR.values():
            self.assertEqual(png.crop(sheet, w, h, *rect), png.crop(base, w, h, *rect))

    def test_classic_mode_keeps_existing_transition_fallback(self):
        result, _ = self.build(omit='front_1', motion='classic')
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((self.root / 'custom.report.json').read_text(encoding='utf-8'))
        self.assertEqual(report['options']['paw_fit'], 'contain')
        self.assertEqual(report['cells']['front_1']['status'], 'reused:front_0')

    def test_natural_default_preserves_knee_in_tall_source(self):
        result, _ = self.build(tall_front=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        w, h, sheet = png.read_png(str(self.root / 'custom.png'))
        cell = png.crop(sheet, w, h, *CELLS['front_0'])
        knee_pixels = sum(cell[i] > 200 and cell[i + 1] < 40 and cell[i + 3] > 200
                          for i in range(0, len(cell), 4))
        self.assertGreater(knee_pixels, 5, 'The compositor cropped the knee out')

    def test_natural_validation_does_not_demand_squashed_shoes(self):
        result, _ = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        check = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/validate.py'),
                                '--sheet', str(self.root / 'custom.png'),
                                '--base', str(self.root / 'base.png'),
                                '--report', str(self.root / 'custom.report.json')],
                               capture_output=True, text=True)
        self.assertIn('motion:natural', check.stdout)
        self.assertNotIn('pressure:front_5', check.stdout)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)


if __name__ == '__main__':
    unittest.main()
