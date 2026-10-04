"""Vorgerechnete Messreihe (data/abl_results.json, erzeugt mit tools/sweep.py): Auswertung je Variante. Die App rechnet sie nie live."""
from __future__ import annotations

import json
import statistics as st
from pathlib import Path

import abl_constants as C
import abl_evaluation as E

ROOT = Path(__file__).resolve().parent


def load_results(path=None) -> dict:
    return json.loads(Path(path or ROOT / C.RESULTS_FILE).read_text(encoding="utf-8"))


def mean_se(xs) -> tuple:
    xs = list(xs)
    return st.mean(xs), (st.stdev(xs) / len(xs) ** 0.5 if len(xs) > 1 else float("nan"))


def rows_of(res: dict, variant: str) -> list:
    return [r for r in res["rows"] if r["variant"] == variant]


def proven(row: dict) -> bool:
    return row["exact"]["proven"]


def summary(res: dict, variant: str) -> dict:
    rows = rows_of(res, variant)
    out = {"n": len(rows), "proven": sum(1 for r in rows if proven(r)), "m_eff": st.mean(r["m_eff"] for r in rows)}
    for key in C.METHODS:
        out[f"passes_{key}"], out[f"passes_{key}_se"] = mean_se(r["methods"][key]["passes"] for r in rows)
        out[f"permove_{key}"] = st.mean(r["methods"][key]["moves"] / r["n_cars"] for r in rows)
        out[f"moves_{key}"] = st.mean(r["methods"][key]["moves"] for r in rows)
    out["passes_exact"] = st.mean(r["exact"]["passes"] for r in rows)
    out["exact_better"] = sum(1 for r in rows if proven(r) and r["exact"]["passes"] < r["methods"]["radix"]["passes"])
    out["exact_better_share"] = out["exact_better"] / len(rows)
    out["time_median"] = st.median(r["exact"]["time"] for r in rows)
    seq = "seq_size"
    out["crossover"] = E.crossover({"passes": out[f"passes_{seq}"], "moves": out[f"moves_{seq}"]}, {"passes": out["passes_radix"], "moves": out["moves_radix"]})
    return out


def all_variants(res: dict) -> list:
    return [{"name": name, **summary(res, name)} for name in res["meta"]["variants"]]


def variant_name(settings: dict):
    """Welche Messreihen-Variante entspricht den Reglern genau (Aufwand je Durchgang und Seed gehören nicht dazu)? None, wenn keine."""
    key = (settings["n"], settings["m"], settings["k"], settings["sizes"])
    return {(n, m, k, s): name for name, n, m, k, s in C.SWEEP_VARIANTS}.get(key)
