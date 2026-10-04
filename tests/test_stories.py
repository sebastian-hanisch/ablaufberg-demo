"""Preset-Kriterien: jedes Kriterium kippt einzeln an seiner Schwelle (künstliche Zahlen), und `facts_for` liest die richtigen Größen."""
import pytest

import abl_constants as C
import abl_evaluation as E
import abl_results as R
import abl_stories as S

BASE = dict(m_eff=8, k=4, sizes="gleich", setup=20, seq_passes=3, seq_num_passes=3, seq_size_passes=3, seq_num_moves=72, seq_size_moves=64, radix_passes=2, radix_moves=80,
            fastest="radix", crossover=8.0, ref_seq_passes=3, ref_radix_passes=2, exact_passes=None, exact_proven=False, sweep_radix_passes=2.0, sweep_seq_passes=3.0,
            sweep_exact_passes=2.0, sweep_exact_better_share=0.0, sweep_seq_size_permove=1.6, sweep_seq_num_permove=1.9)

GOOD = {
    "Standard": {},
    "Viele Gruppen": dict(m_eff=15, seq_passes=5, seq_num_passes=5, seq_size_passes=5, seq_size_moves=99, seq_num_moves=118, crossover=None),
    "Wenige Gleise": dict(k=2, radix_passes=3, seq_passes=7, ref_radix_passes=2, crossover=None),
    "Ungleiche Gruppen": dict(sizes="ungleich", seq_size_moves=55, seq_num_moves=70, sweep_seq_size_permove=1.31, sweep_seq_num_permove=1.70),
    "Billiger Durchgang": dict(setup=5, fastest="seq_size"),
    "Gruppen teilen": dict(m_eff=12, k=3, radix_passes=3, exact_passes=2, exact_proven=True, sweep_exact_better_share=1.0, crossover=None),
}

BREAK = {
    "Standard": {"radix_fewer": dict(radix_passes=3), "radix_fastest": dict(fastest="seq_size"), "seq_fewer_moves": dict(seq_size_moves=80), "crossover_below": dict(crossover=20.0),
                 "sweep_radix_fewer": dict(sweep_radix_passes=3.0, sweep_exact_passes=3.0), "sweep_exact_equal": dict(sweep_exact_passes=1.9)},
    "Viele Gruppen": {"sixteen": dict(m_eff=13), "seq_many": dict(seq_passes=3, ref_seq_passes=2), "radix_few": dict(radix_passes=3), "radix_dominates": dict(radix_moves=100),
                      "radix_fastest": dict(fastest="seq_num"), "more_than_standard": dict(ref_seq_passes=5)},
    "Wenige Gleise": {"two_tracks": dict(k=3), "radix_three": dict(radix_passes=2, ref_radix_passes=1), "seq_double": dict(seq_passes=5), "radix_fastest": dict(fastest="seq_size"),
                      "more_than_standard": dict(ref_radix_passes=3)},
    "Ungleiche Gruppen": {"unequal": dict(sizes="gleich"), "fewer_moves": dict(seq_size_moves=66), "same_passes": dict(seq_size_passes=2), "sweep_fewer_moves": dict(sweep_seq_size_permove=1.5)},
    "Billiger Durchgang": {"cheap": dict(setup=8.0), "seq_fastest": dict(fastest="radix"), "radix_fewer_passes": dict(radix_passes=3), "standard_other": dict(crossover=25.0)},
    "Gruppen teilen": {"twelve": dict(m_eff=10), "three_tracks": dict(k=4), "radix_three": dict(radix_passes=4), "exact_saves": dict(exact_passes=3), "sweep_exact_saves": dict(sweep_exact_better_share=0.85)},
}


def facts(preset, **over):
    return {**BASE, **GOOD[preset], **over}


def failing(preset, **over):
    return [cid for cid, _, ok in S.check(preset, facts(preset, **over)) if not ok]


def test_every_preset_has_criteria_and_breakers_for_each_of_them():
    assert set(S.CRITERIA) == set(C.PRESET_ORDER) == set(GOOD) == set(BREAK)
    for name in C.PRESET_ORDER:
        assert {cid for cid, _, _ in S.CRITERIA[name]} == set(BREAK[name]), name


@pytest.mark.parametrize("preset", C.PRESET_ORDER)
def test_good_facts_pass_every_criterion(preset):
    assert failing(preset) == []


@pytest.mark.parametrize("preset,cid", [(p, c) for p in C.PRESET_ORDER for c in BREAK[p]])
def test_each_criterion_flips_alone(preset, cid):
    assert failing(preset, **BREAK[preset][cid]) == [cid]


def test_thresholds_are_exact():
    assert failing("Ungleiche Gruppen", seq_size_moves=63, seq_num_moves=70) == [] and failing("Ungleiche Gruppen", seq_size_moves=64, seq_num_moves=70) == ["fewer_moves"]
    assert failing("Ungleiche Gruppen", sweep_seq_size_permove=1.7, sweep_seq_num_permove=2.0) == [] and failing("Ungleiche Gruppen", sweep_seq_size_permove=1.71, sweep_seq_num_permove=2.0) == ["sweep_fewer_moves"]
    assert failing("Viele Gruppen", m_eff=14) == [] and failing("Viele Gruppen", m_eff=13) == ["sixteen"]
    assert failing("Viele Gruppen", seq_passes=4, ref_seq_passes=2) == [] and failing("Viele Gruppen", seq_passes=3, ref_seq_passes=2) == ["seq_many"]
    assert failing("Viele Gruppen", radix_moves=99) == [] and failing("Viele Gruppen", radix_moves=100) == ["radix_dominates"]
    assert failing("Wenige Gleise", seq_passes=6) == [] and failing("Wenige Gleise", seq_passes=5) == ["seq_double"]
    assert failing("Billiger Durchgang", setup=5, crossover=19.9) == [] and failing("Billiger Durchgang", setup=5, crossover=20.0) == ["standard_other"]
    assert failing("Billiger Durchgang", setup=7.9, crossover=8.0) == [] and failing("Billiger Durchgang", setup=8.0, crossover=8.0) == ["cheap"]
    assert failing("Gruppen teilen", sweep_exact_better_share=0.9) == [] and failing("Gruppen teilen", sweep_exact_better_share=0.89) == ["sweep_exact_saves"]
    assert failing("Gruppen teilen", m_eff=11) == [] and failing("Gruppen teilen", m_eff=10) == ["twelve"]
    assert failing("Standard", crossover=19.9) == [] and failing("Standard", crossover=20.0) == ["crossover_below"]


def test_unproven_or_missing_exact_result_fails_the_split_story():
    assert failing("Gruppen teilen", exact_proven=False) == ["exact_saves"]
    assert failing("Gruppen teilen", exact_passes=None, exact_proven=False) == ["exact_saves"]
    assert failing("Billiger Durchgang", crossover=None) == ["cheap", "standard_other"]


def test_facts_for_reads_the_live_run_and_the_sweep():
    res = R.load_results()
    p = C.PRESETS["Standard"]
    settings = {k: p[k] for k in ("n", "m", "k", "sizes", "setup", "seed")}
    run = E.run_live(settings)
    f = S.facts_for(run, run, res, settings)
    assert (f["m_eff"], f["k"], f["sizes"], f["setup"]) == (8, 4, "gleich", 20)
    assert (f["seq_num_passes"], f["seq_num_moves"], f["seq_size_moves"], f["radix_passes"], f["radix_moves"]) == (3, 72, 64, 2, 80)
    assert f["fastest"] == "radix" and f["crossover"] == 8.0 and f["exact_passes"] is None and f["exact_proven"] is False
    v = R.summary(res, "Standard (40 Wagen)")
    assert f["sweep_radix_passes"] == v["passes_radix"] and f["sweep_seq_passes"] == v["passes_seq_num"] and f["sweep_exact_better_share"] == v["exact_better_share"]
    assert f["sweep_seq_size_permove"] == v["permove_seq_size"] and f["ref_seq_passes"] == 3 and f["ref_radix_passes"] == 2
    g = S.facts_for(run, run, res, settings, {"passes": 2, "proven": True})
    assert g["exact_proven"] is True and g["exact_passes"] == 2


def test_facts_for_without_a_sweep_variant_uses_neutral_sweep_values():
    res = R.load_results()
    settings = {"n": 20, "m": 4, "k": 2, "sizes": "gleich", "setup": 20, "seed": 1}
    run = E.run_live(settings)
    f = S.facts_for(run, run, res, settings)
    assert f["sweep_radix_passes"] == 0 and f["sweep_exact_better_share"] == 0.0
