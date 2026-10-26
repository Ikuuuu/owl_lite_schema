"""KG 트리플을 스키마로 검증하고 버전별로 비교한다.

    python scripts/validate_kg.py                                       # data/triples_v1_0.json, v1_1 비교
    python scripts/validate_kg.py --triples data/triples_v1_1.json

산출물 : results/validation_report.md, results/violations_<ver>.json (위반 사례 전체)
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from owlschema.schema import load_schema  # noqa: E402
from owlschema.validator import validate  # noqa: E402

LABELS = [
    ("triples", "전체 트리플"), ("entities", "엔티티"),
    ("C1_type_coverage", "C1 타입 커버리지"),
    ("C2_untyped_endpoint_facts", "C2 타입 미상 끝점 (검사 제외)"),
    ("C2_domain", "C2 domain 위반"), ("C2_range", "C2 range 위반"),
    ("C3_functional", "C3 Functional(소속) 위반"),
    ("C4_inverse_missing", "C4 역관계 누락"),
    ("C5_transitive_implied", "C5 이행 폐포 함의 (미명시)"),
    ("C6_symmetric_pair", "C6 방향성 관계 양방향 쌍"),
    ("C7_self_loop", "C7 자기 루프"),
    ("C8_dangling_article", "C8 미해결 조문 참조"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", default="ontology/schema.json")
    ap.add_argument("--triples", nargs="+", default=["data/triples_v1_0.json", "data/triples_v1_1.json"])
    args = ap.parse_args()

    schema = load_schema(ROOT / args.schema)
    results = {}
    for tp in args.triples:
        triples = [tuple(x) for x in json.loads((ROOT / tp).read_text(encoding="utf-8"))]
        res = validate(schema, triples)
        name = Path(tp).stem.replace("triples_", "")
        results[name] = res
        (ROOT / "results").mkdir(exist_ok=True)
        (ROOT / "results" / f"violations_{name}.json").write_text(
            json.dumps({k: [list(map(str, x)) for x in v] for k, v in res["violations"].items()},
                       ensure_ascii=False, indent=1), encoding="utf-8")

    names = list(results)
    L = ["# KG 스키마 검증 리포트", "", "| 검사 | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for key, label in LABELS:
        cells = []
        for n in names:
            val = results[n]["summary"].get(key, 0)
            cells.append(f"{val * 100:.1f}%" if key == "C1_type_coverage" else f"{val:,}")
        L.append(f"| {label} | " + " | ".join(cells) + " |")
    for n in names:
        vio = results[n]["violations"]
        L += ["", f"## 위반 사례 예시 — {n}", ""]
        for key in ["C2_domain", "C2_range", "C3_functional", "C6_symmetric_pair", "C8_dangling_article",
                    "C5_transitive_implied"]:
            ex = vio.get(key, [])[:3]
            if ex:
                L.append(f"- **{key}** ({len(vio[key])}건)")
                L += [f"  - `{' | '.join(map(str, e))}`" for e in ex]
    (ROOT / "results" / "validation_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:len(LABELS) + 4]))


if __name__ == "__main__":
    main()
