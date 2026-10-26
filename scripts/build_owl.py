"""스키마(JSON) → OWL Turtle 파일 + OWL Lite 프로파일 점검 (+ 선택: KG 인스턴스 포함 RDF).

    python scripts/build_owl.py                                   # ontology/defense_law.ttl
    python scripts/build_owl.py --with-kg data/triples_v1_1.json  # results/defense_law_kg_v1_1.ttl 도 생성
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from owlschema.owl_export import check_owl_lite, kg_to_graph, schema_to_graph  # noqa: E402
from owlschema.schema import load_schema  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", default="ontology/schema.json")
    ap.add_argument("--out", default="ontology/defense_law.ttl")
    ap.add_argument("--with-kg", default=None, help="트리플 JSON 경로 (인스턴스까지 RDF 로 내보내기)")
    args = ap.parse_args()

    schema = load_schema(ROOT / args.schema)
    problems = check_owl_lite(schema)
    print("OWL Lite 프로파일 점검 :", "통과" if not problems else f"{len(problems)}건 위반")
    for p in problems:
        print("  -", p)

    g = schema_to_graph(schema)
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(out), format="turtle")
    print(f"→ {args.out}  (클래스 {len(schema.classes)}개, 속성 {len(schema.properties)}개, RDF 트리플 {len(g)}개)")

    if args.with_kg:
        triples = [tuple(x) for x in json.loads((ROOT / args.with_kg).read_text(encoding="utf-8"))]
        kg = kg_to_graph(schema, triples)
        name = Path(args.with_kg).stem.replace("triples", "defense_law_kg")
        kout = ROOT / "results" / f"{name}.ttl"
        kout.parent.mkdir(exist_ok=True)
        kg.serialize(destination=str(kout), format="turtle")
        print(f"→ results/{kout.name}  (RDF 트리플 {len(kg):,}개)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
