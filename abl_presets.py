"""SETTING_SPECS-Permalink-Muster, Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio).
Alle Regler sind immer sichtbar mit festen Grenzen - kein ausblendbarer Regler, kein KEPT-Muster."""

import random
from dataclasses import dataclass

import streamlit as st

import abl_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    options: tuple | None = None
    lo: int | None = None
    hi: int | None = None


SETTING_SPECS = {
    "n_select": SettingSpec("n", int, C.DEFAULT_N, C.N_OPTIONS),
    "m_select": SettingSpec("m", int, C.DEFAULT_M, C.M_OPTIONS),
    "k_select": SettingSpec("k", int, C.DEFAULT_K, C.K_OPTIONS),
    "sizes_select": SettingSpec("sizes", str, C.DEFAULT_SIZES, C.SIZE_OPTIONS),
    "setup_slider": SettingSpec("setup", int, C.DEFAULT_SETUP, None, C.SETUP_MIN, C.SETUP_MAX),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, None, C.SEED_MIN, C.SEED_MAX),
    "view_select": SettingSpec("view", str, C.DEFAULT_VIEW, C.VIEW_OPTIONS),
}
PRESET_KEYS = {"n": "n_select", "m": "m_select", "k": "k_select", "sizes": "sizes_select", "setup": "setup_slider", "seed": "seed_input"}


def snap(options, value):
    """Nächste Stufe (bei Gleichstand die kleinere)."""
    return min(options, key=lambda o: (abs(o - value), o))


def snap_step(value, lo, hi, step):
    """Auf das Raster lo, lo + step, ... innerhalb [lo, hi] einrasten (bei Gleichstand der kleinere Wert)."""
    q, r = divmod(max(lo, min(hi, value)) - lo, step)
    return lo + step * (q + (1 if 2 * r > step else 0))


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
                if spec.caster is str:
                    if value not in spec.options:
                        continue
                elif spec.options is not None:
                    value = snap(spec.options, value)
                elif state_key == "setup_slider":
                    value = snap_step(value, spec.lo, spec.hi, C.SETUP_STEP)
                else:
                    value = max(spec.lo, min(spec.hi, value))
                st.session_state[state_key] = value
            except (ValueError, TypeError):
                pass
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        st.session_state[state_key] = C.PRESETS[name][key]


def randomize_seed():
    st.session_state["seed_input"] = random.randint(C.SEED_MIN, C.SEED_MAX)


def settings_from_state(values: dict) -> dict:
    return {"n": int(values["n_select"]), "m": int(values["m_select"]), "k": int(values["k_select"]), "sizes": str(values["sizes_select"]),
            "setup": int(values["setup_slider"]), "seed": int(values["seed_input"])}
