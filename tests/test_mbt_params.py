
import pytest
from context import mbt
from mbt.directory_context import DirectoryContext
from mbt.mbt_configurator import MbtConfigurator
from mbt.mbt_params import MbtParams

assert mbt


def test_config():
    conf = MbtConfigurator()
    conf.add_series("5.5")
    conf.add_series("5.7")
    conf.add_build_config("some-build", "image")
    return conf


def test_topic():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo/topics/whatever")
    params = MbtParams(test_config(), dc)
    params.add_topic_arg()
    assert params.parse([]).topic == "whatever"


def test_required_topic_error():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo")
    params = MbtParams(test_config(), dc)
    params.add_topic_arg()
    with pytest.raises(SystemExit):
        params.parse([])


def test_required_topic_short_succeeds():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo")
    params = MbtParams(test_config(), dc)
    params.add_topic_arg()
    assert params.parse(["-t", "whatever"]).topic == "whatever"


def test_required_topic_long_succeeds():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo")
    params = MbtParams(test_config(), dc)
    params.add_topic_arg()
    assert params.parse(["--topic", "whatever"]).topic == "whatever"


def test_series():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo/topics/whatever/5.7")
    params = MbtParams(test_config(), dc)
    params.add_series_arg()
    assert params.parse([]).series == "5.7"


def test_required_series_error():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo")
    params = MbtParams(test_config(), dc)
    params.add_series_arg()
    with pytest.raises(SystemExit):
        params.parse([])


def test_required_series_short_incorrect():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo")
    params = MbtParams(test_config(), dc)
    params.add_series_arg()
    with pytest.raises(SystemExit):
        params.parse(["-s", "whatever"])


def test_required_series_short_succeeds():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo")
    params = MbtParams(test_config(), dc)
    params.add_series_arg()
    assert params.parse(["-s", "5.7"]).series == "5.7"


def test_required_series_long_succeeds():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo")
    params = MbtParams(test_config(), dc)
    params.add_series_arg()
    assert params.parse(["--series", "5.7"]).series == "5.7"


def test_variant():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo/topics/whatever/5.7-some-build")
    params = MbtParams(test_config(), dc)
    params.add_variant_arg()
    assert params.parse([]).variant == "some-build"


def test_required_variant_error():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo")
    params = MbtParams(test_config(), dc)
    params.add_variant_arg()
    with pytest.raises(SystemExit):
        params.parse([])


def test_required_variant_short_invalid():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo")
    params = MbtParams(test_config(), dc)
    params.add_variant_arg()
    with pytest.raises(SystemExit):
        params.parse(["-v", "some"])


def test_required_variant_short_succeeds():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo")
    params = MbtParams(test_config(), dc)
    params.add_variant_arg()
    assert params.parse(["-v", "some-build"]).variant == "some-build"


def test_required_variant_long_succeeds():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo")
    params = MbtParams(test_config(), dc)
    params.add_variant_arg()
    assert params.parse(["--variant", "some-build"]).variant == "some-build"


def test_installation():
    dc = DirectoryContext(test_config(),
                          "/foo",
                          "/foo/topics/whatever/5.7-some-build-inst-some")
    params = MbtParams(test_config(), dc)
    params.add_installation_arg()
    assert params.parse([]).installation == "some"


def test_required_installation_error():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo/topics/whatever/5.7-some-build")
    params = MbtParams(test_config(), dc)
    params.add_installation_arg()
    with pytest.raises(SystemExit):
        params.parse([])


def test_installation_implies_everything_else():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo")
    params = MbtParams(test_config(), dc)
    params.add_installation_arg()
    with pytest.raises(SystemExit):
        params.parse(["-i", "some-tag"])


def test_required_installation_short_succeeds():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo/topics/whatever/5.7-some-build")
    params = MbtParams(test_config(), dc)
    params.add_installation_arg()
    assert params.parse(["-i", "some-tag"]).installation == "some-tag"


def test_required_installation_long_succeeds():
    dc = DirectoryContext(test_config(),
                          "/foo", "/foo/topics/whatever/5.7-some-build")
    params = MbtParams(test_config(), dc)
    params.add_installation_arg()
    assert params.parse(["--installation", "some"]).installation == "some"
