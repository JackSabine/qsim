from enum import Enum

class TestResult(Enum):
    PASS = 0
    FAIL = 1
    TIMEOUT = 2

class RegressionResult(Enum):
    PASS = 0
    FAIL = 1