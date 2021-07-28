import os
import pytest
from pathlib import Path

base = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def cwl_packed_workflow_path() -> Path:
    return Path(f'{base}/fixtures/cwl/simple_serial_packed.json')
