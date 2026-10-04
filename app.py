"""Ablaufberg: Wie viele Durchgänge braucht die Zugbildung? - interaktive Fall-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Vierter Baustein der Reihe Bahn/Schienenverkehr: Ein Güterzug rollt über den Ablaufberg auf Richtungsgleise und soll in Abfahrtszüge sortiert werden. Die Demo vergleicht das
gruppenweise Abarbeiten mit Radix, rechnet die exakte Mindestzahl an Durchgängen mit CP-SAT und fragt, was ein Durchgang kosten darf.

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import abl_constants as C
import abl_exact as X
import abl_model as M
import abl_results as R
from abl_evaluation import exact_message, passes_message, run_live, time_message, times
from abl_pdf_export import generate_plan_pdf
from abl_presets import (apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, settings_from_state,
                         sync_query_params)
from abl_visualization import (build_better_share, build_length_series, build_setup_lines, build_sweep_moves, build_sweep_passes, build_time_bars,
                               build_train_strips)

st.set_page_config(page_title="Ablaufberg – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _results():
    return R.load_results()


@st.cache_data(show_spinner=False)
def _live(n, m, k, sizes, seed):
    return run_live({"n": n, "m": m, "k": k, "sizes": sizes, "seed": seed})


st.title("🚂 Ablaufberg: Wie viele Durchgänge braucht die Zugbildung?")
st.markdown(
    """
Ein Güterzug rollt über den **Ablaufberg** auf **Richtungsgleise**; jeder Wagen gehört zu einem **Abfahrtszug** (seiner Zielgruppe). Weil es weniger Gleise als Gruppen geben kann, muss der Zug **mehrfach**
über den Berg: **Gruppenweise** werden jedes Mal ein paar Gruppen fertig, bei **Radix** wird alles gleichzeitig nach und nach sortiert. Die Demo zeigt, wie viele **Durchgänge** jedes Verfahren braucht, ob
eine **exakte Lösung** (OR-Tools CP-SAT) weniger schafft, und was **ein Durchgang kosten darf**, bevor sich die Wahl umdreht.
"""
)
st.caption(
    "Vierter Baustein der Reihe Bahn/Schienenverkehr nach [Taktfahrplan](https://sebastianhanisch-taktfahrplan-demo.streamlit.app/), "
    "[Crew Pairing](https://sebastianhanisch-crew-pairing-demo.streamlit.app/) und [Trassenkonflikt](https://sebastianhanisch-streckenkonflikt-demo.streamlit.app/). "
    "Anders als das Abstellen auf LIFO-Plätzen in [hofstellplatz-demo](https://sebastianhanisch-hofstellplatz-demo.streamlit.app/) und "
    "[stapelplanung-demo](https://sebastianhanisch-stapelplanung-demo.streamlit.app/) sind die Gleise hier Warteschlangen (wer zuerst rollt, steht vorn), die Aufgabe ist das Sortieren."
)

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_cols = st.columns(3)
for i, name in enumerate(C.PRESET_ORDER):
    with preset_cols[i % 3]:
        st.button(name, key=f"preset_{name}", width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name])

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.select_slider("Wagen im Zug", options=C.N_OPTIONS, key="n_select", help="Länge des ankommenden Zuges. Die exakte Rechnung wächst mit der Wagenzahl.")
    st.select_slider("Zielgruppen (Abfahrtszüge)", options=C.M_OPTIONS, key="m_select", help="Zahl der Abfahrtszüge, in die der Zug zerlegt wird. Jede Gruppe soll am Ende zusammenhängend stehen.")
    st.select_slider("Richtungsgleise", options=C.K_OPTIONS, key="k_select", help="Zahl der Gleise im Richtungsbereich: je Durchgang kann in so viele Teile getrennt werden.")
    st.select_slider("Gruppengrößen", options=C.SIZE_OPTIONS, key="sizes_select", format_func=lambda s: C.SIZE_LABELS[s],
                     help="Gleich groß: jeder Wagen gehört zufällig zu einer der Gruppen. Ungleich: wenige große und viele kleine Gruppen (Gewicht 1/Rang).")
    st.slider("Aufwand je Durchgang (min)", C.SETUP_MIN, C.SETUP_MAX, step=C.SETUP_STEP, key="setup_slider",
              help=f"Zeit für Lok umsetzen und Gleise abziehen, einmal je Durchgang. Dazu kommen {C.CAR_MIN} min Abdrückzeit je bewegtem Wagen (feste Annahme).")
    st.number_input("Zufalls-Seed", min_value=bounds("seed_input")[0], max_value=bounds("seed_input")[1], step=1, key="seed_input",
                    help="Bestimmt, welcher Wagen zu welcher Gruppe gehört.")
    st.button("🎲 Neuen Zug würfeln", on_click=randomize_seed)

values = {k: st.session_state[k] for k in ("n_select", "m_select", "k_select", "sizes_select", "setup_slider", "seed_input", "view_select")}
sync_query_params(values)
settings = settings_from_state(values)

res = _results()
run = _live(settings["n"], settings["m"], settings["k"], settings["sizes"], settings["seed"])
group_of, results = run["group_of"], run["results"]
gsz = M.group_sizes(group_of)
vname = R.variant_name(settings)
setup = settings["setup"]
st.caption(
    f"{len(group_of)} Wagen in {run['m_eff']} Zielgruppen (kleinste Gruppe {min(gsz.values())}, größte {max(gsz.values())} Wagen), {settings['k']} Richtungsgleise. "
    f"Rechenzeit der drei Verfahren {run['seconds'] * 1000:.0f} ms."
)

st.markdown("---")
st.markdown("## ⛰️ Zeit gegen Arbeit: was kostet jedes Verfahren am Berg?")
t = times(run, setup)
cols = st.columns(3)
for col, key in zip(cols, C.METHODS):
    r = results[key]
    col.metric(C.METHOD_LABELS[key], f"{t[key]:.0f} min Bergzeit", delta=f"{r['passes']} Durchgänge, {r['moves']} Wagenbewegungen", delta_color="off",
               help=f"Bergzeit = Durchgänge × {setup} min + Wagenbewegungen × {C.CAR_MIN} min. Wagenbewegung = ein Wagen rollt einmal über den Berg.")
state, text = time_message(run, setup)
(st.success if state in ("radix", "trivial") else st.info)(f"⏱️ {text}")
st.info("🔢 " + passes_message(run, settings["k"]))

rows = []
for key in C.METHODS:
    r = results[key]
    rows.append({"Verfahren": C.METHOD_LABELS[key], "Durchgänge": r["passes"], "Wagenbewegungen": r["moves"], "Bewegungen je Wagen": round(r["moves"] / len(group_of), 2),
                 "Bergzeit (min)": round(t[key], 1), "Plan zulässig": "ja" if r["valid"] else "NEIN"})
st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
st.caption("Jeder Plan wird von einem unabhängigen Prüfer abgespielt (Gleise als Warteschlangen): Die Endfolge hat jede Gruppe zusammenhängend und jeder Wagen kommt genau einmal vor.")
if not all(v["valid"] for v in results.values()):
    st.error("Interner Fehler: ein Plan verletzt das Modell.")

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Woraus sich die Bergzeit zusammensetzt**")
    st.plotly_chart(build_time_bars(run, setup), width="stretch", key=f"timebars_{settings}")
with c2:
    st.markdown("**Bergzeit gegen den Aufwand je Durchgang** (gestrichelt: Ihre Einstellung)")
    st.plotly_chart(build_setup_lines(run, setup), width="stretch", key=f"setuplines_{settings}")

st.markdown("### Die Zugfolge Durchgang für Durchgang")
view = st.radio("Verfahren anzeigen", C.VIEW_OPTIONS, key="view_select", horizontal=True, format_func=lambda k: C.METHOD_LABELS[k],
                help="Reine Anzeigewahl: welches Verfahren als Folge der Züge gezeigt wird (keine Einstellung der Rechnung).")
st.plotly_chart(build_train_strips(group_of, results[view]["schedule"], settings["k"]), width="stretch", key=f"strips_{settings}_{view}")
st.caption("Jedes Quadrat ist ein Wagen, die Farbe seine Zielgruppe. Oben der ankommende Zug, darunter der Zug nach jedem Durchgang (rechts: wie viele Wagen in diesem Durchgang über den Berg gingen): Beim gruppenweisen Abarbeiten stehen die fertigen Gruppen vorn (mit Lücke), der Rest geht wieder über den Berg; bei Radix steht am Ende alles nach Gruppen sortiert.")
summary_lines = [f"{len(group_of)} Wagen, {run['m_eff']} Zielgruppen, {settings['k']} Richtungsgleise, Verfahren: {C.METHOD_LABELS[view]}",
                 f"{results[view]['passes']} Durchgänge, {results[view]['moves']} Wagenbewegungen, Bergzeit {t[view]:.0f} min bei {setup} min Aufwand je Durchgang."]
st.download_button("📄 Rangierplan als PDF herunterladen", data=generate_plan_pdf(group_of, results[view]["schedule"], settings["k"], "Rangierplan", summary_lines),
                   file_name="rangierplan.pdf", mime="application/pdf", key="pdf_download")

# ------------------------------------------------------------------ Kernabschnitt: Messreihe
st.markdown("---")
st.subheader("📐 Was die Messreihe zeigt")
variants = R.all_variants(res)
names = [v["name"] for v in variants]
st.caption(f"Vorgerechnet (tools/sweep.py): {len(R.rows_of(res, names[0]))} Züge je Variante; Durchgänge und Bewegungen aller drei Verfahren plus die exakte Mindestzahl (CP-SAT, Zahl der bewiesenen Fälle in der Tabelle).")
std = next(v for v in variants if v["name"] == "Standard (40 Wagen)")
d1, d2, d3, d4 = st.columns(4)
d1.metric("Radix: Durchgänge", f"{std['passes_radix']:.1f}", help="Standardfall, 40 Wagen, 8 Gruppen, 4 Gleise: Mittel über die Züge der Messreihe.")
d2.metric("Gruppenweise: Durchgänge", f"{std['passes_seq_num']:.1f}")
d3.metric("Exakt: Durchgänge", f"{std['passes_exact']:.1f}", help="Mindestzahl nach CP-SAT; bewiesen in den in der Tabelle genannten Fällen.")
d4.metric("Exakt besser als Radix", f"{std['exact_better']} von {std['n']} Zügen")
st.plotly_chart(build_sweep_passes(variants), width="stretch", key="sweep_passes")
st.plotly_chart(build_sweep_moves(variants), width="stretch", key="sweep_moves")
st.markdown("**Wann schlägt die exakte Lösung Radix?**")
st.plotly_chart(build_better_share(variants), width="stretch", key="sweep_better")
byname = {v["name"]: v for v in variants}
a, b, c = byname["12 Gruppen, 3 Gleise"], byname["Standard (40 Wagen)"], byname["6 Gleise"]
st.caption(
    f"Radix braucht ⌈log_k m⌉ Durchgänge, aber das ist nicht immer das Minimum: Das Ziel verlangt nur, dass jede Gruppe am Ende zusammenhängend steht; sie darf dafür auf mehrere Gleise verteilt werden, wenn die Gleise in passender Reihenfolge abgezogen werden. "
    f"Bei 12 Gruppen auf 3 Gleisen braucht die exakte Lösung im Mittel {a['passes_exact']:.1f} statt {a['passes_radix']:.1f} Durchgänge ({a['exact_better']} von {a['n']} Zügen besser), bei 8 Gruppen auf 6 Gleisen "
    f"{c['passes_exact']:.1f} statt {c['passes_radix']:.1f}; im Standardfall (8 Gruppen auf 4 Gleisen) nie ({b['exact_better']} von {b['n']}). Ein einfaches Muster, wann es sich lohnt, ließ sich nicht ableiten: "
    "bei 4 Gleisen und 12 oder 16 Gruppen gibt es nichts zu gewinnen, bei 6 Gleisen und 12 Gruppen fast immer."
)
st.markdown("**Und die Zuglänge?**")
length_rows = [v for v in variants if v["name"] in C.LENGTH_SERIES]
length_rows.sort(key=lambda v: C.LENGTH_SERIES.index(v["name"]))
st.plotly_chart(build_length_series(length_rows), width="stretch", key="sweep_length")
st.caption("Gleiche Gruppenzahl (6) und gleiche Gleise (3), nur die Zuglänge wächst. Bei sehr kurzen Zügen bestehen die Gruppen aus ein oder zwei Wagen und lassen sich fast immer in einem Durchgang zusammenfassen; ab etwa 30 Wagen verschwindet der Vorsprung in diesem Fall. Wie stark der Vorsprung bleibt, hängt also an der Kombination aus Gruppen, Gleisen und Zuglänge.")
st.dataframe(pd.DataFrame([{"Variante": v["name"], "bewiesen": f"{v['proven']}/{v['n']}", "Gruppenweise": round(v["passes_seq_num"], 2), "Radix": round(v["passes_radix"], 2),
                            "Exakt": round(v["passes_exact"], 2), "exakt besser": f"{v['exact_better']}/{v['n']}", "Bewegungen/Wagen gruppenweise (größte zuerst)": round(v["permove_seq_size"], 2),
                            "Bewegungen/Wagen Radix": round(v["permove_radix"], 2),
                            "Kipppunkt (min Aufwand je Durchgang)": "–" if v["crossover"] is None else f"{v['crossover']:.1f}"} for v in variants]), width="stretch", hide_index=True)
if vname:
    cur = next(v for v in variants if v["name"] == vname)
    st.caption(f"Die gewählten Einstellungen entsprechen der Messreihen-Variante „{vname}“: Gruppenweise {cur['passes_seq_num']:.1f}, Radix {cur['passes_radix']:.1f}, exakt {cur['passes_exact']:.1f} Durchgänge im Mittel.")
else:
    st.caption("Für diese Kombination der Regler gibt es keine Messreihen-Variante; die Tabelle zeigt die gemessenen Fälle.")

# ------------------------------------------------------------------ Methodenvergleich
st.markdown("---")
with st.expander("🔧 Wie wir das erreichen – vollständiger Methodenvergleich", expanded=False):
    tabs = st.tabs(["⛰️ Verfahren", "🧮 Exakt (OR-Tools)", "📈 Messreihe"])

    with tabs[0]:
        st.markdown(
            "**Gruppenweise:** Im ersten Durchgang bekommen k − 1 Gruppen ein eigenes Gleis und sind fertig, alle anderen Wagen sammeln sich auf dem letzten Gleis und gehen wieder über den Berg. "
            "Das wiederholt sich, im letzten Durchgang bekommt jede übrige Gruppe ein Gleis. Fertige Wagen werden nicht mehr bewegt. Die Reihenfolge der Gruppen ist frei: *nach Nummer* oder *größte zuerst* "
            "(dann sind früh viele Wagen fertig und der Rest ist klein). **Radix:** Die Gruppen werden durchgezählt; Durchgang 1 sortiert nach der letzten Ziffer der Gruppennummer zur Basis k, "
            "Durchgang 2 nach der vorletzten und so weiter. Weil die Gleise Warteschlangen sind, bleibt die Reihenfolge innerhalb einer Ziffer erhalten; nach d Durchgängen ist der Zug sortiert. "
            "Jeder Wagen wird in jedem Durchgang bewegt."
        )
        st.dataframe(pd.DataFrame([{"Wagen": c + 1, "Gruppe": group_of[c] + 1, **{f"{C.METHOD_LABELS[k_]}: Gleis im 1. Durchgang": (results[k_]["schedule"][0]["keys"][c] + 1) if results[k_]["schedule"] else "–"
                                                                               for k_ in C.METHODS}} for c in range(len(group_of))]), width="stretch", hide_index=True)

    with tabs[1]:
        st.caption(f"Das exakte Modell fragt für P = 1 bis (Radix − 1): Geht das Gruppieren in P Durchgängen? Je Durchgang ein Gleisschlüssel je Wagen, die Wagenfolge folgt aus den Schlüsseln, "
                   f"die Gruppen müssen am Ende zusammenhängen. Zeitlimit {C.EXACT_TIME_LIMIT:.0f} s je Frage.")
        key = tuple(sorted(settings.items()))
        if st.button("🧮 Mindestzahl der Durchgänge exakt bestimmen", key="exact_button"):
            with st.spinner(f"CP-SAT rechnet (bis zu {C.EXACT_TIME_LIMIT:.0f} s je Frage, bei 60 Wagen meist 5 bis 10 s) …"):
                ex = X.min_passes(group_of, settings["k"], C.EXACT_TIME_LIMIT)
                st.session_state["exact_result"] = {"key": key, "res": ex, "valid": M.valid_schedule(group_of, ex["schedule"], settings["k"])}
        er = st.session_state.get("exact_result")
        if er and er["key"] == key:
            ex = er["res"]
            e1, e2, e3, e4 = st.columns(4)
            e1.metric("Mindestzahl", f"{ex['passes']}", help="Kleinste Zahl Durchgänge, in der jede Gruppe zusammenhängend steht.")
            e2.metric("Radix", f"{ex['radix']}", help="Durchgänge, die Radix braucht.")
            e3.metric("Status", "bewiesen" if ex["proven"] else "Zeitlimit")
            e4.metric("Rechenzeit", f"{ex['time']:.1f} s")
            state, text = exact_message(run, ex)
            (st.success if state == "same" else st.warning if state == "unproven" else st.info)(text)
            if not er["valid"]:
                st.error("Interner Fehler: der exakte Plan verletzt das Modell.")
            st.plotly_chart(build_train_strips(group_of, ex["schedule"], settings["k"]), width="stretch", key=f"strips_exact_{settings}")
            st.caption("Der Plan der exakten Lösung (alle Wagen in jedem Durchgang bewegt); er wird vom selben unabhängigen Prüfer abgenommen wie die beiden Verfahren.")
        elif er:
            st.caption("Die Einstellungen haben sich seit dem letzten Lauf geändert - bitte erneut lösen.")

    with tabs[2]:
        st.caption("Alle Varianten der Messreihe: mittlere Durchgänge und mittlere Wagenbewegungen je Verfahren, mittlere Rechenzeit der exakten Rechnung (Median).")
        st.dataframe(pd.DataFrame([{"Variante": v["name"], "Gruppen Ø": round(v["m_eff"], 1), "Durchgänge gruppenweise": round(v["passes_seq_num"], 2), "Durchgänge Radix": round(v["passes_radix"], 2),
                                    "Durchgänge exakt": round(v["passes_exact"], 2), "Bewegungen gruppenweise (Nummer)": round(v["moves_seq_num"]), "Bewegungen gruppenweise (größte zuerst)": round(v["moves_seq_size"]),
                                    "Bewegungen Radix": round(v["moves_radix"]), "CP-SAT-Zeit Median (s)": round(v["time_median"], 1)} for v in variants]), width="stretch", hide_index=True)

with st.expander("Wie funktioniert diese Demo?"):
    st.markdown(
        f"""
**Anlage.** Ein Ablaufberg mit {settings['k']} Richtungsgleisen (einstellbar 2 bis 6). Ein Zug wird Wagen für Wagen über den Berg abgedrückt und rollt auf ein Gleis; auf einem Gleis steht der zuerst gerollte Wagen vorn
(Warteschlange). Anschließend werden die Gleise abgezogen: entweder als fertiger Teil eines Abfahrtszuges oder, in einer festen Gleisreihenfolge hintereinander, als neuer Zug für den nächsten Durchgang.

**Zug.** Jeder Wagen gehört zu einer Zielgruppe (einem Abfahrtszug). Ziel ist, dass am Ende jede Gruppe zusammenhängend steht; in welcher Reihenfolge die Gruppen stehen, ist egal. Die Wagen innerhalb einer Gruppe dürfen in beliebiger Folge stehen.

**Kosten.** Ein *Durchgang* ist ein Durchlauf aller noch nicht fertigen Wagen über den Berg. Die *Bergzeit* ist Durchgänge mal Aufwand je Durchgang (Lok umsetzen, Gleise abziehen; Regler) plus Wagenbewegungen
mal {C.CAR_MIN} min Abdrückzeit je Wagen (feste Annahme). So wird sichtbar, was die beiden Verfahren gegeneinander tauschen: Radix braucht wenige Durchgänge, bewegt aber jeden Wagen in jedem; das gruppenweise
Abarbeiten bewegt weniger Wagen, braucht aber mehr Durchgänge.

**Grenzen.** Synthetische Züge, feste Abdrückzeit, keine Gleislängen (jedes Gleis fasst beliebig viele Wagen), keine Ankunftszeiten mehrerer Züge, keine Bergkapazität über den Tag, Wagen innerhalb einer Gruppe unsortiert.
Die Zahlen belegen Größenordnungen auf diesen Zügen, keinen realen Betrieb.
"""
    )

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** Wagen $1..n$ mit Gruppe $g(c)$, $k$ Gleise (Warteschlangen). Ein Durchgang ordnet jedem Wagen des Zuges ein Gleis $\kappa(c) \in \{1..k\}$ zu; die neue Folge ist die Verkettung der Gleise in Gleisreihenfolge,
innerhalb eines Gleises in Ankunftsreihenfolge. Nach $P$ Durchgängen soll jede Gruppe zusammenhängend stehen.

**Gruppenweise.** Mit $m$ Gruppen braucht das Verfahren $\lceil (m-1)/(k-1) \rceil$ Durchgänge: Je Durchgang werden $k-1$ Gruppen fertig, im letzten höchstens $k$. **Radix.** Die Gruppen werden mit $0..m-1$ nummeriert, Durchgang $j$
sortiert nach der $j$-ten Ziffer der Nummer zur Basis $k$ (niedrigste zuerst): $\lceil \log_k m \rceil$ Durchgänge, in jedem werden alle $n$ Wagen bewegt, also $n \lceil \log_k m \rceil$ Bewegungen.

**Bergzeit.** $T = P \cdot s + W \cdot t_w$ mit $P$ Durchgängen, $W$ Wagenbewegungen, $s$ dem Aufwand je Durchgang und $t_w$ der Abdrückzeit je Wagen. Zwei Verfahren $a, b$ mit $P_a > P_b$ und $W_a < W_b$ sind gleich schnell bei
$s^* = (W_b - W_a)\, t_w / (P_a - P_b)$.

**Exakt.** Boolesche Variablen $v^p_{ab}$ = „Wagen $a$ steht nach Durchgang $p$ vor $b$“: $v^p_{ab} \Leftrightarrow \kappa_p(a) < \kappa_p(b) \lor (\kappa_p(a) = \kappa_p(b) \land v^{p-1}_{ab})$. Die Gruppe von $a, b$ ist zusammenhängend,
wenn kein Wagen $x$ anderer Gruppe mit $a$ vor $x$ vor $b$ steht. Gefragt wird nach $P = 1, \dots, \lceil \log_k m \rceil - 1$.
"""
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zum Thema: [Schienenverkehr optimieren](https://sebastianhanisch.net/schienenverkehr-optimierung.html)."
)
