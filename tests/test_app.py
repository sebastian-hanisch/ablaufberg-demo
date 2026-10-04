"""AppTest-Rauchtests: Voreinstellung, jedes Preset, Randwerte, Würfel-Knopf, Permalink, Abschnitte, Exakt-Tab, Footer."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import abl_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(**state):
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def _metric(at, label):
    return next(m.value for m in at.metric if m.label == label)


def _has_metric(at, label):
    return any(m.label == label for m in at.metric)


def _texts(at):
    return [x.value for x in list(at.success) + list(at.info) + list(at.warning)]


def test_default_run_has_no_exception_and_shows_the_three_methods():
    at = _run()
    _ok(at)
    for key in C.METHODS:
        assert _has_metric(at, C.METHOD_LABELS[key]), key
    s = at.session_state
    assert s["n_select"] == C.DEFAULT_N and s["m_select"] == C.DEFAULT_M and s["k_select"] == C.DEFAULT_K and s["setup_slider"] == C.DEFAULT_SETUP and s["seed_input"] == C.DEFAULT_SEED
    assert any("Radix gewinnt mit 80 min" in t for t in _texts(at))
    assert any("8 Gruppen auf 4 Gleisen" in t for t in _texts(at))


@pytest.mark.parametrize("name", C.PRESET_ORDER)
def test_every_preset_button_runs_and_sets_the_controls(name):
    at = _run()
    next(b for b in at.button if b.key == f"preset_{name}").click().run()
    _ok(at)
    p = C.PRESETS[name]
    s = at.session_state
    assert (s["n_select"], s["m_select"], s["k_select"], s["sizes_select"], s["setup_slider"], s["seed_input"]) == (p["n"], p["m"], p["k"], p["sizes"], p["setup"], p["seed"])
    assert _has_metric(at, C.METHOD_LABELS["radix"])


def test_cheap_pass_preset_tells_the_other_story():
    at = _run()
    next(b for b in at.button if b.key == "preset_Billiger Durchgang").click().run()
    _ok(at)
    assert any("gruppenweise Abarbeiten gewinnt" in t for t in _texts(at))


@pytest.mark.parametrize("kw", [dict(n_select=20), dict(n_select=60), dict(m_select=4), dict(m_select=16), dict(k_select=2), dict(k_select=6), dict(sizes_select="ungleich"),
                                 dict(setup_slider=0), dict(setup_slider=60), dict(seed_input=C.SEED_MIN), dict(seed_input=C.SEED_MAX),
                                 dict(view_select="seq_num"), dict(view_select="seq_size"), dict(k_select=6, m_select=4)])
def test_extreme_settings_run(kw):
    _ok(_run(**kw))


def test_other_settings_change_the_result_and_the_text():
    std = _run()
    other = _run(m_select=16)
    assert _metric(std, C.METHOD_LABELS["radix"]) != _metric(other, C.METHOD_LABELS["radix"]) or _metric(std, C.METHOD_LABELS["seq_num"]) != _metric(other, C.METHOD_LABELS["seq_num"])
    cheap = _run(setup_slider=5)
    assert any("gewinnt mit 47 min" in t for t in _texts(cheap)) and any("Radix gewinnt" in t for t in _texts(std))


def test_dice_button_changes_the_seed_and_the_train():
    at = _run()
    old_seed = at.session_state["seed_input"]
    next(b for b in at.button if b.label == "🎲 Neuen Zug würfeln").click().run()
    _ok(at)
    assert at.session_state["seed_input"] != old_seed


def test_permalink_values_are_clamped_and_snapped():
    at = AppTest.from_file(APP, default_timeout=300)
    at.query_params["n"] = "33"
    at.query_params["m"] = "100"
    at.query_params["k"] = "5"
    at.query_params["sizes"] = "ungleich"
    at.query_params["setup"] = "23"
    at.query_params["seed"] = "99999"
    at.query_params["view"] = "seq_num"
    at.run()
    _ok(at)
    s = at.session_state
    assert s["n_select"] == 30 and s["m_select"] == 16 and s["k_select"] == 4 and s["sizes_select"] == "ungleich" and s["setup_slider"] == 25 and s["seed_input"] == C.SEED_MAX
    assert s["view_select"] == "seq_num"


def test_permalink_ignores_garbage_and_roundtrips():
    at = AppTest.from_file(APP, default_timeout=300)
    at.query_params["n"] = "viele"
    at.query_params["view"] = "unbekannt"
    at.query_params["sizes"] = "riesig"
    at.run()
    _ok(at)
    s = at.session_state
    assert s["n_select"] == C.DEFAULT_N and s["view_select"] == C.DEFAULT_VIEW and s["sizes_select"] == C.DEFAULT_SIZES
    next(b for b in at.button if b.key == "preset_Ungleiche Gruppen").click().run()
    qp = at.query_params
    at2 = AppTest.from_file(APP, default_timeout=300)
    for k in ("n", "m", "k", "sizes", "setup", "seed", "view"):
        v = qp[k]
        at2.query_params[k] = v[0] if isinstance(v, list) else v
    at2.run()
    _ok(at2)
    assert at2.session_state["sizes_select"] == "ungleich"


def test_sections_expanders_and_charts_are_present():
    at = _run()
    _ok(at)
    headers = [s.value for s in at.subheader] + [m.value for m in at.markdown]
    assert any("Was die Messreihe zeigt" in h for h in headers) and any("Zeit gegen Arbeit" in h for h in headers) and any("Zugfolge Durchgang für Durchgang" in h for h in headers)
    titles = [e.label for e in at.expander]
    assert "🔧 Wie wir das erreichen – vollständiger Methodenvergleich" in titles and "Wie funktioniert diese Demo?" in titles and "📐 Mathematische Formulierung" in titles
    assert [t.label for t in at.tabs] == ["⛰️ Verfahren", "🧮 Exakt (OR-Tools)", "📈 Messreihe"]
    assert len(at.get("plotly_chart")) == 7          # Bergzeit-Balken, Aufwand-Geraden, Zugfolge, vier Messreihen-Diagramme


def test_exact_tab_runs_cpsat_on_the_current_train():
    at = _run(n_select=20, m_select=12, k_select=3)
    _ok(at)
    next(b for b in at.button if b.key == "exact_button").click().run()
    _ok(at)
    assert _has_metric(at, "Mindestzahl") and _metric(at, "Status") == "bewiesen"
    assert len(at.get("plotly_chart")) == 8          # dazu die Zugfolge der exakten Lösung
    at.select_slider(key="n_select").set_value(30).run()
    assert not _has_metric(at, "Mindestzahl") and any("erneut lösen" in c.value for c in at.caption)


def test_seed_control_uses_the_portfolio_wording():
    assert [n.label for n in _run().number_input] == ["Zufalls-Seed"]


def test_related_demos_are_linked_and_footer_is_present():
    at = _run()
    text = " ".join(c.value for c in at.caption)
    for name in ("taktfahrplan-demo", "crew-pairing-demo", "streckenkonflikt-demo", "hofstellplatz-demo", "stapelplanung-demo"):
        assert name in text
    assert "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in text
    assert "geplant" not in text and "noch nicht" not in text
