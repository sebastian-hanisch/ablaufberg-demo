"""Live-Rechnung der drei Verfahren, Bergzeit, Kipppunkt und die Meldungen der App."""
from __future__ import annotations

import time

import abl_constants as C
import abl_model as M


def bergzeit(passes: int, moves: int, setup: float) -> float:
    """Bergzeit (min) = Durchgänge mal Aufwand je Durchgang plus Wagenbewegungen mal Abdrückzeit je Wagen."""
    return passes * setup + moves * C.CAR_MIN


def run_live(settings: dict) -> dict:
    """Drei Verfahren auf dem Zug der Einstellungen; jeder Plan wird vom unabhängigen Prüfer abgenommen."""
    t0 = time.time()
    group_of = M.generate(settings["n"], settings["m"], settings["sizes"], settings["seed"])
    k = settings["k"]
    results = {}
    for key in C.METHODS:
        schedule = M.plan(group_of, k, key)
        met = M.metrics(schedule)
        results[key] = {"schedule": schedule, "passes": met["passes"], "moves": met["moves"], "valid": M.valid_schedule(group_of, schedule, k)}
    return {"group_of": group_of, "m_eff": len(M.present_groups(group_of)), "results": results, "seconds": time.time() - t0}


def times(run: dict, setup: float) -> dict:
    return {k: bergzeit(r["passes"], r["moves"], setup) for k, r in run["results"].items()}


def fastest(run: dict, setup: float) -> str:
    t = times(run, setup)
    return min(C.METHODS, key=lambda k: (t[k], run["results"][k]["passes"], C.METHODS.index(k)))


def crossover(a: dict, b: dict):
    """Aufwand je Durchgang (min), bei dem zwei Verfahren gleich lang brauchen. `a` hat mehr Durchgänge und weniger Wagenbewegungen als `b`
    (dann gewinnt a unterhalb des Wertes, b oberhalb); sonst None (eines ist in beiden Größen mindestens so gut)."""
    dp = a["passes"] - b["passes"]
    dm = b["moves"] - a["moves"]
    if dp > 0 and dm > 0:
        return dm * C.CAR_MIN / dp
    return None


def best_sequential(run: dict) -> str:
    """Das bessere der beiden gruppenweisen Verfahren (gleiche Durchgänge, weniger Wagenbewegungen; bei Gleichstand nach Nummer)."""
    r = run["results"]
    return "seq_size" if r["seq_size"]["moves"] < r["seq_num"]["moves"] else "seq_num"


def time_message(run: dict, setup: float) -> tuple:
    """(Zustand, Text): wer ist bei diesem Aufwand je Durchgang am schnellsten, und wo kippt es."""
    r = run["results"]
    best = fastest(run, setup)
    seq = best_sequential(run)
    x = crossover(r[seq], r["radix"])
    t = times(run, setup)
    if r["radix"]["passes"] <= 1:
        return "trivial", f"Mit höchstens so vielen Gruppen wie Gleisen reicht ein Durchgang: alle Verfahren sind gleich, die Bergzeit ist {t['radix']:.0f} min."
    if r["radix"]["passes"] <= r[seq]["passes"] and r["radix"]["moves"] <= r[seq]["moves"]:
        return "radix", (f"Radix ist hier in beiden Größen mindestens so gut: {r['radix']['passes']} Durchgänge und {r['radix']['moves']} Wagenbewegungen gegen {r[seq]['passes']} und "
                         f"{r[seq]['moves']} beim gruppenweisen Abarbeiten. Die Bergzeit ist {t['radix']:.0f} min gegen {t[seq]:.0f} min; den Aufwand je Durchgang umzustellen ändert daran nichts.")
    if x is None:
        return "other", f"Am schnellsten ist {C.METHOD_LABELS[best]} mit {t[best]:.0f} min Bergzeit."
    if best == "radix":
        return "radix", (f"Radix gewinnt mit {t['radix']:.0f} min Bergzeit gegen {t[seq]:.0f} min beim gruppenweisen Abarbeiten: ein Durchgang kostet hier {setup:.0f} min, "
                         f"das Umschlagen lohnt sich erst unter {x:.0f} min Aufwand je Durchgang.")
    return "sequential", (f"Das gruppenweise Abarbeiten gewinnt mit {t[seq]:.0f} min Bergzeit gegen {t['radix']:.0f} min bei Radix: ein Durchgang kostet nur {setup:.0f} min, "
                          f"es bewegt {r[seq]['moves']} statt {r['radix']['moves']} Wagen. Ab {x:.0f} min Aufwand je Durchgang gewinnt Radix.")


def passes_message(run: dict, k: int) -> str:
    r = run["results"]
    m_eff = run["m_eff"]
    return (f"{m_eff} Gruppen auf {k} Gleisen: Radix braucht {r['radix']['passes']} Durchgänge (kleinstes d mit {k}^d ≥ {m_eff}), das gruppenweise Abarbeiten "
            f"{r['seq_num']['passes']} (je Durchgang werden {k - 1} Gruppen fertig).")


def exact_message(run: dict, exact: dict) -> tuple:
    """(Zustand, Text) zum Ergebnis des Exakt-Tabs; exact = Rückgabe von abl_exact.min_passes."""
    rad = run["results"]["radix"]["passes"]
    if not exact["proven"]:
        return "unproven", (f"Im Zeitlimit nicht entschieden: bewiesen ist nur, dass Radix mit {rad} Durchgängen genügt; ob es mit weniger geht, ist offen "
                            f"(gefunden: {exact['passes']} Durchgänge).")
    if exact["passes"] < rad:
        return "better", f"Exakt reichen {exact['passes']} statt {rad} Durchgänge: hier schlägt eine auf diesen Zug zugeschnittene Lösung Radix."
    return "same", f"Exakt sind {exact['passes']} Durchgänge nötig, genau so viele wie bei Radix: bewiesen, dass es für diesen Zug nicht besser geht."
