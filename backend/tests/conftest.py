import os, tempfile
os.environ["FW_DATA_DIR"] = tempfile.mkdtemp()
os.environ["FW_FIXTURE"] = "1"
import pytest
from fw import data


@pytest.fixture(autouse=True, scope="session")
def _load():
    data.load(force_fixture=True)
