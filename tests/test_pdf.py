"""Rangierplan als PDF: gültige Datei, Kernschrift-Bereinigung, leerer Plan."""
import abl_model as M
import abl_pdf_export as P


def test_pdf_is_a_valid_document_for_every_method():
    g = M.generate(30, 8, "gleich", 500)
    for method in ("seq_num", "seq_size", "radix"):
        data = P.generate_plan_pdf(g, M.plan(g, 4, method), 4, "Rangierplan", ["30 Wagen – 8 Gruppen", "Zeit ≥ 40 min"])
        assert data.startswith(b"%PDF") and data.rstrip().endswith(b"%%EOF") and len(data) > 1500


def test_pdf_for_an_already_grouped_train_has_no_pass():
    data = P.generate_plan_pdf([0, 0, 1], [], 2, "Rangierplan", [])
    assert data.startswith(b"%PDF")


def test_clean_replaces_characters_the_core_font_cannot_draw():
    assert P._clean("A – B ≥ C → D … € Ø") == "A - B >= C -> D ... EUR Durchschnitt"
    assert P._clean("Größe äöüß") == "Größe äöüß" and P._clean("Emoji 🚂") == "Emoji ?"


def test_car_list_names_group_and_handles_empty_tracks():
    assert P._cars([0, 2], [3, 1, 3]) == "1 (G4), 3 (G4)" and P._cars([], [0]) == "leer"
