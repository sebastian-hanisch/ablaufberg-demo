"""Feste Annahmen, Regler-Stufen, Presets und Farben der Ablaufberg-Demo (eine Wahrheitsquelle)."""

# ------------------------------------------------------------------ Annahmen
CAR_MIN = 0.5               # Abdrückzeit je Wagen über den Berg (min), feste Annahme; der Aufwand je Durchgang ist ein Regler
ZIPF_BASE = 2520            # ungleiche Gruppengrößen: Gewicht der Gruppe i = 2520 // (i + 1), ganzzahlig (2520 = kgV(1..10))
EXACT_TIME_LIMIT = 90.0     # Sekunden je CP-SAT-Entscheidung im Exakt-Tab
EXACT_TIME_LIMIT_SWEEP = 120.0

# ------------------------------------------------------------------ Regler
N_OPTIONS = (20, 30, 40, 60)        # Wagen im ankommenden Zug
DEFAULT_N = 40
M_OPTIONS = (4, 8, 12, 16)          # Zielgruppen (Abfahrtszüge)
DEFAULT_M = 8
K_OPTIONS = (2, 3, 4, 6)            # Richtungsgleise
DEFAULT_K = 4
SIZE_OPTIONS = ("gleich", "ungleich")
SIZE_LABELS = {"gleich": "gleich groß", "ungleich": "ungleich groß (wenige große, viele kleine)"}
DEFAULT_SIZES = "gleich"
SETUP_MIN, SETUP_MAX, SETUP_STEP = 0, 60, 5   # Aufwand je Durchgang (min)
DEFAULT_SETUP = 20
SEED_MIN, SEED_MAX = 0, 9999
DEFAULT_SEED = 500
METHODS = ("seq_num", "seq_size", "radix")
VIEW_OPTIONS = METHODS
DEFAULT_VIEW = "radix"
METHOD_LABELS = {"seq_num": "Gruppenweise (nach Nummer)", "seq_size": "Gruppenweise (größte zuerst)", "radix": "Radix (alle Gruppen gleichzeitig)", "exact": "Exakt (CP-SAT)"}
METHOD_COLORS = {"seq_num": "#7d8898", "seq_size": "#c77700", "radix": "#2a6fb0", "exact": "#2e7d4f"}
GROUP_COLORS = (
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
    "#bcbd22", "#17becf", "#393b79", "#ad494a", "#637939", "#8c6d31", "#843c39", "#5254a3",
)

# ------------------------------------------------------------------ Messreihe
RESULTS_FILE = "data/abl_results.json"
SWEEP_SEEDS = range(100, 120)
SWEEP_VARIANTS = (          # Name -> (Wagen, Gruppen, Gleise, Gruppengrößen)
    ("Standard (40 Wagen)", 40, 8, 4, "gleich"),
    ("8 Wagen", 8, 6, 3, "gleich"),
    ("12 Wagen", 12, 6, 3, "gleich"),
    ("20 Wagen", 20, 6, 3, "gleich"),
    ("30 Wagen", 30, 6, 3, "gleich"),
    ("40 Wagen, 6 Gruppen", 40, 6, 3, "gleich"),
    ("60 Wagen", 60, 8, 4, "gleich"),
    ("4 Gruppen", 40, 4, 4, "gleich"),
    ("12 Gruppen", 40, 12, 4, "gleich"),
    ("16 Gruppen", 40, 16, 4, "gleich"),
    ("2 Gleise", 40, 8, 2, "gleich"),
    ("3 Gleise", 40, 8, 3, "gleich"),
    ("6 Gleise", 40, 8, 6, "gleich"),
    ("Ungleiche Gruppen", 40, 8, 4, "ungleich"),
    ("12 Gruppen, 3 Gleise", 40, 12, 3, "gleich"),
    ("16 Gruppen, 3 Gleise", 40, 16, 3, "gleich"),
    ("12 Gruppen, 6 Gleise", 40, 12, 6, "gleich"),
    ("12 Gruppen, 2 Gleise", 40, 12, 2, "gleich"),
)
LENGTH_SERIES = ("8 Wagen", "12 Wagen", "20 Wagen", "30 Wagen", "40 Wagen, 6 Gruppen")   # gleiche Gruppen und Gleise (6 Gruppen, 3 Gleise), nur die Zuglänge wächst

# ------------------------------------------------------------------ Presets (Seeds liegen außerhalb der Messreihen-Seeds)
PRESET_ORDER = ["Standard", "Viele Gruppen", "Wenige Gleise", "Ungleiche Gruppen", "Billiger Durchgang", "Gruppen teilen"]
PRESETS = {
    "Standard": {"n": 40, "m": 8, "k": 4, "sizes": "gleich", "setup": 20, "seed": 500},
    "Viele Gruppen": {"n": 40, "m": 16, "k": 4, "sizes": "gleich", "setup": 20, "seed": 500},
    "Wenige Gleise": {"n": 40, "m": 8, "k": 2, "sizes": "gleich", "setup": 20, "seed": 500},
    "Ungleiche Gruppen": {"n": 40, "m": 8, "k": 4, "sizes": "ungleich", "setup": 20, "seed": 500},
    "Billiger Durchgang": {"n": 40, "m": 8, "k": 4, "sizes": "gleich", "setup": 5, "seed": 500},
    "Gruppen teilen": {"n": 40, "m": 12, "k": 3, "sizes": "gleich", "setup": 20, "seed": 500},
}
PRESET_HELP = {
    "Standard": "40 Wagen für 8 Abfahrtszüge, 4 Richtungsgleise, 20 min Aufwand je Durchgang: der Grundfall.",
    "Viele Gruppen": "16 statt 8 Abfahrtszüge: gruppenweises Abarbeiten braucht viele Durchgänge, Radix kaum mehr.",
    "Wenige Gleise": "Nur 2 Richtungsgleise: jede Stufe teilt nur in zwei, Radix braucht mehr Durchgänge, gruppenweise noch viel mehr.",
    "Ungleiche Gruppen": "Wenige große und viele kleine Gruppen: wer die großen Gruppen zuerst fertigstellt, bewegt weniger Wagen.",
    "Billiger Durchgang": "Nur 5 min Aufwand je Durchgang: jetzt zählt vor allem die Zahl bewegter Wagen, und das gruppenweise Abarbeiten gewinnt.",
    "Gruppen teilen": "12 Gruppen auf 3 Gleisen: Radix braucht 3 Durchgänge, die exakte Lösung (Exakt-Tab) schafft es mit 2: Radix ist nicht immer das Minimum.",
}


def fmt_min(x, digits=0):
    return f"{x:.{digits}f} min"
