"""스키마·검증기 단위 테스트.  python -m pytest -q"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from owlschema.owl_export import check_owl_lite  # noqa: E402
from owlschema.schema import load_schema  # noqa: E402
from owlschema.validator import validate  # noqa: E402

S = load_schema(ROOT / "ontology" / "schema.json")


def test_owl_lite_profile():
    assert check_owl_lite(S) == []


def test_class_hierarchy():
    assert S.is_subclass("JointAdministrativeOrder", "LegalDocument")
    assert S.is_subclass("Article", "LegalResource")
    assert not S.is_subclass("Organization", "LegalResource")


def test_inverse_declared_both_ways():
    for r, p in S.properties.items():
        if p.get("inverse"):
            assert S.inverse(p["inverse"]) == r


def test_validator_detects_violations():
    T = [
        ("A법", "type", "Law"), ("B규정", "type", "AdministrativeOrder"), ("C법", "type", "Law"),
        ("A법 제1조", "type", "Article"), ("국방부", "type", "Organization"),
        ("A법 제1조", "소속", "A법"), ("A법", "포함", "A법 제1조"),
        ("A법 제1조", "소속", "C법"),                 # C3 Functional 위반 (+ C4 역관계 누락)
        ("B규정", "상위법령", "A법"),                  # C4 역관계 누락
        ("A법", "상위법령", "C법"), ("C법", "하위법령", "A법"),   # → C5: B규정 상위법령 C법 함의
        ("A법", "소관기관", "B규정"),                  # C2 range 위반 (Organization 이어야 함)
        ("A법 제1조", "인용", "C법 제9조"),             # C8 미해결 조문
    ]
    s = validate(S, T)["summary"]
    assert s["C3_functional"] == 1
    assert s["C2_range"] == 1
    assert s["C5_transitive_implied"] == 1
    assert s["C8_dangling_article"] == 1
    assert s["C4_inverse_missing"] >= 2
