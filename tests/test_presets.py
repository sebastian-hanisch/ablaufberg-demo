"""Permalink-Einrasten, Presets und Konstanten-Konsistenz."""
import abl_constants as C
import abl_presets as PR
import abl_results as R


def test_snap_rounds_to_the_nearest_option_and_prefers_the_smaller_on_ties():
    assert PR.snap(C.N_OPTIONS, 25) == 20 and PR.snap(C.N_OPTIONS, 35) == 30 and PR.snap(C.N_OPTIONS, 99) == 60 and PR.snap(C.N_OPTIONS, 0) == 20
    assert PR.snap(C.K_OPTIONS, 5) == 4 and PR.snap(C.K_OPTIONS, 1) == 2 and PR.snap(C.M_OPTIONS, 10) == 8


def test_snap_step_clamps_and_rounds_half_down():
    assert PR.snap_step(22, 0, 60, 5) == 20 and PR.snap_step(23, 0, 60, 5) == 25 and PR.snap_step(100, 0, 60, 5) == 60 and PR.snap_step(-4, 0, 60, 5) == 0
    assert PR.snap_step(27, 0, 60, 5) == 25 and PR.snap_step(28, 0, 60, 5) == 30 and PR.snap_step(25, 0, 60, 5) == 25
    assert PR.snap_step(7, 5, 60, 10) == 5 and PR.snap_step(10, 5, 60, 10) == 5 and PR.snap_step(11, 5, 60, 10) == 15       # 10 liegt genau zwischen 5 und 15: der kleinere gewinnt


def test_every_preset_sets_every_control_with_valid_values():
    assert set(C.PRESET_ORDER) == set(C.PRESETS) == set(C.PRESET_HELP) and len(C.PRESET_ORDER) == 6
    for name, p in C.PRESETS.items():
        assert set(p) == set(PR.PRESET_KEYS)
        assert p["n"] in C.N_OPTIONS and p["m"] in C.M_OPTIONS and p["k"] in C.K_OPTIONS and p["sizes"] in C.SIZE_OPTIONS
        assert C.SETUP_MIN <= p["setup"] <= C.SETUP_MAX and p["setup"] % C.SETUP_STEP == 0
        assert C.SEED_MIN <= p["seed"] <= C.SEED_MAX and not (C.SWEEP_SEEDS.start <= p["seed"] < C.SWEEP_SEEDS.stop), name


def test_each_non_standard_preset_changes_the_levers_it_is_named_for():
    std = C.PRESETS["Standard"]
    changed = {n: sorted(k for k in std if k != "seed" and C.PRESETS[n][k] != std[k]) for n in C.PRESET_ORDER if n != "Standard"}
    assert changed == {"Viele Gruppen": ["m"], "Wenige Gleise": ["k"], "Ungleiche Gruppen": ["sizes"], "Billiger Durchgang": ["setup"], "Gruppen teilen": ["k", "m"]}
    assert len({p["seed"] for p in C.PRESETS.values()}) == 1 and std["seed"] == C.DEFAULT_SEED


def test_presets_with_a_sweep_variant_match_it():
    names = {n: R.variant_name({k: C.PRESETS[n][k] for k in ("n", "m", "k", "sizes")}) for n in C.PRESET_ORDER}
    assert names["Standard"] == "Standard (40 Wagen)" and names["Viele Gruppen"] == "16 Gruppen" and names["Wenige Gleise"] == "2 Gleise"
    assert names["Ungleiche Gruppen"] == "Ungleiche Gruppen" and names["Billiger Durchgang"] == "Standard (40 Wagen)" and names["Gruppen teilen"] == "12 Gruppen, 3 Gleise"


def test_view_options_are_the_methods_and_settings_convert():
    assert tuple(C.VIEW_OPTIONS) == tuple(C.METHODS) and set(C.METHOD_LABELS) >= set(C.METHODS) and set(C.METHOD_COLORS) == set(C.METHOD_LABELS)
    s = PR.settings_from_state({"n_select": 40, "m_select": 8, "k_select": 4, "sizes_select": "gleich", "setup_slider": 20, "seed_input": 500.0})
    assert s == {"n": 40, "m": 8, "k": 4, "sizes": "gleich", "setup": 20, "seed": 500}


def test_group_colors_cover_the_largest_group_count():
    assert len(set(C.GROUP_COLORS)) == len(C.GROUP_COLORS) >= max(C.M_OPTIONS)
