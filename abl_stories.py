"""Abnahmekriterien der Presets: jedes Preset erzählt eine Geschichte, die am gezeigten Zug UND an der Messreihe überprüfbar ist.

Reine Funktionen einfacher Zahlen (`check`), damit Tests sie mit künstlichen Werten einzeln an ihrer Schwelle kippen können; `facts_for` baut die Zahlen aus einer Live-Rechnung,
dem Standard-Lauf auf demselben Seed, der Ergebnisdatei und (nur für „Gruppen teilen“) einem Ergebnis der exakten Rechnung. `tools/preset_search.py` sucht damit einen Seed außerhalb der
Messreihen-Seeds, bei dem alle Kriterien aller Presets gelten.
"""
from __future__ import annotations

import abl_constants as C
import abl_evaluation as E
import abl_results as R

CRITERIA = {
    "Standard": [
        ("radix_fewer", "Radix braucht weniger Durchgänge als das gruppenweise Abarbeiten", lambda f: f["radix_passes"] < f["seq_passes"]),
        ("radix_fastest", "Radix ist beim voreingestellten Aufwand je Durchgang am schnellsten", lambda f: f["fastest"] == "radix"),
        ("seq_fewer_moves", "das gruppenweise Abarbeiten (größte zuerst) bewegt weniger Wagen als Radix", lambda f: f["seq_size_moves"] < f["radix_moves"]),
        ("crossover_below", "der Kipppunkt liegt unter dem voreingestellten Aufwand", lambda f: f["crossover"] is not None and f["crossover"] < f["setup"]),
        ("sweep_radix_fewer", "Messreihe: Radix braucht im Mittel weniger Durchgänge als das gruppenweise Abarbeiten", lambda f: f["sweep_radix_passes"] < f["sweep_seq_passes"]),
        ("sweep_exact_equal", "Messreihe: die exakte Lösung braucht im Mittel genau so viele Durchgänge wie Radix", lambda f: f["sweep_exact_passes"] == f["sweep_radix_passes"]),
    ],
    "Viele Gruppen": [
        ("sixteen", "mindestens 14 Gruppen sind im Zug", lambda f: f["m_eff"] >= 14),
        ("seq_many", "das gruppenweise Abarbeiten braucht mindestens 4 Durchgänge", lambda f: f["seq_passes"] >= 4),
        ("radix_few", "Radix braucht höchstens 2 Durchgänge", lambda f: f["radix_passes"] <= 2),
        ("radix_dominates", "Radix bewegt nicht mehr Wagen als das gruppenweise Abarbeiten (größte zuerst)", lambda f: f["radix_moves"] <= f["seq_size_moves"]),
        ("radix_fastest", "Radix ist beim voreingestellten Aufwand je Durchgang am schnellsten", lambda f: f["fastest"] == "radix"),
        ("more_than_standard", "mehr Durchgänge beim gruppenweisen Abarbeiten als im Standardzug", lambda f: f["seq_passes"] > f["ref_seq_passes"]),
    ],
    "Wenige Gleise": [
        ("two_tracks", "der Zug hat 2 Gleise", lambda f: f["k"] == 2),
        ("radix_three", "Radix braucht mindestens 3 Durchgänge", lambda f: f["radix_passes"] >= 3),
        ("seq_double", "das gruppenweise Abarbeiten braucht mindestens doppelt so viele Durchgänge wie Radix", lambda f: f["seq_passes"] >= 2 * f["radix_passes"]),
        ("radix_fastest", "Radix ist beim voreingestellten Aufwand je Durchgang am schnellsten", lambda f: f["fastest"] == "radix"),
        ("more_than_standard", "Radix braucht mehr Durchgänge als im Standardzug", lambda f: f["radix_passes"] > f["ref_radix_passes"]),
    ],
    "Ungleiche Gruppen": [
        ("unequal", "die Gruppengrößen sind ungleich", lambda f: f["sizes"] == "ungleich"),
        ("fewer_moves", "größte zuerst bewegt mindestens 10 % weniger Wagen als nach Nummer", lambda f: f["seq_size_moves"] <= 0.9 * f["seq_num_moves"]),
        ("same_passes", "beide gruppenweisen Verfahren brauchen gleich viele Durchgänge", lambda f: f["seq_size_passes"] == f["seq_num_passes"]),
        ("sweep_fewer_moves", "Messreihe: größte zuerst bewegt im Mittel mindestens 15 % weniger Wagen als nach Nummer", lambda f: f["sweep_seq_size_permove"] <= 0.85 * f["sweep_seq_num_permove"]),
    ],
    "Billiger Durchgang": [
        ("cheap", "der Aufwand je Durchgang liegt unter dem Kipppunkt", lambda f: f["crossover"] is not None and f["setup"] < f["crossover"]),
        ("seq_fastest", "das gruppenweise Abarbeiten ist am schnellsten", lambda f: f["fastest"] in ("seq_num", "seq_size")),
        ("radix_fewer_passes", "Radix braucht dennoch weniger Durchgänge", lambda f: f["radix_passes"] < f["seq_passes"]),
        ("standard_other", "bei 20 min Aufwand je Durchgang wäre Radix am schnellsten (Kipppunkt unter 20 min)", lambda f: f["crossover"] is not None and f["crossover"] < 20),
    ],
    "Gruppen teilen": [
        ("twelve", "mindestens 11 Gruppen sind im Zug", lambda f: f["m_eff"] >= 11),
        ("three_tracks", "der Zug hat 3 Gleise", lambda f: f["k"] == 3),
        ("radix_three", "Radix braucht 3 Durchgänge", lambda f: f["radix_passes"] == 3),
        ("exact_saves", "die exakte Lösung schafft es mit weniger Durchgängen als Radix (bewiesen)", lambda f: f["exact_passes"] is not None and f["exact_proven"] and f["exact_passes"] < f["radix_passes"]),
        ("sweep_exact_saves", "Messreihe: die exakte Lösung ist in mindestens 90 % der Züge besser als Radix", lambda f: f["sweep_exact_better_share"] >= 0.9),
    ],
}


def facts_for(run: dict, ref: dict, res: dict, settings: dict, exact: dict | None = None) -> dict:
    """Die Zahlen für die Kriterien. `ref` = Lauf mit den Standardreglern auf demselben Seed; `exact` = Rückgabe von abl_exact.min_passes für `run` (nur wo gebraucht)."""
    r = run["results"]
    seq = E.best_sequential(run)
    vname = R.variant_name(settings)
    sw = R.summary(res, vname) if vname else None
    f = {"m_eff": run["m_eff"], "k": settings["k"], "sizes": settings["sizes"], "setup": settings["setup"],
         "seq_passes": r["seq_num"]["passes"], "seq_num_passes": r["seq_num"]["passes"], "seq_size_passes": r["seq_size"]["passes"],
         "seq_num_moves": r["seq_num"]["moves"], "seq_size_moves": r["seq_size"]["moves"], "radix_passes": r["radix"]["passes"], "radix_moves": r["radix"]["moves"],
         "fastest": E.fastest(run, settings["setup"]), "crossover": E.crossover(r[seq], r["radix"]),
         "ref_seq_passes": ref["results"]["seq_num"]["passes"], "ref_radix_passes": ref["results"]["radix"]["passes"],
         "exact_passes": None if exact is None else exact["passes"], "exact_proven": exact is not None and exact["proven"]}
    f.update({"sweep_radix_passes": sw["passes_radix"], "sweep_seq_passes": sw["passes_seq_num"], "sweep_exact_passes": sw["passes_exact"], "sweep_exact_better_share": sw["exact_better_share"],
              "sweep_seq_size_permove": sw["permove_seq_size"], "sweep_seq_num_permove": sw["permove_seq_num"]} if sw else
             {"sweep_radix_passes": 0, "sweep_seq_passes": 0, "sweep_exact_passes": 0, "sweep_exact_better_share": 0.0, "sweep_seq_size_permove": 0.0, "sweep_seq_num_permove": 0.0})
    return f


def check(preset: str, facts: dict) -> list:
    """Liste (Kennung, Text, erfüllt) der Kriterien eines Presets."""
    return [(cid, text, bool(fn(facts))) for cid, text, fn in CRITERIA[preset]]
