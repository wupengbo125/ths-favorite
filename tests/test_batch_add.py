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


class TestReadCodesCsv(unittest.TestCase):
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="ts_code,name\n600519.SH,贵州茅台\n000001.SZ,平安银行\n833454,某北交所\n",
    )
    def test_reads_ts_code_column(self, mock_file):
        self.assertEqual(
            batch_add._read_codes_from_csv("any.csv"),
            ["600519.SH", "000001.SZ", "833454"],
        )

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="name,stock_code\nfoo,600519\nbar,\nbaz,000001\n",
    )
    def test_reads_stock_code_column_and_skips_empty_cells(self, mock_file):
        self.assertEqual(
            batch_add._read_codes_from_csv("any.csv"),
            ["600519", "000001"],
        )

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="ts_code,stock_code\n600519.SH,600519\n",
    )
    def test_errors_when_both_columns_present(self, mock_file):
        with self.assertRaises(ValueError) as ctx:
            batch_add._read_codes_from_csv("any.csv")
        self.assertIn("同时存在", str(ctx.exception))

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="name,price\nfoo,1.23\n",
    )
    def test_errors_when_neither_column_present(self, mock_file):
        with self.assertRaises(ValueError) as ctx:
            batch_add._read_codes_from_csv("any.csv")
        self.assertIn("缺少", str(ctx.exception))

    @patch("builtins.open", new_callable=mock_open, read_data="")
    def test_empty_file_returns_empty_list_without_error(self, mock_file):
        self.assertEqual(batch_add._read_codes_from_csv("any.csv"), [])

    @patch("builtins.open", new_callable=mock_open, read_data="ts_code\n")
    def test_header_only_returns_empty_list_without_error(self, mock_file):
        self.assertEqual(batch_add._read_codes_from_csv("any.csv"), [])


class TestBatchAddCsvFlow(unittest.TestCase):
    @patch("batch_add.PortfolioManager")
    @patch("os.path.isfile", return_value=True)
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="ts_code,name\n600519.SH,贵州茅台\n000001.SZ,平安银行\n",
    )
    def test_csv_input_drives_add_item_to_group(
        self, mock_file, mock_isfile, mock_manager_class
    ):
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        test_args = ["batch_add.py", "我的分组.csv", "--workers", "1"]
        with patch.object(sys, "argv", test_args):
            with patch("builtins.print"):
                batch_add.main()

        calls = mock_manager.add_item_to_group.call_args_list
        self.assertEqual(len(calls), 2)
        # 倒序:000001.SZ 先,600519.SH 后
        self.assertEqual(calls[0].args, ("我的分组", "000001.SZ"))
        self.assertEqual(calls[1].args, ("我的分组", "600519.SH"))

    @patch("batch_add.PortfolioManager")
    @patch("os.path.isfile", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="")
    def test_empty_csv_skips_upload_silently(
        self, mock_file, mock_isfile, mock_manager_class
    ):
        test_args = ["batch_add.py", "空文件.csv"]
        with patch.object(sys, "argv", test_args):
            with patch("builtins.print"):
                batch_add.main()

        # 空文件:连 PortfolioManager 都不应该被构造,更不应该上传
        mock_manager_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()
