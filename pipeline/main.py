"""
Pipeline orchestrator with tiered failure handling.

Runs all data ingestors in three phases:
1. CRITICAL sources (RBA Cash Rate, CPI, Employment) - fail fast if any error
2. IMPORTANT sources (Household Spending, Wage Price Index) - warn but continue
3. OPTIONAL sources (Building Approvals, CoreLogic, NAB) - graceful degradation

Exit codes:
- 0: All critical sources succeeded (important/optional failures are non-fatal)
- 1: Critical source failed (pipeline failed)
"""

import json
import sys
from datetime import datetime
from typing import Any

# Import all ingestors
from pipeline.ingest import abs_data, corelogic_scraper, nab_scraper, rba_data

# Import normalization engine (guarded -- pipeline works even if module unavailable)
try:
    from pipeline.normalize.engine import generate_status
    NORMALIZATION_AVAILABLE = True
except ImportError:
    NORMALIZATION_AVAILABLE = False


# Define source tiers
CRITICAL_SOURCES = [
    ('RBA Cash Rate', rba_data),
    ('ABS CPI', lambda: abs_data.fetch_and_save('cpi')),
    ('ABS Employment', lambda: abs_data.fetch_and_save('employment')),
]

IMPORTANT_SOURCES = [
    ('ABS Household Spending', lambda: abs_data.fetch_and_save('household_spending')),
    ('ABS Wage Price Index', lambda: abs_data.fetch_and_save('wage_price_index')),
]

OPTIONAL_SOURCES = [
    ('ABS Building Approvals', lambda: abs_data.fetch_and_save('building_approvals')),
    ('CoreLogic Housing', corelogic_scraper),
    ('NAB Capacity', nab_scraper),
]


def run_pipeline() -> dict[str, Any]:
    """
    Execute data pipeline with tiered failure handling.

    Returns:
        Dict with run metadata, results by tier, and overall status
    """
    results = {
        'run_date': datetime.utcnow().isoformat() + 'Z',
        'critical': {},
        'important': {},
        'optional': {},
        'status': 'pending'
    }

    print("=" * 60)
    print("RBA HAWK-O-METER DATA PIPELINE")
    print("=" * 60)
    print(f"Started: {results['run_date']}\n")

    # Phase 1: Critical sources (fail fast)
    print("PHASE 1: CRITICAL SOURCES")
    print("-" * 60)

    for name, module in CRITICAL_SOURCES:
        print(f"\n[CRITICAL] {name}")
        try:
            # Call lambda functions directly, modules via fetch_and_save method
            is_lambda = (
                callable(module)
                and hasattr(module, '__name__')
                and '<lambda>' in str(module)
            )
            if is_lambda:
                result = module()
            else:
                result = module.fetch_and_save()
            results['critical'][name] = {
                'status': 'success',
                'result': result
            }
            print(f"✓ {name} completed successfully")

        except Exception as e:
            print(f"\n✗ CRITICAL FAILURE: {name} failed")
            print(f"Error: {e}")
            results['critical'][name] = {
                'status': 'failed',
                'error': str(e)
            }
            results['status'] = 'failed'

            # Print summary and exit immediately
            print("\n" + "=" * 60)
            print("PIPELINE FAILED - CRITICAL SOURCE ERROR")
            print("=" * 60)
            print(json.dumps(results, indent=2))
            sys.exit(1)

    print("\n" + "-" * 60)
    print("✓ All critical sources succeeded")

    # Phase 2: Important sources (warn but continue)
    print("\n\nPHASE 2: IMPORTANT SOURCES")
    print("-" * 60)

    important_failures = []

    for name, module in IMPORTANT_SOURCES:
        print(f"\n[IMPORTANT] {name}")
        try:
            result = module() if callable(module) else module.fetch_and_save()
            results['important'][name] = {'status': 'success', 'result': result}
            print(f"✓ {name} completed successfully")
        except Exception as e:
            print(f"⚠ WARNING: {name} failed: {e}")
            results['important'][name] = {'status': 'failed', 'error': str(e)}
            important_failures.append(name)

    if important_failures:
        print(
            f"\n⚠ {len(important_failures)} important "
            f"source(s) failed: "
            f"{', '.join(important_failures)}"
        )

    # Phase 3: Optional sources (graceful degradation)
    print("\n\nPHASE 3: OPTIONAL SOURCES")
    print("-" * 60)

    optional_failures = []

    for name, module in OPTIONAL_SOURCES:
        print(f"\n[OPTIONAL] {name}")
        try:
            result = module() if callable(module) else module.fetch_and_save()

            # Check if result indicates failure (scrapers return status dicts)
            if isinstance(result, dict) and result.get('status') == 'failed':
                print(
                    f"⚠ WARNING: {name} failed: "
                    f"{result.get('error', 'Unknown error')}"
                )
                results['optional'][name] = result
                optional_failures.append(name)
            else:
                results['optional'][name] = {
                    'status': 'success',
                    'result': result
                }
                print(f"✓ {name} completed successfully")

        except Exception as e:
            print(f"⚠ WARNING: {name} failed: {e}")
            results['optional'][name] = {
                'status': 'failed',
                'error': str(e)
            }
            optional_failures.append(name)

    # Determine final status
    all_failures = important_failures + optional_failures
    if all_failures:
        results['status'] = 'partial'
        results['important_failures'] = important_failures
        results['optional_failures'] = optional_failures
        print(
            f"\n⚠ {len(all_failures)} non-critical "
            f"source(s) failed: {', '.join(all_failures)}"
        )
    else:
        results['status'] = 'success'
        print("\n✓ All non-critical sources succeeded")

    # Phase 4: Data normalization and status.json generation
    print("\n\nPHASE 4: DATA NORMALIZATION")
    print("-" * 60)

    if not NORMALIZATION_AVAILABLE:
        print(
            "\n  Normalization engine not installed "
            "-- skipping status.json generation"
        )
        results['normalization'] = {
            'status': 'skipped',
            'reason': 'module not available',
        }
    else:
        try:
            status = generate_status()
            results['normalization'] = {
                'status': 'success',
                'hawk_score': status['overall']['hawk_score'],
                'indicators_available': status['metadata']['indicators_available'],
                'indicators_missing': status['metadata']['indicators_missing'],
            }
            print(
                f"\n  Normalization completed: "
                f"Hawk Score = "
                f"{status['overall']['hawk_score']:.1f}"
            )
            print(
                f"  Zone: {status['overall']['zone_label']}"
            )
            avail = status['metadata']['indicators_available']
            missing = status['metadata']['indicators_missing']
            print(
                f"  Indicators: {avail} available, "
                f"{len(missing)} missing"
            )

        except Exception as e:
            print(f"\n  WARNING: Normalization failed: {e}")
            results['normalization'] = {
                'status': 'failed',
                'error': str(e)
            }
            # Normalization failure is non-fatal -- the pipeline still succeeds
            # if critical data was ingested. status.json just won't be updated.

    # Print summary
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)

    total_sources = (
        len(CRITICAL_SOURCES)
        + len(IMPORTANT_SOURCES)
        + len(OPTIONAL_SOURCES)
    )
    critical_success = sum(
        1 for r in results['critical'].values()
        if r.get('status') == 'success'
    )
    important_success = sum(
        1 for r in results['important'].values()
        if r.get('status') == 'success'
    )
    optional_success = sum(
        1 for r in results['optional'].values()
        if r.get('status') == 'success'
    )
    total_success = critical_success + important_success + optional_success
    total_failures = total_sources - total_success

    print(f"Total sources: {total_sources}")
    print(f"Succeeded: {total_success}")
    print(f"Failed: {total_failures}")
    print("\nTier Breakdown:")
    print(f"  Critical: {critical_success}/{len(CRITICAL_SOURCES)} succeeded")
    print(f"  Important: {important_success}/{len(IMPORTANT_SOURCES)} succeeded")
    print(f"  Optional: {optional_success}/{len(OPTIONAL_SOURCES)} succeeded")
    print(f"\nStatus: {results['status'].upper()}")
    print("=" * 60)

    return results


if __name__ == '__main__':
    results = run_pipeline()

    # Print JSON summary to stdout
    print("\nJSON SUMMARY:")
    print(json.dumps(results, indent=2))

    # Exit with appropriate code
    # 0 = success or partial (critical sources OK, optional failures are non-fatal)
    # 1 = critical source failure (already exits early in run_pipeline)
    if results['status'] in ('success', 'partial'):
        sys.exit(0)
    # Failed status already exits with code 1 in run_pipeline()
