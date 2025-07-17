from enum import Enum
from dataclasses import dataclass

class TestResultCode(Enum):
    PASS = 0
    FAIL = 1
    TIMEOUT = 2

class RegressionResult(Enum):
    PASS = 0
    FAIL = 1

@dataclass
class TestResult:
    code: TestResultCode
    testname: str
