
import pytest

from context import mbt
from mbt.mbt_root import MbtRoot
from os import getcwd
from os.path import join

assert mbt


def test_with_real_file():
    root = MbtRoot("tests/assets")
    assert root.root_dir().endswith("tests/assets")
    assert root.config_file().endswith("tests/assets/mbt_config.py")


def test_with_real_file_without_parameter(mocker):
    fake_workdir = join(getcwd(), "tests", "assets")
    mocker.patch("mbt.mbt_root.getcwd", return_value=fake_workdir)

    root = MbtRoot()
    assert root.root_dir().endswith("tests/assets")
    assert root.config_file().endswith("tests/assets/mbt_config.py")


def test_no_config_file(mocker):
    mocker.patch("mbt.mbt_root.isfile", return_value=False)

    with pytest.raises(IOError):
        MbtRoot()
