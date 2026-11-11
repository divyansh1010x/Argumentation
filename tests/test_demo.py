import json

import matplotlib

matplotlib.use("Agg")

from argengine import demo  # noqa: E402
from argengine.io import load, parse_apx, save, to_apx  # noqa: E402
from argengine.examples import figure_5_3  # noqa: E402


def test_demo_runs(tmp_path, capsys):
    demo.main(["--figures", str(tmp_path)])
    out = capsys.readouterr().out
    assert "Example 5.10" in out and "TRUTHFUL IS NOT BEST" in out
    assert list(tmp_path.glob("*.png"))


def test_io_roundtrip(tmp_path):
    af = figure_5_3()
    assert parse_apx(to_apx(af)) == af
    save(af, tmp_path / "f.json", types=[{"a", "b"}, {"c"}, {"d", "e"}])
    af2, types = load(tmp_path / "f.json")
    assert af2 == af and types == [{"a", "b"}, {"c"}, {"d", "e"}]
    demo.main(["--file", str(tmp_path / "f.json")])
