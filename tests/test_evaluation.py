"""Bergzeit, Kipppunkt, Meldungen und die Live-Rechnung, mit künstlichen Werten an jeder Schwelle."""
import pytest

import abl_constants as C
import abl_evaluation as E


def fake(num, size, radix, m_eff=8):
    """Künstlicher Lauf: je Verfahren (Durchgänge, Wagenbewegungen)."""
    return {"m_eff": m_eff, "group_of": [], "seconds": 0.0,
            "results": {k: {"passes": p, "moves": m, "valid": True, "schedule": []} for k, (p, m) in (("seq_num", num), ("seq_size", size), ("radix", radix))}}


STD = fake((3, 72), (3, 64), (2, 80))


def test_bergzeit_by_hand():
    assert E.bergzeit(3, 72, 20) == 3 * 20 + 72 * 0.5 == 96
    assert E.bergzeit(2, 80, 20) == 80 and E.bergzeit(0, 0, 55) == 0 and E.bergzeit(2, 80, 0) == 40


def test_times_and_fastest_follow_the_setup():
    t = E.times(STD, 20)
    assert t == {"seq_num": 96, "seq_size": 92, "radix": 80}
    assert E.fastest(STD, 20) == "radix"
    assert E.fastest(STD, 5) == "seq_size"                                         # 47 gegen 50 gegen 51
    assert E.times(STD, 5) == {"seq_num": 51, "seq_size": 47, "radix": 50}
    assert E.fastest(STD, 8) == "radix"                                            # Gleichstand 56 gegen 56: weniger Durchgänge gewinnt


def test_crossover_is_the_setup_where_two_methods_take_equally_long():
    a, b = STD["results"]["seq_size"], STD["results"]["radix"]
    x = E.crossover(a, b)
    assert x == 8.0 and E.bergzeit(a["passes"], a["moves"], x) == E.bergzeit(b["passes"], b["moves"], x)
    assert E.crossover(b, a) is None                                               # b hat weniger Durchgänge: keine Umkehr
    assert E.crossover({"passes": 3, "moves": 80}, {"passes": 2, "moves": 80}) is None   # nicht weniger Wagenbewegungen
    assert E.crossover({"passes": 2, "moves": 60}, {"passes": 2, "moves": 80}) is None   # gleich viele Durchgänge
    assert E.crossover({"passes": 3, "moves": 70}, {"passes": 1, "moves": 80}) == 2.5


def test_best_sequential_is_the_one_with_fewer_moves_and_nums_win_ties():
    assert E.best_sequential(STD) == "seq_size"
    assert E.best_sequential(fake((3, 64), (3, 64), (2, 80))) == "seq_num"
    assert E.best_sequential(fake((3, 60), (3, 64), (2, 80))) == "seq_num"


def test_message_radix_wins_at_high_setup_and_names_the_tipping_point():
    state, text = E.time_message(STD, 20)
    assert state == "radix" and "Radix gewinnt mit 80 min" in text and "unter 8 min" in text and "92 min" in text


def test_message_sequential_wins_at_low_setup_and_names_the_tipping_point():
    state, text = E.time_message(STD, 5)
    assert state == "sequential" and "gewinnt mit 47 min" in text and "Ab 8 min" in text and "64 statt 80" in text


def test_message_when_radix_is_better_in_both_sizes():
    run = fake((5, 118), (5, 99), (2, 80), m_eff=16)
    state, text = E.time_message(run, 20)
    assert state == "radix" and "in beiden Größen mindestens so gut" in text and "ändert daran nichts" in text and "2 Durchgänge und 80 Wagenbewegungen" in text
    assert E.time_message(run, 0)[0] == "radix"


def test_message_when_one_pass_is_enough():
    state, text = E.time_message(fake((1, 40), (1, 40), (1, 40), m_eff=4), 20)
    assert state == "trivial" and "ein Durchgang" in text and "40 min" in text


def test_message_when_the_sequential_method_has_equal_passes():
    run = fake((2, 60), (2, 55), (2, 80))                                            # gleiche Durchgänge, weniger Bewegungen: gruppenweise ist besser, kein Kipppunkt
    state, text = E.time_message(run, 20)
    assert state == "other" and C.METHOD_LABELS["seq_size"] in text


def test_passes_message_names_groups_tracks_and_both_counts():
    text = E.passes_message(STD, 4)
    assert "8 Gruppen auf 4 Gleisen" in text and "2 Durchgänge" in text and "4^d ≥ 8" in text and "3 (je Durchgang werden 3 Gruppen fertig)" in text


def test_exact_message_has_three_states():
    run = fake((3, 72), (3, 64), (3, 120), m_eff=12)
    assert E.exact_message(run, {"passes": 2, "proven": True})[0] == "better"
    assert "2 statt 3" in E.exact_message(run, {"passes": 2, "proven": True})[1]
    s, t = E.exact_message(run, {"passes": 3, "proven": True})
    assert s == "same" and "bewiesen" in t
    s, t = E.exact_message(run, {"passes": 3, "proven": False})
    assert s == "unproven" and "Zeitlimit" in t and "offen" in t
    s, t = E.exact_message(run, {"passes": 2, "proven": False})
    assert s == "unproven" and "gefunden: 2" in t


def test_live_run_on_the_standard_train_is_frozen_and_valid():
    run = E.run_live({"n": 40, "m": 8, "k": 4, "sizes": "gleich", "seed": 500})
    r = run["results"]
    assert run["m_eff"] == 8 and len(run["group_of"]) == 40 and all(v["valid"] for v in r.values())
    assert [(r[k]["passes"], r[k]["moves"]) for k in C.METHODS] == [(3, 72), (3, 64), (2, 80)]


def test_live_run_changes_with_every_setting():
    base = {"n": 40, "m": 8, "k": 4, "sizes": "gleich", "seed": 500}
    ref = E.run_live(base)["results"]
    snap = {k: (v["passes"], v["moves"]) for k, v in ref.items()}
    for change in ({"k": 2}, {"m": 16}, {"n": 20}, {"sizes": "ungleich"}, {"seed": 501}):
        other = E.run_live({**base, **change})["results"]
        assert {k: (v["passes"], v["moves"]) for k, v in other.items()} != snap, change


@pytest.mark.parametrize("key", C.METHODS)
def test_every_method_runs_on_extreme_settings(key):
    for k in C.K_OPTIONS:
        for m in C.M_OPTIONS:
            run = E.run_live({"n": 20, "m": m, "k": k, "sizes": "ungleich", "seed": 1})
            assert run["results"][key]["valid"]


def test_message_when_both_methods_are_exactly_equal_radix_is_named_as_good_as_the_other():
    state, text = E.time_message(fake((2, 80), (2, 80), (2, 80)), 20)
    assert state == "radix" and "in beiden Größen mindestens so gut" in text
