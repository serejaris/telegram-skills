import importlib.util
import os
import pathlib

path = pathlib.Path(__file__).parents[1] / "scripts" / "widget_tool.py"
spec = importlib.util.spec_from_file_location("widget_tool", path)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def test_small_widget_is_ok():
    assert tool.measure(b"<p>hello</p>")["verdict"] == "ok"


def test_incompressible_html_is_too_large():
    assert tool.measure(os.urandom(5000))["verdict"] == "too_large"


def test_over_html_limit_is_too_large_even_if_it_compresses():
    assert tool.measure(b"a" * 40000)["verdict"] == "too_large"


def test_examples_fit():
    for example in (path.parents[1] / "examples").glob("*.html"):
        assert tool.measure(example.read_bytes())["verdict"] != "too_large", example
