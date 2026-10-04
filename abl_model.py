"""Ablaufberg: Zug, Richtungsgleise, Durchgänge, die beiden Verfahren und der unabhängige Prüfer.

Ein Zug mit n Wagen (Nummern 0..n-1 in Zugfolge) wird über den Berg auf k Richtungsgleise abgedrückt (FIFO: wer zuerst rollt, steht vorn). Ein Durchgang verteilt alle Wagen
des Zuges auf Gleise; danach werden einzelne Gleise als Abfahrtszug-Teil fertig abgezogen (`finish`), die übrigen in Gleisreihenfolge zum neuen Zug zusammengezogen.
Ziel: Jede Zielgruppe (Abfahrtszug) steht am Ende zusammenhängend. Kosten: Durchgänge und Wagenbewegungen (Summe der Zuglängen vor jedem Durchgang).
"""
from __future__ import annotations

import abl_constants as C
from abl_rng import SplitMix64


class ScheduleError(ValueError):
    """Der Plan verletzt das Modell (falsche Wagenmenge, unbekanntes Gleis)."""


# ------------------------------------------------------------------ Zug erzeugen
def generate(n: int, m: int, sizes: str, seed: int) -> list:
    """Zielgruppe je Wagen, ganzzahlig (SplitMix64). `gleich`: jeder Wagen gleichverteilt auf m Gruppen; `ungleich`: Gewicht der Gruppe i ist 2520 // (i + 1).
    Die Gruppennummern werden zufällig vertauscht, damit die Nummer nichts über die Größe verrät."""
    rng = SplitMix64(seed)
    perm = list(range(m))
    for i in range(m - 1, 0, -1):
        j = rng.below(i + 1)
        perm[i], perm[j] = perm[j], perm[i]
    weights = [1] * m if sizes == "gleich" else [C.ZIPF_BASE // (i + 1) for i in range(m)]
    total = sum(weights)
    out = []
    for _ in range(n):
        r = rng.below(total)
        g = 0
        acc = weights[0]
        while r >= acc:
            g += 1
            acc += weights[g]
        out.append(perm[g])
    return out


def present_groups(group_of) -> list:
    return sorted(set(group_of))


def group_sizes(group_of) -> dict:
    out = {}
    for g in group_of:
        out[g] = out.get(g, 0) + 1
    return out


# ------------------------------------------------------------------ ein Durchgang und der Prüfer
def run_pass(rest: list, keys: dict, k: int) -> list:
    """Verteilt die Wagen von `rest` (in Zugfolge) FIFO auf k Gleise; Rückgabe: Inhalt der Gleise."""
    if set(keys) != set(rest) or len(keys) != len(rest):
        raise ScheduleError("Jeder Wagen des Zuges muss genau einmal über den Berg.")
    tracks = [[] for _ in range(k)]
    for car in rest:
        t = keys[car]
        if not 0 <= t < k:
            raise ScheduleError(f"Gleis {t} gibt es nicht.")
        tracks[t].append(car)
    return tracks


def simulate(n: int, schedule: list, k: int) -> list:
    """Spielt den Plan Durchgang für Durchgang ab. Zustand nach jedem Durchgang: fertig abgezogene Gleise, Rest des Zuges, Gleisinhalte."""
    rest = list(range(n))
    finished: list = []
    states = []
    for p in schedule:
        tracks = run_pass(rest, p["keys"], k)
        fin = set(p["finish"])
        for t in sorted(fin):
            if tracks[t]:
                finished.append(tracks[t])
        rest = [c for t in range(k) if t not in fin for c in tracks[t]]
        states.append({"tracks": tracks, "finished": [list(b) for b in finished], "rest": list(rest), "moved": sum(len(x) for x in tracks)})
    return states


def arrangement(n: int, schedule: list, k: int) -> list:
    """Endgültige Wagenfolge: erst die fertig abgezogenen Gleise in Abzugsreihenfolge, dann der Rest."""
    states = simulate(n, schedule, k)
    if not states:
        return list(range(n))
    last = states[-1]
    return [c for block in last["finished"] for c in block] + last["rest"]


def is_grouped(order: list, group_of) -> bool:
    seen = set()
    prev = None
    for car in order:
        g = group_of[car]
        if g != prev:
            if g in seen:
                return False
            seen.add(g)
            prev = g
    return True


def valid_schedule(group_of, schedule: list, k: int) -> bool:
    """Unabhängiger Prüfer: Plan läuft im Modell, und die Endfolge hat jede Gruppe zusammenhängend."""
    try:
        order = arrangement(len(group_of), schedule, k)
    except ScheduleError:
        return False
    return sorted(order) == list(range(len(group_of))) and is_grouped(order, group_of)


def metrics(schedule: list) -> dict:
    return {"passes": len(schedule), "moves": sum(len(p["keys"]) for p in schedule)}


# ------------------------------------------------------------------ Verfahren
def radix_passes(m_eff: int, k: int) -> int:
    """Kleinstes d mit k**d >= m_eff (0 bei höchstens einer Gruppe), ganzzahlig."""
    if m_eff <= 1:
        return 0
    d, cap = 0, 1
    while cap < m_eff:
        cap *= k
        d += 1
    return d


def sequential_passes(m_eff: int, k: int) -> int:
    """ceil((m_eff - 1) / (k - 1)): je Durchgang k - 1 Gruppen fertig, im letzten Durchgang alle übrigen (höchstens k)."""
    if m_eff <= 1:
        return 0
    return -(-(m_eff - 1) // (k - 1))


def plan_sequential(group_of, k: int, order: str) -> list:
    """Gruppenweise: je Durchgang bekommen k - 1 Gruppen ein eigenes Gleis und sind fertig; alle anderen Wagen sammeln sich auf dem letzten Gleis und gehen wieder über den Berg.
    Im letzten Durchgang (höchstens k Gruppen übrig) bekommt jede Gruppe ein Gleis. `order`: `num` nach Gruppennummer, `size` größte Gruppe zuerst (bei Gleichstand kleinere Nummer)."""
    counts = group_sizes(group_of)
    ids = sorted(counts) if order == "num" else sorted(counts, key=lambda g: (-counts[g], g))
    rest = list(range(len(group_of)))
    schedule = []
    while len(ids) > 1:
        if len(ids) <= k:
            track = {g: i for i, g in enumerate(ids)}
            schedule.append({"keys": {c: track[group_of[c]] for c in rest}, "finish": tuple(range(len(ids)))})
            break
        take = ids[:k - 1]
        track = {g: i for i, g in enumerate(take)}
        keys = {c: track.get(group_of[c], k - 1) for c in rest}
        schedule.append({"keys": keys, "finish": tuple(range(k - 1))})
        rest = [c for c in rest if group_of[c] not in track]
        ids = ids[k - 1:]
    return schedule


def plan_radix(group_of, k: int) -> list:
    """Radix (LSD): die Gruppen werden der Nummer nach 0..m-1 durchgezählt; Durchgang j sortiert alle Wagen nach der j-ten Ziffer (Basis k, niedrigste zuerst).
    Nach d = radix_passes Durchgängen steht der Zug nach Gruppennummer sortiert, jeder Wagen wurde d-mal bewegt."""
    ids = present_groups(group_of)
    d = radix_passes(len(ids), k)
    rank = {g: i for i, g in enumerate(ids)}
    rest = list(range(len(group_of)))
    schedule = []
    for j in range(d):
        keys = {c: (rank[group_of[c]] // k ** j) % k for c in rest}
        last = j == d - 1
        schedule.append({"keys": keys, "finish": tuple(range(k)) if last else ()})
        tracks = run_pass(rest, keys, k)
        rest = [c for t in tracks for c in t]
    return schedule


def plan(group_of, k: int, method: str) -> list:
    if method == "seq_num":
        return plan_sequential(group_of, k, "num")
    if method == "seq_size":
        return plan_sequential(group_of, k, "size")
    if method == "radix":
        return plan_radix(group_of, k)
    raise ValueError(method)
