"""Quick 5-vehicle sanity test for the Gemini 3 Flash Preview resolver.

Run with:  python test_gemini3.py

The script bypasses DB persistence so it works without a live Supabase connection.
Results are printed in ASCII-safe format for Windows terminals.
"""
import os
import sys
import time
import types as builtin_types
from unittest.mock import patch, MagicMock

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

# Patch DB calls BEFORE importing the resolver so the module-level singleton
# doesn't fail on import when DATABASE_URL is unavailable.
_mock_resolution = None  # filled per-test below


def _noop_ensure_schema():
    pass


def _noop_persist(self, **kwargs):
    pass


def _noop_cache_lookup(self, vehicle_key):
    return None


def _noop_record_hit(self, run_id, vehicle_key, user_id):
    pass


with (
    patch("persistence.ensure_schema", _noop_ensure_schema),
    patch("single_call_gemini_resolver.SingleCallGeminiResolver._fetch_from_cache", _noop_cache_lookup),
    patch("single_call_gemini_resolver.SingleCallGeminiResolver._persist_to_db", _noop_persist),
    patch("single_call_gemini_resolver.SingleCallGeminiResolver._record_cache_hit_run", _noop_record_hit),
):
    from single_call_gemini_resolver import SingleCallGeminiResolver


# (year, make, model, weight_lo, weight_hi, expected_cats)
TEST_VEHICLES = [
    (2015, "Honda",     "Civic",     2500, 3000, 1),
    (2018, "Ford",      "F-150",     4000, 5500, 2),
    (2010, "Toyota",    "Camry",     3000, 3700, 1),
    (2020, "Chevrolet", "Silverado", 4200, 5600, 2),
    (2008, "BMW",       "3 Series",  3100, 3700, 1),
]


def tick(ok: bool) -> str:
    return "OK" if ok else "FAIL"


def main():
    resolver = SingleCallGeminiResolver()
    print(f"\nModel: {resolver.model}   Thinking budget: {resolver.thinking_budget} tokens\n")
    print("=" * 80)

    results = []

    with (
        patch.object(resolver, "_fetch_from_cache", return_value=None),
        patch.object(resolver, "_persist_to_db"),
        patch.object(resolver, "_record_cache_hit_run"),
    ):
        for year, make, model, wlo, whi, exp_cats in TEST_VEHICLES:
            t0 = time.time()
            try:
                res = resolver.resolve_vehicle(year, make, model)
                elapsed = time.time() - t0

                w    = res.fields.get("curb_weight", {})
                cats = res.fields.get("catalytic_converters", {})
                eng  = res.fields.get("aluminum_engine", {})
                rims = res.fields.get("aluminum_rims", {})

                weight_val = w.get("value")
                cats_val   = cats.get("value")

                weight_ok = weight_val is not None and wlo <= weight_val <= whi
                cats_ok   = cats_val == exp_cats
                overall   = "PASS" if (weight_ok and cats_ok) else "WARN"

                print(f"[{overall}]  {year} {make} {model}")
                print(f"    Time:      {elapsed:.2f}s")
                wcheck = f"{tick(weight_ok)} ({weight_val} lbs, expected {wlo}-{whi})"
                ccheck = f"{tick(cats_ok)} ({cats_val}, expected {exp_cats})"
                print(f"    Weight:    {wcheck}")
                print(f"    Cats:      {ccheck}")
                print(f"    Al. Eng:   {eng.get('value')}  (status={eng.get('status')})")
                print(f"    Al. Rims:  {rims.get('value')}  (status={rims.get('status')})")

                results.append({
                    "vehicle": f"{year} {make} {model}",
                    "elapsed": elapsed,
                    "weight": weight_val,
                    "cats": cats_val,
                    "weight_ok": weight_ok,
                    "cats_ok": cats_ok,
                })

            except Exception as exc:
                elapsed = time.time() - t0
                print(f"[ERROR]  {year} {make} {model}  ({elapsed:.2f}s)")
                print(f"    {exc}")
                results.append({
                    "vehicle": f"{year} {make} {model}",
                    "elapsed": elapsed,
                    "error": str(exc),
                })

            print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for r in results:
        if "error" in r:
            snippet = r["error"][:70]
            print(f"  [ERROR]  {r['vehicle']:<35s}  {r['elapsed']:5.1f}s  {snippet}")
        else:
            tag = "PASS" if (r["weight_ok"] and r["cats_ok"]) else "WARN"
            print(
                f"  [{tag}]  {r['vehicle']:<35s}  {r['elapsed']:5.1f}s"
                f"  weight={r['weight']} lbs  cats={r['cats']}"
            )

    times = [r["elapsed"] for r in results]
    print(f"\n  Average latency : {sum(times) / len(times):.2f}s")
    print(f"  Min / Max       : {min(times):.2f}s / {max(times):.2f}s")
    passed = sum(1 for r in results if "error" not in r and r["weight_ok"] and r["cats_ok"])
    print(f"  Passed checks   : {passed}/{len(results)}")


if __name__ == "__main__":
    main()
