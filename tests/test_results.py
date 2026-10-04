"""Auswertung der Messreihe an einer von Hand gerechneten Mini-Ergebnisdatei (4 Züge, 10 Wagen je Zug)."""
import json

import pytest

import abl_constants as C
import abl_results as R


def row(variant, num, size, radix, exact, proven=True, time=1.0, m_eff=4):
    return {"variant": variant, "seed": 0, "n_cars": 10, "m_eff": m_eff,
            "methods": {"seq_num": {"passes": num[0], "moves": num[1], "valid": True}, "seq_size": {"passes": size[0], "moves": size[1], "valid": True},
                        "radix": {"passes": radix[0], "moves": radix[1], "valid": True}},
            "exact": {"passes": exact, "proven": proven, "time": time, "valid": True}}


RES = {"meta": {"variants": ["V1", "V2"]}, "rows": [
    row("V1", (2, 15), (2, 12), (2, 20), 1, True, 1.0),
    row("V1", (3, 25), (3, 20), (2, 20), 2, True, 3.0),
    row("V1", (2, 15), (2, 14), (2, 20), 2, False, 5.0),
    row("V1", (3, 30), (3, 22), (2, 20), 1, True, 2.0),
    row("V2", (1, 10), (1, 10), (1, 10), 1, True, 0.5),
]}


def test_summary_by_hand():
    s = R.summary(RES, "V1")
    assert s["n"] == 4 and s["proven"] == 3
    assert s["passes_seq_num"] == 2.5 and s["passes_seq_num_se"] == pytest.approx(0.288675, abs=1e-6)
    assert s["permove_seq_num"] == pytest.approx((1.5 + 2.5 + 1.5 + 3.0) / 4)
    assert s["moves_seq_num"] == 21.25 and s["moves_seq_size"] == 17 and s["moves_radix"] == 20
    assert s["passes_radix"] == 2.0 and s["passes_exact"] == 1.5
    assert s["exact_better"] == 2 and s["exact_better_share"] == 0.5                  # nur bewiesene Fälle zählen: Zeile 1 und 4, nicht Zeile 3 (unbewiesen)
    assert s["time_median"] == 2.5
    assert s["crossover"] == pytest.approx(3.0)                                         # gruppenweise (größte zuerst) 2.5 Durchgänge/17 Bewegungen gegen Radix 2/20


def test_summary_of_a_trivial_variant_has_no_crossover():
    s = R.summary(RES, "V2")
    assert s["n"] == 1 and s["crossover"] is None and s["exact_better"] == 0 and s["passes_exact"] == 1


def test_all_variants_follow_the_meta_order():
    assert [v["name"] for v in R.all_variants(RES)] == ["V1", "V2"]


def test_a_single_run_variant_has_no_standard_error():
    s = R.summary(RES, "V2")
    assert s["passes_seq_num_se"] != s["passes_seq_num_se"]                              # nan


def test_variant_name_matches_the_four_structural_levers_only():
    assert R.variant_name({"n": 40, "m": 8, "k": 4, "sizes": "gleich", "setup": 20, "seed": 500}) == "Standard (40 Wagen)"
    assert R.variant_name({"n": 40, "m": 8, "k": 4, "sizes": "gleich", "setup": 5, "seed": 3}) == "Standard (40 Wagen)"
    assert R.variant_name({"n": 40, "m": 8, "k": 4, "sizes": "ungleich", "setup": 20, "seed": 500}) == "Ungleiche Gruppen"
    assert R.variant_name({"n": 40, "m": 12, "k": 3, "sizes": "gleich", "setup": 20, "seed": 500}) == "12 Gruppen, 3 Gleise"
    assert R.variant_name({"n": 20, "m": 4, "k": 2, "sizes": "gleich", "setup": 20, "seed": 500}) is None


def test_variant_names_are_unique_and_configurations_distinct():
    names = [v[0] for v in C.SWEEP_VARIANTS]
    configs = [v[1:] for v in C.SWEEP_VARIANTS]
    assert len(set(names)) == len(names) and len(set(configs)) == len(configs)
    assert set(C.LENGTH_SERIES) <= set(names)


def test_load_results_reads_a_file(tmp_path):
    f = tmp_path / "res.json"
    f.write_text(json.dumps(RES), encoding="utf-8")
    assert R.load_results(f)["meta"]["variants"] == ["V1", "V2"]


def test_mean_se_of_a_pair():
    m, se = R.mean_se([1, 3])
    assert m == 2 and se == pytest.approx(1.0)
