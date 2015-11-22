from __future__ import print_function, division, absolute_import
import unittest
import random

import dotdot
import experiments.provenance


random.seed(0)


class TestProvenance(unittest.TestCase):

    def test_modules_provenance(self):
        mod_names = ['explorers', 'environments', 'learners', 'scicfg', 'scipy', 'numpy']
        cfg = experiments.provenance.modules_provenance(mod_names)
        self.assertEqual(set([name for name, _ in cfg._branches]), set(mod_names))

        cfg.explorers.dirty = True
        with self.assertRaises(ValueError):
            experiments.provenance.check_dirty(cfg)

if __name__ == '__main__':
    unittest.main()
