"""Fehler-Einbau-Test: baut einzelne Fehler in die Module ein und prüft, ob die Tests (ohne AppTests) sie finden.

Aufruf (im Projektordner): python tools/mutation_check.py [Teilstring des Dateinamens] [--jobs N] [--indices 5,8-12] [--with-app] [--dry-run]
Jeder Mutant ersetzt genau eine Stelle; Überlebende sind entweder gleichwertig (kein sichtbarer Unterschied) oder eine Lücke der Tests. Die Kopie liegt je Mutant in einem
temporären Ordner; PYTHONDONTWRITEBYTECODE=1, damit veralteter Bytecode keine Überlebenden vortäuscht; Quelltexte als LF. Ein Mutant kann in eine Endlosschleife laufen;
nach TIMEOUT Sekunden gilt er als gefunden. `--with-app` nimmt die AppTests hinzu, `--dry-run` prüft nur, ob jede Zeichenkette genau einmal vorkommt."""
import concurrent.futures
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY = sys.executable
WITH_APP = "--with-app" in sys.argv
TIMEOUT = 600
TEST_ORDER = ["test_rng.py", "test_model.py", "test_results.py", "test_presets.py", "test_evaluation.py", "test_stories.py", "test_gaps.py", "test_pdf.py", "test_oracle_bfs.py",
              "test_claims.py", "test_exact.py"]

MUTANTS = [
    ('abl_model.py', '    for i in range(m - 1, 0, -1):\n        j = rng.below(i + 1)', '    for i in range(m - 1, 1, -1):\n        j = rng.below(i + 1)'),
    ('abl_model.py', '        j = rng.below(i + 1)', '        j = rng.below(i)'),
    ('abl_model.py', 'C.ZIPF_BASE // (i + 1) for i in range(m)]', 'C.ZIPF_BASE // (i + 2) for i in range(m)]'),
    ('abl_model.py', '        while r >= acc:', '        while r > acc:'),
    ('abl_model.py', '        if not 0 <= t < k:', '        if not 0 <= t <= k:'),
    ('abl_model.py', '        for t in sorted(fin):', '        for t in sorted(fin, reverse=True):'),
    ('abl_model.py', '        rest = [c for t in range(k) if t not in fin for c in tracks[t]]', '        rest = [c for t in range(k) if t in fin for c in tracks[t]]'),
    ('abl_model.py', '            seen.add(g)\n            prev = g', '            prev = g'),
    ('abl_model.py', '    return {"passes": len(schedule), "moves": sum(len(p["keys"]) for p in schedule)}', '    return {"passes": len(schedule), "moves": sum(len(p["finish"]) for p in schedule)}'),
    ('abl_model.py', '    while cap < m_eff:', '    while cap <= m_eff:'),
    ('abl_model.py', '    return -(-(m_eff - 1) // (k - 1))', '    return (m_eff - 1) // (k - 1)'),
    ('abl_model.py', '        if len(ids) <= k:\n            track = {g: i for i, g in enumerate(ids)}', '        if len(ids) < k:\n            track = {g: i for i, g in enumerate(ids)}'),
    ('abl_model.py', '        take = ids[:k - 1]\n        track = {g: i for i, g in enumerate(take)}', '        take = ids[:k]\n        track = {g: i for i, g in enumerate(take)}'),
    ('abl_model.py', 'sorted(counts, key=lambda g: (-counts[g], g))', 'sorted(counts, key=lambda g: (counts[g], g))'),
    ('abl_model.py', '"finish": tuple(range(k - 1))})', '"finish": tuple(range(k))})'),
    ('abl_model.py', '        rest = [c for c in rest if group_of[c] not in track]', '        rest = [c for c in rest if group_of[c] in track]'),
    ('abl_model.py', '        keys = {c: (rank[group_of[c]] // k ** j) % k for c in rest}', '        keys = {c: (rank[group_of[c]] // k ** (d - 1 - j)) % k for c in rest}'),
    ('abl_model.py', '        last = j == d - 1', '        last = j == 0'),
    ('abl_model.py', '        ids = ids[k - 1:]', '        ids = ids[k:]'),
    ('abl_exact.py', '    for p in range(1, rad):', '    for p in range(1, rad + 1):'),
    ('abl_exact.py', '            proven = False                                        # p war nicht entschieden', '            pass                                                  # p war nicht entschieden'),
    ('abl_exact.py', '    if M.is_grouped(list(range(len(group_of))), group_of):', '    if False:'),
    ('abl_exact.py', '                model.AddBoolOr([before(a, x).Not(), before(x, b).Not(), before(a, b).Not()])', '                model.AddBoolOr([before(a, x).Not(), before(x, b).Not()])'),
    ('abl_exact.py', '                    model.Add(v == prev[(a, b)]).OnlyEnforceIf(eq)', '                    model.Add(v == 0).OnlyEnforceIf(eq)'),
    ('abl_exact.py', '                    model.Add(v == 1).OnlyEnforceIf(eq)', '                    model.Add(v == 0).OnlyEnforceIf(eq)'),
    ('abl_exact.py', '"finish": tuple(range(k)) if p == passes - 1 else ()', '"finish": tuple(range(k)) if p == 0 else ()'),
    ('abl_exact.py', '    return (False if status == cp_model.INFEASIBLE else None), None', '    return False, None'),
    ('abl_evaluation.py', '    return passes * setup + moves * C.CAR_MIN', '    return passes * setup + moves'),
    ('abl_evaluation.py', '(t[k], run["results"][k]["passes"], C.METHODS.index(k))', '(t[k], C.METHODS.index(k))'),
    ('abl_evaluation.py', '    if dp > 0 and dm > 0:', '    if dp > 0 and dm >= 0:'),
    ('abl_evaluation.py', '    if dp > 0 and dm > 0:', '    if dp >= 0 and dm > 0:'),
    ('abl_evaluation.py', '        return dm * C.CAR_MIN / dp', '        return dm / dp'),
    ('abl_evaluation.py', '    return "seq_size" if r["seq_size"]["moves"] < r["seq_num"]["moves"] else "seq_num"', '    return "seq_size" if r["seq_size"]["moves"] <= r["seq_num"]["moves"] else "seq_num"'),
    ('abl_evaluation.py', '    if r["radix"]["passes"] <= 1:', '    if r["radix"]["passes"] < 1:'),
    ('abl_evaluation.py', '    if r["radix"]["passes"] <= r[seq]["passes"] and r["radix"]["moves"] <= r[seq]["moves"]:', '    if r["radix"]["passes"] <= r[seq]["passes"] and r["radix"]["moves"] < r[seq]["moves"]:'),
    ('abl_evaluation.py', '    if best == "radix":', '    if best != "radix":'),
    ('abl_evaluation.py', '    if exact["passes"] < rad:', '    if exact["passes"] <= rad:'),
    ('abl_evaluation.py', '    if not exact["proven"]:', '    if exact["proven"]:'),
    ('abl_results.py', 'and r["exact"]["passes"] < r["methods"]["radix"]["passes"])', 'and r["exact"]["passes"] <= r["methods"]["radix"]["passes"])'),
    ('abl_results.py', '    seq = "seq_size"', '    seq = "seq_num"'),
    ('abl_results.py', '(st.stdev(xs) / len(xs) ** 0.5 if', '(st.stdev(xs) / len(xs) if'),
    ('abl_results.py', '    return row["exact"]["proven"]', '    return True'),
    ('abl_results.py', '    key = (settings["n"], settings["m"], settings["k"], settings["sizes"])', '    key = (settings["n"], settings["m"], settings["k"], "gleich")'),
    ('abl_presets.py', '(1 if 2 * r > step else 0)', '(1 if 2 * r >= step else 0)'),
    ('abl_presets.py', 'return min(options, key=lambda o: (abs(o - value), o))', 'return min(options, key=lambda o: (abs(o - value), -o))'),
    ('abl_presets.py', 'q, r = divmod(max(lo, min(hi, value)) - lo, step)', 'q, r = divmod(max(lo, value) - lo, step)'),
    ('abl_presets.py', '                    if value not in spec.options:', '                    if False:'),
    ('abl_constants.py', 'CAR_MIN = 0.5 ', 'CAR_MIN = 0.6 '),
    ('abl_constants.py', 'ZIPF_BASE = 2520 ', 'ZIPF_BASE = 2500 '),
    ('abl_stories.py', 'f["seq_size_moves"] <= 0.9 * f["seq_num_moves"]', 'f["seq_size_moves"] < 0.9 * f["seq_num_moves"]'),
    ('abl_stories.py', 'lambda f: f["m_eff"] >= 14', 'lambda f: f["m_eff"] > 14'),
    ('abl_stories.py', 'lambda f: f["crossover"] is not None and f["setup"] < f["crossover"]', 'lambda f: f["crossover"] is not None and f["setup"] <= f["crossover"]'),
    ('abl_stories.py', 'f["sweep_exact_better_share"] >= 0.9', 'f["sweep_exact_better_share"] > 0.9'),
    ('abl_visualization.py', 'GAP = 1.5 ', 'GAP = 0.5 '),
    ('abl_visualization.py', 'pos + (GAP if pos >= ndone and ndone else 0)', 'pos + (GAP if pos > ndone and ndone else 0)'),
    ('abl_visualization.py', '        rows.append((f"nach Durchgang {j}", done + st["rest"], len(done), st["moved"]))', '        rows.append((f"nach Durchgang {j}", st["rest"] + done, len(done), st["moved"]))'),
    ('abl_visualization.py', 'y=[run["results"][k]["passes"] * setup for k in C.METHODS]', 'y=[run["results"][k]["passes"] for k in C.METHODS]'),
    ('abl_visualization.py', '[E.bergzeit(r["passes"], r["moves"], s) for s in xs]', '[E.bergzeit(r["passes"], r["moves"], 0) for s in xs]'),
    ('abl_visualization.py', 'y=[100 * r["exact_better_share"] for r in rows], marker_color=C.METHOD_COLORS["exact"], name="exakt besser als Radix"', 'y=[r["exact_better_share"] for r in rows], marker_color=C.METHOD_COLORS["exact"], name="exakt besser als Radix"'),
    ('abl_pdf_export.py', '_REPLACE = {"–": "-"', '_REPLACE = {"–": ""'),
    ('abl_pdf_export.py', '    return ", ".join(f"{c + 1} (G{group_of[c] + 1})" for c in cars) if cars else "leer"', '    return ", ".join(f"{c} (G{group_of[c] + 1})" for c in cars) if cars else "leer"'),
]


def check_unique():
    bad = []
    for n, (name, old, new) in enumerate(MUTANTS, 1):
        text = (ROOT / name).read_bytes().decode("utf-8").replace("\r\n", "\n")
        if text.count(old) != 1:
            bad.append((n, name, old[:70], text.count(old)))
        if old == new:
            bad.append((n, name, "alt == neu", 0))
    return bad


def run_one(args):
    n, name, old, new, base = args
    tmp = pathlib.Path(tempfile.mkdtemp(prefix=f"abl_mut{n}_"))
    try:
        shutil.copytree(base, tmp, dirs_exist_ok=True)
        path = tmp / name
        original = path.read_bytes().decode("utf-8")
        path.write_bytes(original.replace(old, new).encode("utf-8"))
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        files = [f"tests/{f}" for f in TEST_ORDER + (["test_app.py"] if WITH_APP else [])]
        try:
            r = subprocess.run([PY, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", *files], cwd=tmp, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT)
            return n, name, old, new, r.returncode == 0, False
        except subprocess.TimeoutExpired:
            return n, name, old, new, False, True                 # Endlosschleife oder zu langsam: gilt als gefunden
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = args[0] if args else ""
    jobs = 6
    if "--jobs" in sys.argv:
        jobs = int(sys.argv[sys.argv.index("--jobs") + 1])
        only = "" if only == str(jobs) else only
    wanted = None
    if "--indices" in sys.argv:
        spec = sys.argv[sys.argv.index("--indices") + 1]
        only = "" if only == spec else only
        wanted = set()
        for part in spec.split(","):
            lo, _, hi = part.partition("-")
            wanted.update(range(int(lo), int(hi or lo) + 1))
    bad = check_unique()
    for b in bad:
        print("FEHLER (Stelle nicht eindeutig gefunden):", b)
    if "--dry-run" in sys.argv:
        print(f"{len(MUTANTS)} Mutanten, {len(bad)} Fehler in der Mutantenliste")
        return
    base = pathlib.Path(tempfile.mkdtemp(prefix="abl_mut_base_"))
    for f in ROOT.glob("*.py"):
        (base / f.name).write_bytes(f.read_bytes().replace(b"\r\n", b"\n"))
    shutil.copytree(ROOT / "tests", base / "tests", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(ROOT / "README.md", base / "README.md")
    shutil.copytree(ROOT / "data", base / "data")
    for f in (base / "tests").glob("*.py"):
        f.write_bytes(f.read_bytes().replace(b"\r\n", b"\n"))
    bad_ids = {b[0] for b in bad}
    work = [(n, name, old, new, base) for n, (name, old, new) in enumerate(MUTANTS, 1) if n not in bad_ids and (not only or only in name) and (wanted is None or n in wanted)]
    survivors, killed = [], 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        for n, name, old, new, survived, timeout in pool.map(run_one, work):
            if timeout:
                print(f"[{n:3d}] Zeitüberschreitung (als gefunden gezählt)  {name}", flush=True)
            if survived:
                survivors.append((n, name, old[:70], new[:70]))
                print(f"[{n:3d}] ÜBERLEBT  {name}: {old[:70]!r} -> {new[:70]!r}", flush=True)
            else:
                killed += 1
                print(f"[{n:3d}] gefunden  {name}", flush=True)
    print(f"\n{killed} gefunden, {len(survivors)} überlebt, {len(bad)} Fehler in der Mutantenliste")
    shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()
