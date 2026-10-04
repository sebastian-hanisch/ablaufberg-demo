"""Plotly-Figuren der Ablaufberg-Demo. Alle Achsen fest (fixedrange), damit Touch-Scrollen nicht am Chart hängen bleibt."""
from __future__ import annotations

import plotly.graph_objects as go

import abl_constants as C
import abl_evaluation as E
import abl_model as M

GAP = 1.5          # Lücke zwischen fertig abgezogenen Wagen und dem Rest des Zuges (in Wagenbreiten)


def _lock(fig, height=360, **layout):
    fig.update_layout(height=height, margin=dict(l=50, r=20, t=40, b=55), font=dict(size=12),
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0), **layout)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def train_rows(group_of, schedule: list, k: int) -> list:
    """Zeilen des Zugfolge-Bildes: (Beschriftung, Wagen in Folge, Zahl fertig abgezogener Wagen vorn, bewegte Wagen). Erste Zeile ist der Eingang."""
    n = len(group_of)
    rows = [("Eingang", list(range(n)), 0, None)]
    for j, st in enumerate(M.simulate(n, schedule, k), 1):
        done = [c for b in st["finished"] for c in b]
        rows.append((f"nach Durchgang {j}", done + st["rest"], len(done), st["moved"]))
    return rows


def build_train_strips(group_of, schedule: list, k: int) -> go.Figure:
    """Jede Zeile eine Zugfolge, jeder Wagen ein Quadrat in der Farbe seiner Zielgruppe; nach den Durchgängen stehen fertig abgezogene Wagen vorn (kleine Lücke dahinter)."""
    rows = train_rows(group_of, schedule, k)
    n = len(group_of)
    ids = M.present_groups(group_of)
    size = max(7, min(20, int(700 / max(n, 1))))
    fig = go.Figure()
    for g in ids:
        xs, ys, tx = [], [], []
        for r, (_label, order, ndone, _moved) in enumerate(rows):
            for pos, car in enumerate(order):
                if group_of[car] == g:
                    xs.append(pos + (GAP if pos >= ndone and ndone else 0))
                    ys.append(r)
                    tx.append(f"Wagen {car + 1}, Gruppe {g + 1}")
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", name=f"Gruppe {g + 1}", text=tx, hovertemplate="%{text}<extra></extra>",
                                 marker=dict(symbol="square", size=size, color=C.GROUP_COLORS[g % len(C.GROUP_COLORS)], line=dict(width=0))))
    for r, (_label, _order, _ndone, moved) in enumerate(rows):
        if moved is not None:
            fig.add_annotation(x=n + GAP + 1, y=r, text=f"{moved} bewegt", showarrow=False, xanchor="left", font=dict(size=11, color="#555"))
    fig.update_xaxes(visible=False, range=[-1, n + GAP + 9])
    fig.update_yaxes(tickvals=list(range(len(rows))), ticktext=[x[0] for x in rows], autorange="reversed", range=[len(rows) - 0.5, -0.5])
    return _lock(fig, 150 + 48 * len(rows), showlegend=len(ids) <= 16)


def build_time_bars(run: dict, setup: float) -> go.Figure:
    """Bergzeit je Verfahren, geteilt in den Aufwand der Durchgänge und die Abdrückzeit der bewegten Wagen."""
    fig = go.Figure()
    labels = [C.METHOD_LABELS[k] for k in C.METHODS]
    fig.add_trace(go.Bar(x=labels, y=[run["results"][k]["passes"] * setup for k in C.METHODS], name="Aufwand der Durchgänge", marker_color="#c77700",
                         hovertemplate="%{x}: %{y:.0f} min<extra>Aufwand der Durchgänge</extra>"))
    fig.add_trace(go.Bar(x=labels, y=[run["results"][k]["moves"] * C.CAR_MIN for k in C.METHODS], name="Abdrücken der Wagen", marker_color="#2a6fb0",
                         hovertemplate="%{x}: %{y:.0f} min<extra>Abdrücken der Wagen</extra>"))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Bergzeit (min)", rangemode="tozero")
    return _lock(fig, 340)


def build_setup_lines(run: dict, setup: float) -> go.Figure:
    """Bergzeit gegen den Aufwand je Durchgang: wo sich die Geraden schneiden, kippt die beste Wahl."""
    xs = list(range(C.SETUP_MIN, C.SETUP_MAX + 1, C.SETUP_STEP))
    fig = go.Figure()
    for key in C.METHODS:
        r = run["results"][key]
        fig.add_trace(go.Scatter(x=xs, y=[E.bergzeit(r["passes"], r["moves"], s) for s in xs], mode="lines", name=C.METHOD_LABELS[key],
                                 line=dict(color=C.METHOD_COLORS[key], width=3 if key == "radix" else 2.5, dash="solid" if key != "seq_num" else "dot"),
                                 hovertemplate="%{y:.0f} min bei %{x} min Aufwand<extra>" + C.METHOD_LABELS[key] + "</extra>"))
    fig.add_vline(x=setup, line_dash="dash", line_color="#555")
    fig.update_xaxes(title_text="Aufwand je Durchgang (min)", range=[C.SETUP_MIN, C.SETUP_MAX])
    fig.update_yaxes(title_text="Bergzeit (min)", rangemode="tozero")
    return _lock(fig, 340)


def build_sweep_passes(rows: list) -> go.Figure:
    """Messreihe: mittlere Durchgänge je Variante (gruppenweise nach Nummer, Radix, exakt)."""
    fig = go.Figure()
    names = [r["name"] for r in rows]
    for key, col in (("seq_num", "seq_num"), ("radix", "radix")):
        fig.add_trace(go.Bar(x=names, y=[r[f"passes_{col}"] for r in rows], name=C.METHOD_LABELS[key], marker_color=C.METHOD_COLORS[key]))
    fig.add_trace(go.Bar(x=names, y=[r["passes_exact"] for r in rows], name=C.METHOD_LABELS["exact"], marker_color=C.METHOD_COLORS["exact"]))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Durchgänge (Mittel)", rangemode="tozero")
    return _lock(fig, 380)


def build_sweep_moves(rows: list) -> go.Figure:
    """Messreihe: Wagenbewegungen je Wagen (jeder Wagen im Mittel so oft über den Berg)."""
    fig = go.Figure()
    names = [r["name"] for r in rows]
    for key in C.METHODS:
        fig.add_trace(go.Bar(x=names, y=[r[f"permove_{key}"] for r in rows], name=C.METHOD_LABELS[key], marker_color=C.METHOD_COLORS[key]))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Bewegungen je Wagen (Mittel)", rangemode="tozero")
    return _lock(fig, 380)


def build_length_series(rows: list) -> go.Figure:
    """Messreihe nach Zuglänge: in wie vielen Zügen braucht die exakte Lösung weniger Durchgänge als Radix?"""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[r["name"] for r in rows], y=[100 * r["exact_better_share"] for r in rows], marker_color=C.METHOD_COLORS["exact"],
                         text=[f"{100 * r['exact_better_share']:.0f} %" for r in rows], textposition="outside", name="exakt besser als Radix",
                         hovertemplate="%{x}: %{y:.0f} % der Züge<extra></extra>"))
    fig.update_yaxes(title_text="Züge mit weniger Durchgängen als Radix (%)", range=[0, 110])
    return _lock(fig, 340, showlegend=False)


def build_better_share(rows: list) -> go.Figure:
    """Messreihe: je Variante der Anteil der Züge, in denen die exakte Lösung weniger Durchgänge braucht als Radix."""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[r["name"] for r in rows], y=[100 * r["exact_better_share"] for r in rows], marker_color=C.METHOD_COLORS["exact"], name="exakt besser als Radix",
                         hovertemplate="%{x}: %{y:.0f} % der Züge<extra></extra>"))
    fig.update_yaxes(title_text="Züge mit weniger Durchgängen als Radix (%)", range=[0, 105])
    return _lock(fig, 360, showlegend=False)
