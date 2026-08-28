from __future__ import annotations

import pytest


class RegressionTestSuite:
    pytestmark = pytest.mark.regression


class SmokeTestSuite:
    pytestmark = pytest.mark.smoke


class UnitTestSuite:
    pytestmark = pytest.mark.unit


class AdapterTestSuite:
    pytestmark = pytest.mark.vendor_contract


class BrowserTestSuite:
    pytestmark = pytest.mark.browser
