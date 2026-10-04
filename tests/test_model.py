"""Kern von Hand gerechnet: Zug erzeugen, Gleise als Warteschlangen, ein Durchgang, die beiden Verfahren, Prüfer und Formeln.

Mini-Zug (5 Wagen, Gruppen 0,1,0,2,1) mit k = 2 Gleisen: Wagen 1 bis 5 liegen in der Folge 0..4, Gruppe je Wagen G = [0, 1, 0, 2, 1]."""
import pytest

import abl_constants as C
import abl_model as M

G = [0, 1, 0, 2, 1]


def test_generate_is_integer_frozen_and_deterministic():
    g = M.generate(12, 4, "gleich", 1)
    assert g == M.generate(12, 4, "gleich", 1) and len(g) == 12 and set(g) <= {0, 1, 2, 3}
    assert g != M.generate(12, 4, "gleich", 2)
    assert M.generate(12, 4, "gleich", 1) == [1, 0, 2, 0, 0, 2, 3, 0, 3, 2, 3, 2]
    assert M.generate(10, 5, "ungleich", 7) == [3, 3, 1, 4, 4, 0, 1, 3, 0, 4]


def test_group_labels_are_decoupled_from_sizes_in_unequal_groups():
    """Ohne Vertauschung wäre Gruppe 0 immer die größte; mit Vertauschung ist es über viele Seeds jede Gruppe etwa gleich oft."""
    biggest = [max(M.group_sizes(M.generate(40, 8, "ungleich", s)).items(), key=lambda kv: (kv[1], -kv[0]))[0] for s in range(300)]
    assert len(set(biggest)) == 8 and max(biggest.count(i) for i in range(8)) < 80


def test_unequal_sizes_follow_the_one_over_rank_weights():
    sizes = sorted(M.group_sizes(M.generate(6000, 6, "ungleich", 3)).values(), reverse=True)
    weights = [C.ZIPF_BASE // (i + 1) for i in range(6)]
    total = sum(weights)
    for got, w in zip(sizes, sorted(weights, reverse=True)):
        assert abs(got / 6000 - w / total) < 0.03
    equal = sorted(M.group_sizes(M.generate(6000, 6, "gleich", 3)).values())
    assert equal[-1] / 6000 - equal[0] / 6000 < 0.04


def test_a_pass_builds_fifo_tracks():
    tracks = M.run_pass([0, 1, 2, 3], {0: 1, 1: 0, 2: 1, 3: 0}, 2)
    assert tracks == [[1, 3], [0, 2]]
    with pytest.raises(M.ScheduleError):
        M.run_pass([0, 1], {0: 0}, 2)                                        # Wagen 1 fehlt
    with pytest.raises(M.ScheduleError):
        M.run_pass([0, 1], {0: 0, 1: 2}, 2)                                  # Gleis 2 gibt es bei k = 2 nicht
    with pytest.raises(M.ScheduleError):
        M.run_pass([0, 1], {0: 0, 1: 1, 5: 0}, 2)                            # fremder Wagen


def test_sequential_plan_by_hand():
    s = M.plan_sequential(G, 2, "num")
    assert [p["finish"] for p in s] == [(0,), (0, 1)]
    assert s[0]["keys"] == {0: 0, 1: 1, 2: 0, 3: 1, 4: 1}                      # Gruppe 0 fertig auf Gleis 1, der Rest sammelt sich auf Gleis 2
    assert s[1]["keys"] == {1: 0, 3: 1, 4: 0}                                  # nur der Rest geht wieder über den Berg
    assert M.arrangement(5, s, 2) == [0, 2, 1, 4, 3]
    assert M.metrics(s) == {"passes": 2, "moves": 8} and M.valid_schedule(G, s, 2)


def test_sequential_by_size_puts_the_largest_group_first():
    g = [0, 1, 1, 1, 2, 2]                                                      # Gruppe 1 hat 3 Wagen, Gruppe 2 hat 2, Gruppe 0 hat 1
    by_num = M.plan_sequential(g, 2, "num")
    by_size = M.plan_sequential(g, 2, "size")
    assert M.metrics(by_num) == {"passes": 2, "moves": 6 + 5} and M.metrics(by_size) == {"passes": 2, "moves": 6 + 3}
    assert by_size[0]["keys"][1] == 0 and by_num[0]["keys"][0] == 0              # größte Gruppe zuerst gegen Gruppe mit kleinster Nummer
    assert M.valid_schedule(g, by_num, 2) and M.valid_schedule(g, by_size, 2)


def test_radix_plan_by_hand():
    s = M.plan_radix(G, 2)
    assert [p["finish"] for p in s] == [(), (0, 1)]
    assert s[0]["keys"] == {0: 0, 1: 1, 2: 0, 3: 0, 4: 1}                      # niedrigste Ziffer der Gruppennummer 0, 1, 2 zur Basis 2
    assert s[1]["keys"] == {0: 0, 2: 0, 3: 1, 1: 0, 4: 0}                      # zweite Ziffer, Zugfolge nach Durchgang 1: 0, 2, 3, 1, 4
    assert M.arrangement(5, s, 2) == [0, 2, 1, 4, 3]
    assert M.metrics(s) == {"passes": 2, "moves": 10} and M.valid_schedule(G, s, 2)


def test_radix_with_absent_groups_renumbers_the_present_ones():
    g = [5, 9, 5, 9]                                                            # nur die Gruppen 5 und 9 sind da: ein Durchgang auf zwei Gleisen
    s = M.plan_radix(g, 2)
    assert len(s) == 1 and s[0]["keys"] == {0: 0, 1: 1, 2: 0, 3: 1} and M.valid_schedule(g, s, 2)


def test_a_train_that_is_already_grouped_needs_no_pass():
    for g in ([0, 0, 0], [3], [0, 0, 1, 1]):
        for method in C.METHODS:
            s = M.plan(g, 3, method)
            assert M.valid_schedule(g, s, 3)
    assert M.plan([4, 4, 4], 3, "radix") == [] and M.plan([4, 4, 4], 3, "seq_num") == []


def test_validator_rejects_broken_plans():
    good = M.plan_radix(G, 2)
    assert M.valid_schedule(G, good, 2)
    assert not M.valid_schedule(G, [], 2)                                        # Eingang ist nicht gruppiert
    assert not M.valid_schedule(G, [{"keys": {0: 0, 1: 1, 2: 1, 3: 0, 4: 0}, "finish": ()}], 2)   # ein Durchgang ohne Abziehen: Folge 0,3,4,1,2 hat Gruppe 0 zweimal getrennt
    wrong_group = [{"keys": {0: 0, 1: 1, 2: 1, 3: 0, 4: 1}, "finish": (0, 1)}]    # Gruppe 0 auf zwei Gleise verteilt
    assert not M.valid_schedule(G, wrong_group, 2)
    missing = [{"keys": {0: 0, 1: 1, 2: 0, 3: 1}, "finish": (0, 1)}]
    assert not M.valid_schedule(G, missing, 2)
    out_of_range = [{"keys": {0: 0, 1: 1, 2: 0, 3: 2, 4: 1}, "finish": (0, 1)}]
    assert not M.valid_schedule(G, out_of_range, 2)


def test_validator_accepts_split_groups_when_the_end_arrangement_is_grouped():
    """Eine Gruppe darf auf zwei benachbarte Gleise verteilt werden, wenn die Endfolge sie wieder zusammenhängend zeigt (Grund, warum die exakte Lösung Radix schlagen kann)."""
    g = [0, 1, 0, 1]
    split = [{"keys": {0: 0, 1: 0, 2: 1, 3: 1}, "finish": (0, 1)}]               # Gleis 1: Wagen 1, 2 / Gleis 2: Wagen 3, 4: Endfolge 0,1,0,1 nicht gruppiert
    assert not M.valid_schedule(g, split, 2)
    g3 = [0, 1, 1, 0]
    ok = [{"keys": {0: 1, 1: 0, 2: 0, 3: 1}, "finish": (0, 1)}]                  # Gleis 1 = Wagen 2, 3 (Gruppe 1), Gleis 2 = Wagen 1, 4 (Gruppe 0)
    assert M.valid_schedule(g3, ok, 2)
    g4 = [0, 1, 2, 3, 0, 1, 2, 3]                                               # vier Gruppen, drei Gleise, ein Durchgang: Gruppe 1 auf zwei Gleise geteilt
    one_pass = [{"keys": {0: 0, 4: 0, 5: 0, 1: 1, 2: 1, 6: 1, 3: 2, 7: 2}, "finish": (0, 1, 2)}]   # Gleis 1: Wagen 1, 5, 6 = 0,0,1; Gleis 2: Wagen 2, 3, 7 = 1,2,2; Gleis 3: Wagen 4, 8 = 3,3
    assert M.arrangement(8, one_pass, 3) == [0, 4, 5, 1, 2, 6, 3, 7] and M.valid_schedule(g4, one_pass, 3)
    assert M.plan_radix(g4, 3) != one_pass and len(M.plan_radix(g4, 3)) == 2                  # Radix braucht 2 Durchgänge


@pytest.mark.parametrize("m,k,expected", [(0, 2, 0), (1, 5, 0), (2, 2, 1), (3, 2, 2), (4, 2, 2), (5, 2, 3), (8, 2, 3), (9, 2, 4), (4, 4, 1), (5, 4, 2), (16, 4, 2), (17, 4, 3), (8, 6, 2)])
def test_radix_passes_formula_is_the_integer_logarithm(m, k, expected):
    assert M.radix_passes(m, k) == expected


@pytest.mark.parametrize("m,k,expected", [(1, 3, 0), (2, 2, 1), (3, 2, 2), (4, 2, 3), (3, 3, 1), (4, 3, 2), (5, 3, 2), (6, 3, 3), (8, 4, 3), (16, 4, 5), (10, 10, 1), (11, 10, 2)])
def test_sequential_passes_formula(m, k, expected):
    assert M.sequential_passes(m, k) == expected


def test_planners_match_their_formulas_and_are_valid_on_many_random_trains():
    for seed in range(60):
        for n, m, k, sizes in ((20, 5, 2, "gleich"), (30, 8, 3, "ungleich"), (25, 12, 4, "gleich"), (40, 16, 6, "ungleich")):
            g = M.generate(n, m, sizes, seed)
            me = len(M.present_groups(g))
            for method in C.METHODS:
                s = M.plan(g, k, method)
                assert M.valid_schedule(g, s, k), (seed, n, m, k, method)
            assert len(M.plan(g, k, "radix")) == M.radix_passes(me, k)
            assert len(M.plan(g, k, "seq_num")) == M.sequential_passes(me, k) == len(M.plan(g, k, "seq_size"))
            rad = M.metrics(M.plan(g, k, "radix"))
            assert rad["moves"] == n * M.radix_passes(me, k)
            assert M.metrics(M.plan(g, k, "seq_size"))["moves"] <= M.metrics(M.plan(g, k, "seq_num"))["moves"]      # größte zuerst minimiert die Summe der Restlängen


def test_sequential_moves_count_only_the_unfinished_cars():
    g = M.generate(40, 8, "gleich", 500)
    s = M.plan_sequential(g, 4, "num")
    sizes = M.group_sizes(g)
    ids = sorted(sizes)
    expected = len(g) + (len(g) - sum(sizes[x] for x in ids[:3])) + (len(g) - sum(sizes[x] for x in ids[:6]))
    assert M.metrics(s) == {"passes": 3, "moves": expected}


def test_unknown_method_is_rejected():
    with pytest.raises(ValueError):
        M.plan(G, 2, "zufall")
