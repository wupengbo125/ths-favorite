import unittest
from unittest.mock import Mock, patch, mock_open
import sys
import os

# Ensure the parent directory is in the path so we can import batch_add
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import batch_add


class TestBatchAdd(unittest.TestCase):
    @patch("batch_add.PortfolioManager")
    @patch("os.path.isfile", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="600519\n000001\n833454\n")
    def test_batch_add_default_reverse(self, mock_file, mock_isfile, mock_manager_class):
        # Setup mocks
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        # Mock sys.argv to simulate calling with --workers 1
        test_args = ["batch_add.py", "dummy.txt", "--workers", "1"]
        with patch.object(sys, "argv", test_args):
            # Also mock print to avoid stdout noise during tests
            with patch("builtins.print"):
                batch_add.main()

        # Check that add_item_to_group was called with the reversed codes by default.
        # Original order: 600519, 000001, 833454
        # Reversed order: 833454, 000001, 600519
        calls = mock_manager.add_item_to_group.call_args_list
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0].args, ("dummy", "833454.BJ"))
        self.assertEqual(calls[1].args, ("dummy", "000001.SZ"))
        self.assertEqual(calls[2].args, ("dummy", "600519.SH"))


if __name__ == "__main__":
    unittest.main()
