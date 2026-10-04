"""Vorgerechnete Messreihe: je Variante 20 Züge (Seeds 100-119), drei Verfahren plus exakte Mindestzahl (CP-SAT) -> data/abl_results.json.

  python tools/sweep.py        # rund 10 bis 20 Minuten mit 6 Prozessen
"""
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import abl_constants as C  # noqa: E402
import abl_exact as X  # noqa: E402
import abl_model as M  # noqa: E402


def one(args):
    name, n, m, k, sizes, seed = args
    group_of = M.generate(n, m, sizes, seed)
    rec = {"variant": name, "seed": seed, "n_cars": n, "m_eff": len(M.present_groups(group_of)), "methods": {}}
    for key in C.METHODS:
        schedule = M.plan(group_of, k, key)
        met = M.metrics(schedule)
        rec["methods"][key] = {"passes": met["passes"], "moves": met["moves"], "valid": M.valid_schedule(group_of, schedule, k)}
    ex = X.min_passes(group_of, k, C.EXACT_TIME_LIMIT_SWEEP, workers=1)
    rec["exact"] = {"passes": ex["passes"], "proven": ex["proven"], "time": ex["time"], "valid": M.valid_schedule(group_of, ex["schedule"], k)}
    return rec


def main():
    t0 = time.time()
    jobs = [(name, n, m, k, sizes, seed) for name, n, m, k, sizes in C.SWEEP_VARIANTS for seed in C.SWEEP_SEEDS]
    with ProcessPoolExecutor(max_workers=6) as ex:
        rows = list(ex.map(one, jobs))
    res = {"meta": {"seeds": [C.SWEEP_SEEDS.start, C.SWEEP_SEEDS.stop], "car_min": C.CAR_MIN, "exact_limit": C.EXACT_TIME_LIMIT_SWEEP,
                    "variants": [v[0] for v in C.SWEEP_VARIANTS]}, "rows": rows}
    out = ROOT / C.RESULTS_FILE
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(res, separators=(",", ":")), encoding="utf-8")
    print("geschrieben:", out, round(out.stat().st_size / 1024), "KB,", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
