
import pytest
from context import mbt
from mbt.directory_context import DirectoryContext
from mbt.mbt_configurator import MbtConfigurator

assert mbt


def test_config():
    conf = MbtConfigurator()
    conf.add_series("5.5")
    conf.add_series("5.7")
    conf.add_build_config("bar-a", "image")
    return conf


def test_incorrect_directory():
    with pytest.raises(mbt.MbtError):
        DirectoryContext(test_config(), "/foo/bar", "/foo/barbar/bar")


def test_in_root():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo/topi/whatever/foo/bar")
    assert dc.topic is None
    assert dc.series is None
    assert dc.variant is None
    assert dc.installation is None


def test_in_topic():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo/topics/whatever/foo/bar")
    assert dc.topic == "whatever"
    assert dc.series is None
    assert dc.variant is None
    assert dc.installation is None


def test_in_series():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo/topics/whatever/5.7/bar")
    assert dc.topic == "whatever"
    assert dc.series == "5.7"
    assert dc.variant is None
    assert dc.installation is None


def test_in_variant():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo/topics/whatever/5.7-bar-a")
    assert dc.topic == "whatever"
    assert dc.series == "5.7"
    assert dc.variant == "bar-a"
    assert dc.installation is None


def test_invalid_variant():
    with pytest.raises(mbt.MbtError):
        DirectoryContext(test_config(),
                         "/foo", "/foo/topics/whatever/5.7-bar")


def test_in_installation():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo/topics/whatever/5.7-bar-a-inst-wh-at")
    assert dc.topic == "whatever"
    assert dc.series == "5.7"
    assert dc.variant == "bar-a"
    assert dc.installation == "wh-at"
