"""Orakel (Breitensuche über alle Gleisverteilungen, ohne Modellfunktionen der Demo) gegen die Verfahren der Demo auf kleinen Zufallszügen."""
import abl_constants as C
import abl_model as M
from oracle_bfs import grouped, oracle_min_passes


def test_no_method_beats_the_brute_force_minimum_and_every_plan_is_a_feasible_path():
    for seed in range(40):
        for n, m, k in ((7, 4, 2), (7, 5, 3), (6, 6, 2)):
            g = M.generate(n, m, "gleich", seed)
            best = oracle_min_passes(g, k)
            for method in C.METHODS:
                s = M.plan(g, k, method)
                assert best <= len(s) or grouped(g), (seed, n, m, k, method)
                assert M.valid_schedule(g, s, k)


def test_orakel_agrees_with_the_radix_count_when_groups_fit_one_pass():
    for seed in range(30):
        g = M.generate(7, 3, "gleich", seed)
        if grouped(g):
            continue
        assert oracle_min_passes(g, 3) == 1 == M.radix_passes(len(set(g)), 3)
