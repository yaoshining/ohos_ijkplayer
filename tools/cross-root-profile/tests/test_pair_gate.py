import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
spec = importlib.util.spec_from_file_location('cross_root', Path(__file__).resolve().parents[1] / 'run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class PairGate(unittest.TestCase):
    def test_mismatched_pair_fails_without_building_fallback(self):
        compare = Mock(return_value={'allMatch':False})
        fallback = Mock(return_value='fixed')
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                runner.compare_chains('a', 'b', Path(tmp), compare, fallback)
            fallback.assert_not_called()
            compare.assert_called_once_with('a', 'b')
    def test_matching_pair_records_only_paired_success(self):
        compare = Mock(return_value={'allMatch':True})
        fallback = Mock()
        with tempfile.TemporaryDirectory() as tmp:
            result=runner.compare_chains('a', 'b', Path(tmp), compare, fallback)
            self.assertTrue(result['pairedAllMatch'])
            self.assertIsNone(result['fixedRootAllMatch'])
            fallback.assert_not_called()
