"""Jede Zahl aus dem README wird hier aus data/abl_results.json nachgerechnet; die formatierten Texte müssen im README stehen.

20 Züge je Variante (Seeds 100-119), Mittelwerte. Die exakte Mindestzahl ist in allen Läufen bewiesen.
"""
from pathlib import Path

import pytest

import abl_constants as C
import abl_evaluation as E
import abl_results as R
import abl_stories as S

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def res():
    return R.load_results()


@pytest.fixture(scope="module")
def v(res):
    return {x["name"]: x for x in R.all_variants(res)}


def test_meta_and_counts(res):
    assert res["meta"]["seeds"] == [100, 120] and res["meta"]["variants"] == [x[0] for x in C.SWEEP_VARIANTS] and len(res["meta"]["variants"]) == 18
    for name in res["meta"]["variants"]:
        assert len(R.rows_of(res, name)) == 20
    assert all(m["valid"] for r in res["rows"] for m in r["methods"].values()) and all(r["exact"]["valid"] for r in res["rows"])
    assert all(R.proven(r) for r in res["rows"]) and len(res["rows"]) == 360 and "in allen 360 Läufen" in README
    assert "18 Varianten" in README and "Port 8961" in README


def test_standard_case_in_the_readme(v):
    s = v["Standard (40 Wagen)"]
    assert f"Gruppenweise **{s['passes_seq_num']:.1f}**, Radix **{s['passes_radix']:.1f}**, exakt **{s['passes_exact']:.1f}**" in README
    assert f"in {s['exact_better']} von {s['n']} Zügen" in README and s["exact_better"] == 0
    assert f"**{s['permove_seq_size']:.2f}** statt **{s['permove_radix']:.2f}** Bewegungen je Wagen" in README
    assert f"**Kipppunkt bei {s['crossover']:.1f} min**" in README
    assert f"Bei 60 Wagen {v['60 Wagen']['crossover']:.1f} min, bei ungleichen Gruppen {v['Ungleiche Gruppen']['crossover']:.1f} min" in README


def test_radix_wins_without_a_choice_in_the_readme(v):
    a, b = v["16 Gruppen"], v["2 Gleise"]
    assert f"**{a['passes_seq_num']:.1f}** Durchgänge gegen **{a['passes_radix']:.1f}**" in README and f"**{a['permove_seq_size']:.2f}** Bewegungen je Wagen auch mehr als Radix ({a['permove_radix']:.2f})" in README
    assert f"**{b['passes_seq_num']:.1f}** Durchgänge gegen **{b['passes_radix']:.1f}** und **{b['permove_seq_size']:.2f}** Bewegungen je Wagen gegen {b['permove_radix']:.2f}" in README
    for x in (a, b):                                                                          # Radix ist in beiden Größen mindestens so gut: gewinnt bei jedem Aufwand
        assert x["passes_radix"] < x["passes_seq_size"] and x["permove_radix"] < x["permove_seq_size"] and x["crossover"] is None


def test_largest_first_on_unequal_groups_in_the_readme(v):
    u = v["Ungleiche Gruppen"]
    assert f"**{u['permove_seq_size']:.2f}** statt **{u['permove_seq_num']:.2f}** Bewegungen je Wagen (−{100 * (1 - u['permove_seq_size'] / u['permove_seq_num']):.0f} %)" in README
    assert u["passes_seq_size"] == u["passes_seq_num"]


def test_exact_saves_in_the_readme(v):
    for name, share in (("12 Gruppen, 3 Gleise", 20), ("16 Gruppen, 3 Gleise", 20), ("12 Gruppen, 2 Gleise", 20), ("6 Gleise", 20), ("12 Gruppen", 0), ("16 Gruppen", 0)):
        assert v[name]["exact_better"] == share, name
    a = v["12 Gruppen, 3 Gleise"]
    assert f"**{a['passes_exact']:.1f}** statt **{a['passes_radix']:.1f}** Durchgängen (20 von 20)" in README
    b, c = v["12 Gruppen, 2 Gleise"], v["6 Gleise"]
    assert f"**{b['passes_exact']:.1f}** statt **{b['passes_radix']:.1f}**" in README and f"**{c['passes_exact']:.1f}** statt **{c['passes_radix']:.1f}**" in README
    assert v["16 Gruppen, 3 Gleise"]["passes_exact"] == a["passes_exact"] and v["16 Gruppen, 3 Gleise"]["passes_radix"] == a["passes_radix"]
    assert v["Standard (40 Wagen)"]["exact_better"] == 0 and v["12 Gruppen"]["passes_exact"] == v["12 Gruppen"]["passes_radix"]


def test_train_length_series_in_the_readme(v):
    shares = [round(100 * v[n]["exact_better_share"]) for n in C.LENGTH_SERIES]
    assert shares == [95, 100, 30, 0, 0]
    assert f"**{shares[0]} %** der 8-Wagen-Züge, **{shares[1]} %** der 12-Wagen-Züge, **{shares[2]} %** der 20-Wagen-Züge und in **{shares[3]} %** der 30- und 40-Wagen-Züge" in README


def test_solver_times_in_the_readme(res, v):
    assert f"Median **{v['Standard (40 Wagen)']['time_median']:.1f} s** bei 40 Wagen, **{v['60 Wagen']['time_median']:.1f} s** bei 60 Wagen" in README
    assert f"längste Rechnung **{max(r['exact']['time'] for r in res['rows']):.1f} s**" in README


def test_exact_is_never_worse_than_radix_and_orderings_hold(res):
    for r in res["rows"]:
        m = r["methods"]
        assert r["exact"]["passes"] <= m["radix"]["passes"] <= m["seq_num"]["passes"]
        assert m["seq_size"]["moves"] <= m["seq_num"]["moves"] and m["seq_size"]["passes"] == m["seq_num"]["passes"]


def test_vorab_artifact_claim_is_consistent_with_the_data(v):
    s8, s12, s20, s30, s40 = (v[n] for n in C.LENGTH_SERIES)
    assert s8["passes_exact"] < 1.1 and s8["passes_radix"] > 1.9 and s30["passes_exact"] == s30["passes_radix"] == s40["passes_exact"] == 2.0


@pytest.mark.parametrize("name", C.PRESET_ORDER)
def test_every_preset_tells_its_story_on_the_shown_train(res, name):
    from abl_exact import min_passes
    p = C.PRESETS[name]
    settings = {k: p[k] for k in ("n", "m", "k", "sizes", "setup", "seed")}
    ref = E.run_live({**{k: C.PRESETS["Standard"][k] for k in ("n", "m", "k", "sizes")}, "seed": p["seed"]})
    run = ref if name == "Standard" else E.run_live(settings)
    exact = min_passes(run["group_of"], p["k"], 60.0, workers=1) if name == "Gruppen teilen" else None
    failed = [text for _, text, ok in S.check(name, S.facts_for(run, ref, res, settings, exact)) if not ok]
    assert not failed, (name, failed)
