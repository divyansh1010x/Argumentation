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


# ------------------------------------------------------------ extra figures
import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

from argengine import examples as ex  # noqa: E402
from argengine.semantics import complete_extensions, grounded_trace  # noqa: E402
from argengine.viz import (_fmt_set, draw_best_response_table, draw_extension_lattice,  # noqa: E402
                           draw_grounded_trace)

ALL_FRAMEWORKS = {**ex.BOOK_FRAMEWORKS, **ex.EXTRA_FRAMEWORKS}


@pytest.mark.parametrize("title", list(ALL_FRAMEWORKS))
def test_grounded_trace_panels(title):
    af = ALL_FRAMEWORKS[title]()
    distinct = len(set(grounded_trace(af)) | {frozenset()})
    fig = draw_grounded_trace(af)
    assert len(fig.axes) == distinct  # F^0 = ∅ plus one panel per new set
    plt.close(fig)


@pytest.mark.parametrize("title", list(ALL_FRAMEWORKS))
def test_lattice_nodes_are_complete_extensions(title):
    af = ALL_FRAMEWORKS[title]()
    ax = draw_extension_lattice(af)
    labels = sorted(t.get_text().split("\n")[0] for t in ax.texts)
    assert labels == sorted(_fmt_set(af, e) for e in complete_extensions(af))
    plt.close(ax.figure)


def test_best_response_table_example_5_10():
    m = ex.example_5_10()
    ax = draw_best_response_table(m, 0)
    tab = ax.tables[0]
    n_rows = max(r for r, _ in tab.get_celld()) + 1
    assert n_rows == 1 + 2 ** len(m.types[0])  # header + every A°x ⊆ Ax
    starred = [tab[r, 0].get_text().get_text() for r in range(1, n_rows) if "best" in tab[r, 5].get_text().get_text()]
    assert starred == ["{α1}"]  # hiding α1 is x's unique best response (book Ex. 5.10)
    plt.close(ax.figure)
