"""Unabhängiges Orakel: Mindestzahl Durchgänge durch Breitensuche über ALLE Gleisverteilungen (itertools.product), ohne CP-SAT und ohne die Modellfunktionen der Demo.

Zustand = Folge der Gruppennummern. Ein Durchgang wählt für jede Position ein Gleis 0..k-1 und zieht die Gleise in Gleisreihenfolge zusammen (innerhalb eines Gleises bleibt die
Reihenfolge). Ziel: jede Gruppe zusammenhängend."""
import itertools


def grouped(seq) -> bool:
    seen = set()
    prev = None
    for g in seq:
        if g != prev:
            if g in seen:
                return False
            seen.add(g)
            prev = g
    return True


def oracle_min_passes(seq, k: int, limit: int = 6) -> int:
    seq = tuple(seq)
    if grouped(seq):
        return 0
    frontier = {seq}
    seen = {seq}
    for depth in range(1, limit + 1):
        nxt = set()
        for s in frontier:
            for assign in itertools.product(range(k), repeat=len(s)):
                new = tuple(s[i] for t in range(k) for i in range(len(s)) if assign[i] == t)
                if new in seen:
                    continue
                if grouped(new):
                    return depth
                seen.add(new)
                nxt.add(new)
        frontier = nxt
    raise AssertionError("Orakel: Grenze erreicht")
