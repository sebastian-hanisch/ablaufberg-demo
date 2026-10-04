"""Rangierplan als PDF (fpdf2, Kernschrift Helvetica: Umlaute gehen, Gedankenstrich, Euro-Zeichen, Emoji und U+2212 nicht)."""
from __future__ import annotations

from fpdf import FPDF

import abl_model as M

_REPLACE = {"–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "→": "->", "↔": "<->", "…": "...", "€": "EUR", "·": ".", "Ø": "Durchschnitt"}


def _clean(text: str) -> str:
    for a, b in _REPLACE.items():
        text = text.replace(a, b)
    return text.encode("latin-1", "replace").decode("latin-1")


def _cars(cars: list, group_of) -> str:
    return ", ".join(f"{c + 1} (G{group_of[c] + 1})" for c in cars) if cars else "leer"


def generate_plan_pdf(group_of, schedule: list, k: int, title: str, summary_lines: list) -> bytes:
    """Je Durchgang: welche Wagen auf welches Gleis rollen, welche Gleise fertig abgezogen werden und was als Rest wieder über den Berg geht."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _clean(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for line in summary_lines:
        pdf.multi_cell(0, 5, _clean(line), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, _clean(f"Eingang: {len(group_of)} Wagen, Zielgruppen G1 bis G{max(group_of) + 1}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 4.5, _clean("  " + _cars(list(range(len(group_of))), group_of)), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    if not schedule:
        pdf.multi_cell(0, 5, _clean("Alle Gruppen stehen schon zusammenhängend: kein Durchgang nötig."), new_x="LMARGIN", new_y="NEXT")
    for j, st in enumerate(M.simulate(len(group_of), schedule, k), 1):
        fin = set(schedule[j - 1]["finish"])
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, _clean(f"Durchgang {j} - {st['moved']} Wagen über den Berg"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for t, cars in enumerate(st["tracks"]):
            if cars:
                tag = " (fertig abgezogen)" if t in fin else ""
                pdf.multi_cell(0, 4.5, _clean(f"  Gleis {t + 1}{tag}: {_cars(cars, group_of)}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    return bytes(pdf.output())
