# tests/test_test_best.py

import pytest
from io import StringIO
from unittest.mock import patch

from src.models.test_best import Checker


class TestChecker:

    def test_check_pass_does_not_increment_failures(self, capsys):
        c = Checker()
        c.check(True, "some check")
        assert c.failures == 0

    def test_check_fail_increments_failures(self, capsys):
        c = Checker()
        c.check(False, "some check")
        assert c.failures == 1

    def test_check_multiple_failures_accumulate(self, capsys):
        c = Checker()
        c.check(False, "check 1")
        c.check(False, "check 2")
        c.check(True,  "check 3")
        assert c.failures == 2

    def test_check_pass_prints_pass(self, capsys):
        c = Checker()
        c.check(True, "my label")
        assert "[PASS]" in capsys.readouterr().out

    def test_check_fail_prints_fail(self, capsys):
        c = Checker()
        c.check(False, "my label")
        assert "[FAIL]" in capsys.readouterr().out

    def test_check_prints_label(self, capsys):
        c = Checker()
        c.check(True, "my label")
        assert "my label" in capsys.readouterr().out

    def test_check_prints_detail_when_provided(self, capsys):
        c = Checker()
        c.check(False, "my label", "some detail")
        assert "some detail" in capsys.readouterr().out

    def test_check_no_detail_when_empty(self, capsys):
        c = Checker()
        c.check(True, "my label", "")
        assert "()" not in capsys.readouterr().out

    def test_check_returns_true(self):
        c = Checker()
        assert c.check(True, "label") is True

    def test_check_returns_false(self):
        c = Checker()
        assert c.check(False, "label") is False

    def test_info_prints_info_tag(self, capsys):
        Checker.info("some info")
        assert "[INFO]" in capsys.readouterr().out

    def test_info_prints_label(self, capsys):
        Checker.info("my info label")
        assert "my info label" in capsys.readouterr().out

    def test_initial_failures_zero(self):
        c = Checker()
        assert c.failures == 0