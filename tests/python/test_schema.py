"""
Unit tests for status.json schema contract.

Validates the STATUS_SCHEMA and GAUGE_SCHEMA against both valid and invalid
documents. All test documents are constructed inline — no live file access.

Key decisions enforced by tests:
  - hawk_score must be integer type (52.0 float is rejected)
  - additionalProperties: false on overall section prevents schema drift
  - Zone and confidence enums are strictly validated (case-sensitive)
"""

import copy

import jsonschema
import jsonschema.validators
import pytest
from jsonschema import Draft7Validator
from jsonschema._types import draft7_type_checker

# =============================================================================
# Strict integer type checker
#
# By default, jsonschema treats Python float 52.0 as a valid "integer" because
# JSON's number types overlap. The per-user-decision contract requires hawk_score
# to be a Python int, not a float. We extend Draft7 with a strict integer checker
# that uses isinstance(x, int) and excludes bool and float.
# =============================================================================

_strict_type_checker = draft7_type_checker.redefine(
    "integer",
    lambda checker, instance: (
        isinstance(instance, int)
        and not isinstance(instance, (bool, float))
    ),
)
StrictValidator = jsonschema.validators.extend(
    Draft7Validator, type_checker=_strict_type_checker
)


def _validate(document, schema):
    """Validate using StrictValidator (rejects float for integer fields)."""
    StrictValidator(schema).validate(document)

# =============================================================================
# Schema definitions (derived from production status.json structure)
# =============================================================================

STATUS_SCHEMA = {
    "type": "object",
    "required": [
        "generated_at", "pipeline_version",
        "overall", "gauges", "weights", "metadata",
    ],
    "additionalProperties": True,  # top-level allows asx_futures optional key
    "properties": {
        "generated_at": {"type": "string"},
        "pipeline_version": {"type": "string"},
        "overall": {
            "type": "object",
            "required": [
                "hawk_score", "zone", "zone_label",
                "verdict", "confidence",
            ],
            "additionalProperties": False,
            "properties": {
                "hawk_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "zone": {
                    "type": "string",
                    "enum": [
                        "cold", "cool", "neutral",
                        "warm", "hot", "unknown",
                    ],
                },
                "zone_label": {"type": "string"},
                "verdict": {"type": "string"},
                "confidence": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
            },
        },
        "gauges": {"type": "object"},
        "weights": {"type": "object"},
        "metadata": {
            "type": "object",
            "required": [
                "window_years",
                "clamp_range",
                "mapping",
                "statistics",
                "indicators_available",
                "indicators_missing",
            ],
            "additionalProperties": False,
            "properties": {
                "window_years": {"type": "integer"},
                "clamp_range": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 2,
                    "maxItems": 2,
                },
                "mapping": {"type": "string"},
                "statistics": {"type": "string"},
                "indicators_available": {"type": "integer", "minimum": 0},
                "indicators_missing": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
}

GAUGE_SCHEMA = {
    "type": "object",
    "required": [
        "value",
        "zone",
        "zone_label",
        "z_score",
        "raw_value",
        "raw_unit",
        "weight",
        "polarity",
        "data_date",
        "staleness_days",
        "confidence",
        "interpretation",
        "history",
    ],
    "properties": {
        "value": {"type": "number", "minimum": 0, "maximum": 100},
        "zone": {
            "type": "string",
            "enum": ["cold", "cool", "neutral", "warm", "hot", "unknown"],
        },
        "zone_label": {"type": "string"},
        "z_score": {"type": "number"},
        "raw_value": {"type": "number"},
        "raw_unit": {"type": "string"},
        "weight": {"type": "number", "minimum": 0, "maximum": 1},
        "polarity": {"type": "integer", "enum": [1, -1]},
        "data_date": {"type": "string"},
        "staleness_days": {"type": "integer"},
        "confidence": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
        "interpretation": {"type": "string"},
        "history": {"type": "array", "items": {"type": "number"}},
    },
    # allows data_source, stale_display, long_run_avg, direction
    "additionalProperties": True,
}


# =============================================================================
# Helper factory for minimal valid status document
# =============================================================================


def _make_valid_status():
    """Return a minimal valid status.json document for reuse across tests."""
    return {
        "generated_at": "2026-02-25T00:00:00Z",
        "pipeline_version": "1.0.0",
        "overall": {
            "hawk_score": 52,
            "zone": "neutral",
            "zone_label": "Balanced",
            "verdict": "Economic indicators are broadly balanced",
            "confidence": "HIGH",
        },
        "gauges": {
            "inflation": {
                "value": 50.0,
                "zone": "neutral",
                "zone_label": "Balanced",
                "z_score": 0.0,
                "raw_value": 3.0,
                "raw_unit": "% YoY",
                "weight": 0.25,
                "polarity": 1,
                "data_date": "2025-12-31",
                "staleness_days": 30,
                "confidence": "HIGH",
                "interpretation": "Inflation near long-run average",
                "history": [50.0, 50.0, 50.0],
            }
        },
        "weights": {"inflation": 0.25},
        "metadata": {
            "window_years": 10,
            "clamp_range": [-3.0, 3.0],
            "mapping": "linear",
            "statistics": "robust (median/MAD)",
            "indicators_available": 1,
            "indicators_missing": [],
        },
    }


# =============================================================================
# Valid document tests
# =============================================================================


def test_valid_status_passes_schema():
    """Minimal valid document passes STATUS_SCHEMA validation without raising."""
    doc = _make_valid_status()
    _validate(doc, STATUS_SCHEMA)  # should not raise


def test_valid_status_with_all_gauges():
    """Document with all 7 gauge entries passes STATUS_SCHEMA validation."""
    doc = _make_valid_status()
    gauge_template = {
        "value": 55.0,
        "zone": "neutral",
        "zone_label": "Balanced",
        "z_score": 0.2,
        "raw_value": 3.5,
        "raw_unit": "% YoY",
        "weight": 0.15,
        "polarity": 1,
        "data_date": "2025-12-31",
        "staleness_days": 30,
        "confidence": "HIGH",
        "interpretation": "Near trend",
        "history": [50.0, 52.0, 55.0],
    }
    indicators = [
        "inflation", "wages", "employment", "spending",
        "building_approvals", "housing", "business_confidence",
    ]
    doc["gauges"] = {name: copy.deepcopy(gauge_template) for name in indicators}
    doc["weights"] = {name: round(1.0 / len(indicators), 4) for name in indicators}

    _validate(doc, STATUS_SCHEMA)  # should not raise


# =============================================================================
# Missing required key tests
# =============================================================================


@pytest.mark.parametrize("missing_key", [
    "generated_at",
    "pipeline_version",
    "overall",
    "gauges",
    "weights",
    "metadata",
])
def test_missing_required_top_level_key(missing_key):
    """Removing each required top-level key raises ValidationError."""
    doc = _make_valid_status()
    del doc[missing_key]
    with pytest.raises(jsonschema.ValidationError):
        _validate(doc, STATUS_SCHEMA)


@pytest.mark.parametrize("missing_key", [
    "hawk_score",
    "zone",
    "zone_label",
    "verdict",
    "confidence",
])
def test_missing_overall_required_key(missing_key):
    """Removing each required overall key raises ValidationError."""
    doc = _make_valid_status()
    del doc["overall"][missing_key]
    with pytest.raises(jsonschema.ValidationError):
        _validate(doc, STATUS_SCHEMA)


# =============================================================================
# Type validation tests
# =============================================================================


def test_hawk_score_must_be_integer():
    """hawk_score=52.0 (float) fails validation — schema requires integer type."""
    doc = _make_valid_status()
    doc["overall"]["hawk_score"] = 52.0  # float, not int
    with pytest.raises(jsonschema.ValidationError):
        _validate(doc, STATUS_SCHEMA)


@pytest.mark.parametrize("out_of_range_value", [-1, 101, 200, -50])
def test_hawk_score_out_of_range(out_of_range_value):
    """hawk_score values outside [0, 100] fail validation."""
    doc = _make_valid_status()
    doc["overall"]["hawk_score"] = out_of_range_value
    with pytest.raises(jsonschema.ValidationError):
        _validate(doc, STATUS_SCHEMA)


@pytest.mark.parametrize("boundary_value", [0, 50, 100])
def test_hawk_score_boundary_values(boundary_value):
    """hawk_score boundary values [0, 50, 100] all pass validation (inclusive range)."""
    doc = _make_valid_status()
    doc["overall"]["hawk_score"] = boundary_value
    _validate(doc, STATUS_SCHEMA)  # should not raise


# =============================================================================
# Enum validation tests
# =============================================================================


def test_invalid_zone_enum():
    """zone='scorching' and zone='COLD' (case-sensitive) both fail validation."""
    # Test unknown zone
    doc = _make_valid_status()
    doc["overall"]["zone"] = "scorching"
    with pytest.raises(jsonschema.ValidationError):
        _validate(doc, STATUS_SCHEMA)

    # Test case-sensitivity: 'COLD' is not in the lowercase enum
    doc2 = _make_valid_status()
    doc2["overall"]["zone"] = "COLD"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc2, STATUS_SCHEMA)


def test_invalid_confidence_enum():
    """confidence='VERY_HIGH' fails validation (not in allowed enum values)."""
    doc = _make_valid_status()
    doc["overall"]["confidence"] = "VERY_HIGH"
    with pytest.raises(jsonschema.ValidationError):
        _validate(doc, STATUS_SCHEMA)


# =============================================================================
# additionalProperties: false on overall section
# =============================================================================


def test_overall_rejects_extra_keys():
    """Extra key in overall section fails validation (additionalProperties: false)."""
    doc = _make_valid_status()
    doc["overall"]["extra_key"] = "foo"
    with pytest.raises(jsonschema.ValidationError):
        _validate(doc, STATUS_SCHEMA)


# =============================================================================
# GAUGE_SCHEMA tests
# =============================================================================


def test_valid_gauge_entry_passes():
    """A single valid gauge entry passes GAUGE_SCHEMA validation."""
    gauge = {
        "value": 50.0,
        "zone": "neutral",
        "zone_label": "Balanced",
        "z_score": 0.0,
        "raw_value": 3.0,
        "raw_unit": "% YoY",
        "weight": 0.25,
        "polarity": 1,
        "data_date": "2025-12-31",
        "staleness_days": 30,
        "confidence": "HIGH",
        "interpretation": "Near trend",
        "history": [50.0, 50.0, 50.0],
    }
    _validate(gauge, GAUGE_SCHEMA)  # should not raise


def test_gauge_value_out_of_range():
    """Gauge value of 150.0 (> 100) fails GAUGE_SCHEMA validation."""
    gauge = {
        "value": 150.0,  # out of range
        "zone": "hot",
        "zone_label": "Strong hawkish pressure",
        "z_score": 2.5,
        "raw_value": 5.0,
        "raw_unit": "% YoY",
        "weight": 0.25,
        "polarity": 1,
        "data_date": "2025-12-31",
        "staleness_days": 30,
        "confidence": "HIGH",
        "interpretation": "Above trend",
        "history": [80.0, 90.0, 100.0],
    }
    with pytest.raises(jsonschema.ValidationError):
        _validate(gauge, GAUGE_SCHEMA)


def test_gauge_invalid_zone_enum():
    """Gauge zone='scorching' fails GAUGE_SCHEMA validation."""
    gauge = {
        "value": 75.0,
        "zone": "scorching",  # invalid
        "zone_label": "Very hot",
        "z_score": 2.0,
        "raw_value": 4.5,
        "raw_unit": "% YoY",
        "weight": 0.25,
        "polarity": 1,
        "data_date": "2025-12-31",
        "staleness_days": 30,
        "confidence": "HIGH",
        "interpretation": "Above trend",
        "history": [70.0, 72.0, 75.0],
    }
    with pytest.raises(jsonschema.ValidationError):
        _validate(gauge, GAUGE_SCHEMA)


# =============================================================================
# Optional key tests (top-level additionalProperties: true)
# =============================================================================


def test_asx_futures_optional_key_allowed():
    """Valid document WITH asx_futures key at top level
    passes (additionalProperties: true at top)."""
    doc = _make_valid_status()
    doc["asx_futures"] = {
        "current_rate": 3.85,
        "next_meeting": "2026-03-03",
        "implied_rate": 3.86,
        "probabilities": {"cut": 0.0, "hold": 100.0, "hike": 0.0},
        "direction": "hold",
        "data_date": "2026-02-23",
        "staleness_days": 1,
        "meetings": [],
    }
    _validate(doc, STATUS_SCHEMA)  # should not raise
