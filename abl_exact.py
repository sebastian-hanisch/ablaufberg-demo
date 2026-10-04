"""Exakte Mindestzahl an Durchgängen (CP-SAT): geht das Gruppieren in P Durchgängen?

Relationales Modell: vor[p][a][b] = Wagen a steht nach Durchgang p vor Wagen b. Durchgang p gibt jedem Wagen einen Gleisschlüssel in 0..k-1; die Gleise werden in Schlüssel-
reihenfolge zusammengezogen, innerhalb eines Gleises bleibt die Reihenfolge (FIFO):
    vor[p][a][b]  <=>  key[a] < key[b]  oder  (key[a] == key[b]  und  vor[p-1][a][b])
Ziel: je Gruppe liegt kein fremder Wagen zwischen zwei Wagen der Gruppe. In diesem Modell werden in jedem Durchgang alle Wagen bewegt (Plan hat `finish` erst im letzten Durchgang).
Die Radix-Durchgangszahl ist eine zulässige Obergrenze, also werden nur P = 1 .. radix - 1 geprüft."""
from __future__ import annotations

import itertools
import time

from ortools.sat.python import cp_model

import abl_constants as C
import abl_model as M


def _feasible(group_of, k: int, passes: int, limit: float, workers: int):
    """Rückgabe (Status, Plan): Status True = gefunden, False = bewiesen unmöglich, None = Zeitlimit."""
    n = len(group_of)
    model = cp_model.CpModel()
    prev = None                                                   # None = Ausgangsfolge (a vor b für a < b)
    keys_all = []
    for _p in range(passes):
        key = [model.NewIntVar(0, k - 1, "") for _ in range(n)]
        keys_all.append(key)
        cur = {}
        for a in range(n):
            for b in range(a + 1, n):
                lt, gt, eq = model.NewBoolVar(""), model.NewBoolVar(""), model.NewBoolVar("")
                model.Add(key[a] < key[b]).OnlyEnforceIf(lt)
                model.Add(key[a] > key[b]).OnlyEnforceIf(gt)
                model.Add(key[a] == key[b]).OnlyEnforceIf(eq)
                model.AddExactlyOne([lt, gt, eq])
                v = model.NewBoolVar("")
                model.Add(v == 1).OnlyEnforceIf(lt)
                model.Add(v == 0).OnlyEnforceIf(gt)
                if prev is None:
                    model.Add(v == 1).OnlyEnforceIf(eq)
                else:
                    model.Add(v == prev[(a, b)]).OnlyEnforceIf(eq)
                cur[(a, b)] = v
        prev = cur

    def before(a, b):
        return prev[(a, b)] if a < b else prev[(b, a)].Not()

    members: dict = {}
    for car, g in enumerate(group_of):
        members.setdefault(g, []).append(car)
    for g, mem in members.items():
        others = [x for x in range(n) if group_of[x] != g]
        for a, b in itertools.permutations(mem, 2):
            for x in others:
                model.AddBoolOr([before(a, x).Not(), before(x, b).Not(), before(a, b).Not()])    # a vor x vor b ist verboten
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = limit
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = 1
    status = solver.Solve(model)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule = []
        for p, key in enumerate(keys_all):
            schedule.append({"keys": {c: solver.Value(key[c]) for c in range(n)}, "finish": tuple(range(k)) if p == passes - 1 else ()})
        return True, schedule
    return (False if status == cp_model.INFEASIBLE else None), None


def min_passes(group_of, k: int, limit: float = C.EXACT_TIME_LIMIT, workers: int = 4) -> dict:
    """Kleinste Zahl Durchgänge. `proven`: alle kleineren Zahlen sind bewiesen unmöglich (oder das Radix-Ergebnis ist bewiesen nicht zu unterbieten)."""
    t0 = time.time()
    m_eff = len(M.present_groups(group_of))
    rad = M.radix_passes(m_eff, k)
    if M.is_grouped(list(range(len(group_of))), group_of):         # schon zusammenhängend: kein Durchgang nötig
        return {"passes": 0, "proven": True, "status": "OPTIMAL", "schedule": [], "time": time.time() - t0, "radix": rad}
    proven = True
    for p in range(1, rad):
        ok, schedule = _feasible(group_of, k, p, limit, workers)
        if ok:
            return {"passes": p, "proven": proven, "status": "OPTIMAL" if proven else "Zeitlimit", "schedule": schedule, "time": time.time() - t0, "radix": rad}
        if ok is None:
            proven = False                                        # p war nicht entschieden; ein größeres p kann trotzdem gefunden werden
    return {"passes": rad, "proven": proven, "status": "OPTIMAL" if proven else "Zeitlimit", "schedule": M.plan_radix(group_of, k), "time": time.time() - t0, "radix": rad}
