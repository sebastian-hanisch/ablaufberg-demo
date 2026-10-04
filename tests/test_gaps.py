"""Gezielte Tests für Stellen, die der Fehler-Einbau-Test (tools/mutation_check.py) zuerst nicht fand: Zeilen und Lücke im Zugfolge-Bild, Diagramm-Werte, feste Achsen."""
import pytest

import abl_constants as C
import abl_model as M
import abl_results as R
import abl_visualization as V
from test_evaluation import STD
from test_results import RES

G = [0, 1, 0, 2, 1]


def test_train_rows_by_hand_for_the_sequential_plan():
    rows = V.train_rows(G, M.plan_sequential(G, 2, "num"), 2)
    assert rows == [("Eingang", [0, 1, 2, 3, 4], 0, None), ("nach Durchgang 1", [0, 2, 1, 3, 4], 2, 5), ("nach Durchgang 2", [0, 2, 1, 4, 3], 5, 3)]


def test_train_rows_of_radix_have_no_finished_cars_until_the_last_pass():
    rows = V.train_rows(G, M.plan_radix(G, 2), 2)
    assert [(r[2], r[3]) for r in rows] == [(0, None), (0, 5), (5, 5)] and rows[1][1] == [0, 2, 3, 1, 4] and rows[2][1] == [0, 2, 1, 4, 3]


def test_strips_have_one_trace_per_group_and_a_gap_behind_finished_cars():
    fig = V.build_train_strips(G, M.plan_sequential(G, 2, "num"), 2)
    assert [t.name for t in fig.data] == ["Gruppe 1", "Gruppe 2", "Gruppe 3"]
    g1 = fig.data[1]                                                              # Gruppe 2 (Nummer 1): Wagen 2 (Index 1) und 5 (Index 4)
    pts = sorted(zip(g1.y, g1.x))
    assert pts == [(0, 1), (0, 4), (1, 3.5), (1, 5.5), (2, 2), (2, 3)]            # Eingang ohne Lücke; nach Durchgang 1: 2 fertige Wagen, dann Lücke 1.5; nach Durchgang 2 alles fertig, keine Lücke
    texts = [a.text for a in fig.layout.annotations]
    assert texts == ["5 bewegt", "3 bewegt"]


def test_strips_of_a_grouped_train_show_only_the_input_row():
    fig = V.build_train_strips([0, 0, 1], [], 2)
    assert len(fig.layout.annotations) == 0 and sorted(set(fig.data[0].y)) == [0]


def test_strip_marker_colors_follow_the_group_number():
    fig = V.build_train_strips(G, M.plan_radix(G, 2), 2)
    assert [t.marker.color for t in fig.data] == [C.GROUP_COLORS[0], C.GROUP_COLORS[1], C.GROUP_COLORS[2]]


def test_time_bars_split_the_time_into_setup_and_pushing():
    fig = V.build_time_bars(STD, 20)
    assert [t.name for t in fig.data] == ["Aufwand der Durchgänge", "Abdrücken der Wagen"]
    assert list(fig.data[0].y) == [3 * 20, 3 * 20, 2 * 20] and list(fig.data[1].y) == [72 * 0.5, 64 * 0.5, 80 * 0.5]
    assert fig.layout.barmode == "stack"


def test_setup_lines_are_the_bergzeit_per_setup_with_a_marker_at_the_setting():
    fig = V.build_setup_lines(STD, 25)
    assert len(fig.data) == 3 and list(fig.data[0].x) == list(range(0, 61, 5))
    radix = next(t for t in fig.data if t.name == C.METHOD_LABELS["radix"])
    assert list(radix.y) == [2 * s + 40 for s in range(0, 61, 5)]
    assert fig.layout.shapes[0].x0 == 25 and fig.layout.shapes[0].x1 == 25


def test_sweep_figures_use_the_mean_values():
    rows = R.all_variants(RES)
    f = V.build_sweep_passes(rows)
    assert [t.name for t in f.data] == [C.METHOD_LABELS["seq_num"], C.METHOD_LABELS["radix"], C.METHOD_LABELS["exact"]]
    assert list(f.data[0].y) == [2.5, 1.0] and list(f.data[1].y) == [2.0, 1.0] and list(f.data[2].y) == [1.5, 1.0]
    m = V.build_sweep_moves(rows)
    assert [round(x, 3) for x in m.data[0].y] == [2.125, 1.0] and [round(x, 3) for x in m.data[2].y] == [2.0, 1.0]
    b = V.build_better_share(rows)
    assert list(b.data[0].y) == [50.0, 0.0]
    ls = V.build_length_series(rows)
    assert list(ls.data[0].y) == [50.0, 0.0] and ls.data[0].text == ("50 %", "0 %")


@pytest.mark.parametrize("make", [lambda: V.build_time_bars(STD, 20), lambda: V.build_setup_lines(STD, 20), lambda: V.build_train_strips(G, M.plan_radix(G, 2), 2),
                                  lambda: V.build_sweep_passes(R.all_variants(RES)), lambda: V.build_sweep_moves(R.all_variants(RES)), lambda: V.build_better_share(R.all_variants(RES)),
                                  lambda: V.build_length_series(R.all_variants(RES))])
def test_all_axes_are_fixed_for_touch_scrolling(make):
    fig = make()
    assert fig.layout.xaxis.fixedrange is True and fig.layout.yaxis.fixedrange is True
