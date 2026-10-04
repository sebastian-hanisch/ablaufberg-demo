"""Exakte Rechnung gegen das unabhängige Breitensuche-Orakel (tests/oracle_bfs.py) auf kleinen Zügen, Zweige des Wrappers, Prüfer-Abnahme."""
import itertools

import pytest

import abl_exact as X
import abl_model as M
from oracle_bfs import oracle_min_passes


def all_sequences(n, m):
    return itertools.product(range(m), repeat=n)


def test_oracle_on_hand_examples():
    assert oracle_min_passes([0, 0, 1, 1], 2) == 0
    assert oracle_min_passes([0, 1, 0, 1], 2) == 1                                  # Gruppe 0 aufs eine, Gruppe 1 aufs andere Gleis
    assert oracle_min_passes([0, 1, 2, 0, 1, 2], 2) == 1                            # Gruppe 1 geteilt: Gleis 2 = 0,0,1, Gleis 1 = 1,2,2 (Gleis 2 zuerst abgezogen)
    assert oracle_min_passes([0, 1, 2, 3, 0, 1, 2, 3], 3) == 1                      # vier Gruppen auf drei Gleisen: Gleise 0,0,1 | 1,2,2 | 3,3 (siehe test_model)
    assert oracle_min_passes([0, 1, 2, 3, 0, 1, 2, 3], 2) == 2


@pytest.mark.parametrize("n,m,k", [(6, 3, 2), (6, 3, 3), (6, 4, 2), (6, 4, 3), (7, 3, 2)])
def test_cpsat_agrees_with_brute_force_on_every_small_train(n, m, k):
    """Alle m^n Folgen (bei n = 6, m = 3: 729) bis auf jede 2. bei den größeren; die Zahl der Durchgänge stimmt mit dem Orakel überein."""
    step = 1 if m ** n <= 800 else 3
    for idx, seq in enumerate(all_sequences(n, m)):
        if idx % step:
            continue
        if len(set(seq)) <= 1:
            continue
        r = X.min_passes(list(seq), k, 30.0, workers=1)
        assert r["proven"] and r["passes"] == oracle_min_passes(seq, k), (seq, k, r["passes"])
        assert M.valid_schedule(list(seq), r["schedule"], k), seq


def test_cpsat_finds_the_improvement_that_radix_misses():
    """k = 2, 5 Gruppen: Radix braucht 3 Durchgänge, hier genügen 2 (Gruppen teilen sich Gleise); das Orakel bestätigt es."""
    seq = [0, 1, 2, 3, 4, 0, 1, 2]
    r = X.min_passes(seq, 2, 30.0, workers=1)
    assert r["radix"] == 3 and r["passes"] == oracle_min_passes(seq, 2) < 3
    assert r["proven"] and M.valid_schedule(seq, r["schedule"], 2)


def test_radix_is_returned_when_nothing_beats_it():
    seq = [0, 1, 2, 3, 0, 1, 2, 3]
    r = X.min_passes(seq, 2, 30.0, workers=1)
    assert r["passes"] == r["radix"] == 2 and r["proven"] and r["schedule"] == M.plan_radix(seq, 2)


def test_trains_with_at_most_k_groups_need_one_pass_and_no_search():
    seq = [2, 0, 1, 0, 2, 1]
    r = X.min_passes(seq, 3, 30.0, workers=1)
    assert r["passes"] == 1 == r["radix"] and r["proven"] and M.valid_schedule(seq, r["schedule"], 3)


def test_a_train_with_one_group_needs_no_pass():
    r = X.min_passes([4, 4, 4], 2, 30.0, workers=1)
    assert r["passes"] == 0 and r["schedule"] == [] and r["proven"]


def test_an_already_grouped_train_needs_no_pass_although_radix_would_run():
    seq = [0, 0, 1, 1, 2, 2, 3, 3]
    r = X.min_passes(seq, 2, 30.0, workers=1)
    assert r["passes"] == 0 and r["radix"] == 2 and r["proven"] and r["schedule"] == [] and M.valid_schedule(seq, [], 2)


def test_undecided_questions_leave_the_result_unproven(monkeypatch):
    seq = [0, 1, 2, 3, 4, 0, 1, 2]
    monkeypatch.setattr(X, "_feasible", lambda *a, **kw: (None, None))
    r = X.min_passes(seq, 2, 0.01, workers=1)
    assert not r["proven"] and r["status"] == "Zeitlimit" and r["passes"] == r["radix"] == 3 and M.valid_schedule(seq, r["schedule"], 2)


def test_a_later_solution_after_an_undecided_question_is_not_proven_optimal(monkeypatch):
    seq = [0, 1, 2, 3, 4, 0, 1, 2]
    real = X._feasible

    def fake(group_of, k, passes, limit, workers):
        return (None, None) if passes == 1 else real(group_of, k, passes, limit, workers)
    monkeypatch.setattr(X, "_feasible", fake)
    r = X.min_passes(seq, 2, 30.0, workers=1)
    assert r["passes"] == 2 and not r["proven"] and r["status"] == "Zeitlimit" and M.valid_schedule(seq, r["schedule"], 2)


def test_exact_schedule_moves_every_car_in_every_pass_and_finishes_in_the_last():
    seq = [0, 1, 2, 3, 4, 0, 1, 2]
    r = X.min_passes(seq, 2, 30.0, workers=1)
    assert [len(p["keys"]) for p in r["schedule"]] == [len(seq)] * r["passes"]
    assert [p["finish"] for p in r["schedule"]] == [()] * (r["passes"] - 1) + [(0, 1)]


def test_a_time_limit_that_is_too_short_leaves_the_question_undecided():
    g = M.generate(60, 12, "gleich", 3)
    ok, schedule = X._feasible(g, 3, 1, 0.001, 1)
    assert ok is None and schedule is None


def test_infeasible_and_feasible_questions_are_decided():
    assert X._feasible([0, 1, 2, 0, 1, 2], 2, 1, 10.0, 1)[0] is True
    ok, schedule = X._feasible([0, 1, 2, 3, 0, 1, 2, 3], 2, 1, 10.0, 1)
    assert ok is False and schedule is None
