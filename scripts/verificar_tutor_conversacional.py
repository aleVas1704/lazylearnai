"""Regresión offline, sin Neon ni llamadas reales a Gemini."""

import unittest

if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover("tests"))
    raise SystemExit(not result.wasSuccessful())
