# Ablaufberg: Wie viele Durchgänge braucht die Zugbildung? (Streamlit-Demo)

**[→ Demo live ausprobieren](https://sebastianhanisch-ablaufberg-demo.streamlit.app/)**

Interaktive **Fall-Demo** zur Zugbildung am Ablaufberg im Portfolio von [Sebastian Hanisch](https://sebastianhanisch.net) (Operations Research und Machine Learning).
**Vierter Baustein der Reihe Bahn/Schienenverkehr** nach dem [Taktfahrplan](https://github.com/sebastian-hanisch/taktfahrplan-demo), dem [Crew Pairing](https://github.com/sebastian-hanisch/crew-pairing-demo) und dem
[Trassenkonflikt](https://github.com/sebastian-hanisch/trassenkonflikt-demo).

Ein Güterzug rollt über den Ablaufberg auf Richtungsgleise; jeder Wagen gehört zu einem Abfahrtszug (seiner Zielgruppe). Gibt es weniger Gleise als Gruppen, muss der Zug mehrfach über den Berg. Die Demo
vergleicht das **gruppenweise Abarbeiten** (je Durchgang ein paar Gruppen fertig) mit **Radix** (alle Gruppen gleichzeitig, nach Ziffern der Gruppennummer), rechnet die **exakte Mindestzahl an Durchgängen**
(OR-Tools CP-SAT) und fragt, **was ein Durchgang kosten darf**, bevor sich die Wahl umdreht.

## Kernfrage

Wie viele Durchgänge über den Berg braucht die Zugbildung, und wann lohnt es sich, wenige Durchgänge (Radix, jeder Wagen in jedem Durchgang) gegen weniger Wagenbewegungen (gruppenweise) zu tauschen? Die Gleise sind
hier Warteschlangen (wer zuerst rollt, steht vorn): ein anderes Modell als das Abstellen auf LIFO-Plätzen in [hofstellplatz-demo](https://github.com/sebastian-hanisch/hofstellplatz-demo) und
[stapelplanung-demo](https://github.com/sebastian-hanisch/stapelplanung-demo), und eine Sortieraufgabe statt einer Platzwahl. Das Radix-Verfahren und die Fragestellung (Klassifizieren von Güterzügen mit mehreren
Durchgängen) stammen aus der Literatur: Jacob, Márton, Maue und Nunkesser, *Multistage Methods for Freight Train Classification*, Networks 57(1), 2011; verwandt, aber eine andere Frage, ist das Train-Marshalling-Problem
von Dahlhaus et al. (2000), NP-vollständig.

## Befunde und Korrekturen gegenüber dem Plan

- **Dieser Baustein ist dünner als die drei vorigen, und das war vor dem Bau bekannt.** Die Modellprüfung gegen das Register ergab: Das Abstellen auf Gleisen ist ein bekanntes Modell (LIFO-Parken, Zuordnung);
  eigenständig bleibt die Ablaufberg-Sortierung. Der Kern ist eine Lehrbuchformel (Radix: ⌈log_k m⌉ Durchgänge). Neu ist, was sich dazu messen ließ.
- **Der erste Eindruck der Vorab-Messreihe war falsch gedeutet.** An Zügen mit 8 Wagen braucht die exakte Lösung im Mittel nur etwa einen Durchgang, Radix fast zwei. Das ist ein Kleinzug-Artefakt: Bei 8 Wagen bestehen
  die Gruppen aus ein oder zwei Wagen. Bei Zügen mit 30 oder 40 Wagen, 6 Gruppen und 3 Gleisen gibt es nichts mehr zu gewinnen (siehe Tabelle).
- **Der Vorsprung der exakten Lösung ist aber kein reines Kleinzug-Artefakt.** Bei 12 oder 16 Gruppen auf 3 Gleisen, 12 Gruppen auf 2 Gleisen und 8 Gruppen auf 6 Gleisen spart die exakte Lösung auch bei 40 Wagen in fast
  jedem Zug einen Durchgang gegenüber Radix. Ein einfaches Muster dafür ließ sich nicht ableiten; die Messreihe zeigt die gemessenen Fälle.
- **Ein Fehler, den erst das Orakel fand:** Die exakte Rechnung begann bei einem Durchgang und meldete für einen schon zusammenhängenden Zug einen Durchgang statt keinen. Behoben (`tests/test_exact.py`), die
  Messreihe danach neu erzeugt.
- Port 8961 (8960 gehören Trassenkonflikt und Splitting).

## Modell

- **Anlage:** ein Ablaufberg mit k Richtungsgleisen (2, 3, 4 oder 6). Ein Zug wird Wagen für Wagen abgedrückt und rollt auf ein Gleis; ein Gleis ist eine Warteschlange. Danach werden die Gleise abgezogen: entweder
  als fertiger Teil eines Abfahrtszuges oder, in Gleisreihenfolge hintereinander, als neuer Zug für den nächsten Durchgang.
- **Zug:** 20 bis 60 Wagen, jeder gehört zu einer von 4 bis 16 Zielgruppen. Gleich große Gruppen (jeder Wagen unabhängig gleichverteilt) oder ungleiche (Gewicht der Gruppe i ist 2520 / (i + 1)); die Gruppennummern werden
  zufällig vertauscht. Alles ganzzahlig mit **SplitMix64** (`abl_rng.py`).
- **Ziel:** Jede Gruppe steht am Ende zusammenhängend; die Reihenfolge der Gruppen und der Wagen innerhalb einer Gruppe ist egal.
- **Kosten:** *Durchgänge* und *Wagenbewegungen* (ein Wagen rollt einmal über den Berg). **Bergzeit** = Durchgänge × Aufwand je Durchgang (Regler, 0 bis 60 min) + Wagenbewegungen × 0,5 min (feste Annahme).

## Methodik

- **Gruppenweise** (`abl_model.plan_sequential`): je Durchgang bekommen k − 1 Gruppen ein eigenes Gleis und sind fertig, alle anderen Wagen sammeln sich auf dem letzten Gleis und gehen wieder über den Berg; im letzten
  Durchgang bekommt jede übrige Gruppe ein Gleis. Fertige Wagen werden nicht mehr bewegt. Reihenfolge der Gruppen *nach Nummer* oder *größte zuerst*; Letzteres minimiert die Summe der Restlängen und damit die Wagenbewegungen.
- **Radix** (`abl_model.plan_radix`): Durchgang j sortiert nach der j-ten Ziffer der Gruppennummer zur Basis k, niedrigste Ziffer zuerst; ⌈log_k m⌉ Durchgänge, jeder Wagen in jedem.
- **Exakt** (`abl_exact.py`): CP-SAT-Modell „geht das Gruppieren in P Durchgängen?“ für P = 1 bis Radix − 1, mit Relationsvariablen „Wagen a steht nach Durchgang p vor Wagen b“. Jeder Plan, auch der exakte, wird von
  einem **unabhängigen Prüfer** (`abl_model.valid_schedule`, Gleise als Warteschlangen) abgespielt.
- **Vorgerechnete Messreihe** (`tools/sweep.py` → `data/abl_results.json`, rund 1,5 Minuten parallel): 18 Varianten (Zuglänge, Gruppen, Gleise, Gruppengrößen) mit je 20 Zügen, alle Verfahren plus die exakte Lösung. Live
  laufen die drei Verfahren auf dem gewählten Zug; die exakte Rechnung nur auf Knopfdruck im Exakt-Tab.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`. 20 Züge je Variante (Seeds 100–119), Mittelwerte; in allen 360 Läufen ist die exakte Mindestzahl bewiesen.

| Frage | Befund |
|---|---|
| Wie viele Durchgänge im Standardfall (40 Wagen, 8 Gruppen, 4 Gleise)? | Gruppenweise **3.0**, Radix **2.0**, exakt **2.0**: Die exakte Lösung schlägt Radix in 0 von 20 Zügen. |
| Was kostet das Gruppenweise gegenüber Radix? | Mehr Durchgänge, aber weniger Wagenbewegungen: im Standardfall **1.61** statt **2.00** Bewegungen je Wagen (größte zuerst). |
| Wo kippt die Wahl? | Im Standardfall liegt der **Kipppunkt bei 7.9 min** Aufwand je Durchgang: Darunter ist das gruppenweise Abarbeiten schneller, darüber Radix. Bei 60 Wagen 10.4 min, bei ungleichen Gruppen 27.8 min. |
| Wann gibt es keine Wahl? | Bei 16 Gruppen braucht das Gruppenweise **4.9** Durchgänge gegen **2.0** und bewegt mit **2.32** Bewegungen je Wagen auch mehr als Radix (2.00); bei 2 Gleisen **7.0** Durchgänge gegen **3.0** und **3.60** Bewegungen je Wagen gegen 3.00. Dann gewinnt Radix bei jedem Aufwand je Durchgang. |
| Hilft es, die großen Gruppen zuerst fertigzustellen? | Bei ungleich großen Gruppen **1.31** statt **1.70** Bewegungen je Wagen (−23 %), bei gleichen Durchgängen. |
| Schlägt die exakte Lösung Radix? | Nicht im Standardfall (0 von 20) und nicht bei 4 Gleisen mit 12 oder 16 Gruppen. Bei **12 Gruppen auf 3 Gleisen** schafft sie **2.0** statt **3.0** Durchgängen (20 von 20), bei 16 Gruppen auf 3 Gleisen ebenso, bei 12 Gruppen auf 2 Gleisen **3.0** statt **4.0**, bei 8 Gruppen auf 6 Gleisen **1.0** statt **2.0**. |
| Und die Zuglänge? | Bei 6 Gruppen auf 3 Gleisen schlägt die exakte Lösung Radix in **95 %** der 8-Wagen-Züge, **100 %** der 12-Wagen-Züge, **30 %** der 20-Wagen-Züge und in **0 %** der 30- und 40-Wagen-Züge. |
| Wie lange rechnet CP-SAT? | Median **2.3 s** bei 40 Wagen, **6.3 s** bei 60 Wagen (je Zug, alle Fragen P = 1 bis Radix − 1); längste Rechnung **13.8 s**. |

## Ehrliche Grenzen

- **Dünner Baustein.** Die Radix-Formel ist Lehrbuch; die Messreihe zeigt, wo sie das Minimum ist und wo nicht, erklärt aber nicht, warum die exakte Lösung in manchen Fällen einen Durchgang spart.
- Synthetische Züge: ein Zug, feste Abdrückzeit je Wagen (0,5 min, Annahme), **keine Gleislängen** (jedes Gleis fasst beliebig viele Wagen), keine Ankunftszeiten mehrerer Züge, keine Bergkapazität über den Tag, Wagen
  innerhalb einer Gruppe unsortiert. Die Zahlen belegen Größenordnungen auf diesen Zügen, keinen realen Betrieb.
- Die exakte Rechnung bewegt in jedem Durchgang alle Wagen; ihre Wagenbewegungen sind deshalb eine Obergrenze und werden nicht mit den anderen verglichen.
- Die Messreihe hat 20 Züge je Variante und 18 Varianten; ein Muster über Gruppen und Gleise lässt sich daraus nicht ablesen.

## Tests

Siehe `tests/`: Zug, Gleise und beide Verfahren an einem von Hand gerechneten Mini-Zug (5 Wagen, 2 Gleise), unabhängiger Prüfer, **CP-SAT gegen eine Breitensuche über alle Gleisverteilungen**
(`tests/oracle_bfs.py`, alle Züge mit 6 Wagen und 3 Gruppen, Stichproben der größeren), Kipppunkt und Meldungen mit künstlichen Werten, Statistik an einer von Hand gerechneten Mini-Ergebnisdatei, Preset-Kriterien
(jedes Kriterium kippt einzeln), `test_claims.py` (jede README-Zahl gegen die Ergebnisdatei), AppTest-Rauchtests (Voreinstellung, jedes Preset, Randwerte, Permalink, Exakt-Tab). Keine Wall-Clock-Assertions.
`tools/mutation_check.py` baut einzelne Fehler in die Module ein und prüft, ob die Tests sie finden.

```
python -m pytest tests -q
```

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche |
| `abl_constants.py` | feste Annahmen, Regler-Stufen, Presets |
| `abl_rng.py`, `abl_model.py` | SplitMix64; Zug, Gleise, Durchgang, beide Verfahren, Prüfer |
| `abl_exact.py` | CP-SAT-Modell: Mindestzahl Durchgänge |
| `abl_evaluation.py` | Live-Rechnung, Bergzeit, Kipppunkt, Meldungen |
| `abl_results.py`, `abl_stories.py`, `abl_presets.py` | Auswertung der Messreihe; Preset-Kriterien; Permalink und Presets |
| `abl_visualization.py`, `abl_pdf_export.py` | Plotly-Figuren; Rangierplan als PDF |
| `data/abl_results.json` | Ergebnisse der Messreihe |
| `tools/` | `sweep.py`, `preset_search.py`, `mutation_check.py`, `PRESET_SWEEP.md` |

## Bewusst nicht umgesetzt

Gleislängen und Überläufe, mehrere ankommende Züge mit Abfahrtsfristen, Bergkapazität und Schichten, Sortieren innerhalb der Gruppen (volle Reihenfolge nach Wagennummer), Gleise als Stapel (LIFO) wie im
Flachbahnhof, Störungen und Rangierlok-Planung.

## Lokal ausführen

```
pip install -r requirements.txt
streamlit run app.py
```

Die Messreihe neu erzeugen: `python tools/sweep.py`.

Gebaut mit Streamlit, Plotly, OR-Tools, pandas und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zum Thema: [ÖPNV und Fernverkehr optimieren](https://sebastianhanisch.net/oepnv-fernverkehr-optimierung.html).
