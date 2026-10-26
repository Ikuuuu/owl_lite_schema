# owl_lite_schema — 국방 법령 KG 온톨로지 (OWL Lite) 설계 · 검증

> 졸업논문 **Part 1 · 데이터셋 구축 (RQ1: 한국어 공공 도메인 KG에 맞는 온톨로지 스키마)**
> 법령·조문·기관을 OWL Lite 클래스로 정의하고, 관계 11종의 domain/range와 속성 특성(inverseOf, Transitive, Functional)을 선언합니다. 이 스키마로 추출된 KG의 정합성을 자동 검증하고 RDF(Turtle)로 내보냅니다.

## 1. 왜 OWL Lite 인가

| 비교 | RDFS | **OWL Lite** (채택) | OWL DL / OWL 2 |
|---|---|---|---|
| 클래스 계층, domain/range | O | O | O |
| inverseOf, Transitive, Functional, Symmetric | X | **O** | O |
| unionOf, disjointWith, Asymmetric | X | X | O |
| 소규모 KG 임베딩 손실로 바꾸기 쉬운가 | 쉬움 | **쉬움** | 어려움 |

본 연구의 임베딩 손실은 온톨로지에서 바로 나옵니다.

| 스키마 요소 | 임베딩 손실 ([ontology_constraint_kge](https://github.com/Ikuuuu/ontology_constraint_kge)) |
|---|---|
| `rdf:type` + `rdfs:subClassOf` | `L_type` (같은 클래스 엔티티 응집) |
| `owl:inverseOf` | `L_attr` (역관계 점수 일관성) |
| `owl:TransitiveProperty` (상위법령) | `L_hier_attn` (계층 관계 적응 가중) |
| 방향성 관계 (비대칭 힌트) | `L_dir` (방향 뒤집힌 트리플 억제) |

그래서 표현력보다 **손실로 옮길 수 있는가**를 기준으로 OWL Lite를 골랐습니다. OWL Lite에는 `unionOf`가 없어서, 법령과 조문을 모두 가리키는 `인용` 관계의 range를 공통 상위 클래스 `LegalResource`로 두었습니다. 비대칭성(AsymmetricProperty)은 OWL 2 구성요소라서 스키마에는 `asymmetric_hint`로만 적고 검증·학습 단계에서 씁니다.

## 2. 스키마

### 클래스 계층 (14개)

```
LegalResource
├── LegalDocument
│   ├── Law                    법률
│   ├── EnforcementOrdinance   시행령(대통령령)
│   ├── EnforcementRule        시행규칙(부령)
│   ├── SpecialRegulation      특례규정
│   ├── AdministrativeOrder    행정규칙(훈령·규정)
│   │   └── JointAdministrativeOrder  공동훈령
│   └── ExternalLegalDocument  말뭉치 외부 법령
└── TextUnit
    ├── Article                조문
    └── AddendumArticle        부칙 조문
Agent
└── Organization               기관
```

### 속성 (11개)

| 관계 | IRI | domain → range | 특성 | inverseOf |
|---|---|---|---|---|
| 소속 | belongsTo | Article → LegalDocument | Functional | 포함 |
| 포함 | contains | LegalDocument → Article | InverseFunctional | 소속 |
| 인용 | cites | TextUnit → LegalResource | – | – |
| 외부인용 | citesExternal | TextUnit → ExternalLegalDocument | – | – |
| 상위법령 | parentLaw | LegalDocument → LegalDocument | Transitive | 하위법령 |
| 하위법령 | childLaw | LegalDocument → LegalDocument | Transitive | 상위법령 |
| 위임 | delegates | LegalDocument → LegalDocument | – | 위임받음 |
| 위임받음 | delegatedBy | LegalDocument → LegalDocument | – | 위임 |
| 소관기관 | competentAuthority | LegalDocument → Organization | – | 관할법령 |
| 관할법령 | governingLaw | Organization → LegalDocument | – | 소관기관 |
| 발령기관 | issuedBy | LegalDocument → Organization | – | – |

## 3. 폴더 구조

```
owl_lite_schema/
├── ontology/
│   ├── schema.json          # 스키마 원본 (사람이 편집)
│   └── defense_law.ttl      # OWL Turtle (자동 생성, Protégé 로 열람 가능)
├── owlschema/
│   ├── schema.py            # 스키마 로드, 클래스 계층 질의
│   ├── owl_export.py        # OWL Lite 프로파일 점검, Turtle 변환, KG → RDF
│   └── validator.py         # 정합성 검사 C1~C8
├── scripts/
│   ├── build_owl.py         # schema.json → .ttl (+ KG 인스턴스 RDF)
│   └── validate_kg.py       # 트리플 검증 + 버전 비교 리포트
├── data/                    # triples_v1_0.json (논문), triples_v1_1.json (개선)
├── results/                 # validation_report.md, violations_*.json, defense_law_kg_v1_1.ttl
└── tests/test_schema.py
```

## 4. 실행 방법

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/build_owl.py                                    # OWL Lite 점검 + ontology/defense_law.ttl
python scripts/build_owl.py --with-kg data/triples_v1_1.json   # KG 전체를 RDF 로 (results/*.ttl)
python scripts/validate_kg.py                                  # v1.0 / v1.1 정합성 비교
python -m pytest -q
```

생성된 `ontology/defense_law.ttl`과 `results/defense_law_kg_v1_1.ttl`은 Protégé, GraphDB, Apache Jena 같은 표준 도구에서 바로 열 수 있습니다.

## 5. 결과 (`results/validation_report.md`)

| 검사 | v1.0 (논문 데이터셋) | v1.1 |
|---|---|---|
| 전체 트리플 | 7,354 | 8,327 |
| C1 타입 커버리지 | 100% | 100% |
| C2 domain / range 위반 | 0 / **1** | 0 / 0 |
| C3 Functional(소속) 위반 | 0 | 0 |
| C4 역관계 누락 | 0 | 0 |
| C5 이행 폐포로 함의되지만 빠진 트리플 | 56 | 14 |
| C6 방향성 관계 양방향 쌍 | **4** | 2 |
| C7 자기 루프 / C8 미해결 조문 참조 | 0 / 0 | 0 / 0 |

발견한 내용

- **v1.0 의 상호 위임 오류** : `국방과학기술혁신 촉진법 ⇄ 방위사업법` 이 서로 위임하는 것으로 추출되어 있었습니다(C6). 법률끼리는 위임 관계가 성립하지 않으므로, [law_triple_extraction](https://github.com/Ikuuuu/law_triple_extraction) v1.1 에 법령 위계 검증을 넣어 없앴습니다.
- **range 위반 1건(v1.0)** : 말뭉치 안 법령(`방위산업에 관한 착수금 및 중도금 지급규칙`)이 표기 변이 때문에 외부 법령으로 잘못 분류된 경우입니다. v1.1 정규화로 해결했습니다.
- **C6 잔여 2건(v1.1)** : 서로 다른 두 법령의 조문이 서로를 인용하는 경우로, 실제 법령 구조상 가능한 정상 사례입니다.
- **C5 이행 폐포** : `훈령 → 시행령 → 법률` 연쇄에서 `훈령 → 법률`이 명시되지 않은 경우입니다. 위반이 아니라 추론으로 늘릴 수 있는 학습 데이터 후보이며, 소규모 KG 데이터 증강 실험에 활용할 수 있습니다.

## 6. 관련 저장소

[law_pdf_parser](https://github.com/Ikuuuu/law_pdf_parser) → **owl_lite_schema** → [law_triple_extraction](https://github.com/Ikuuuu/law_triple_extraction) → [defense_law_kg_dataset](https://github.com/Ikuuuu/defense_law_kg_dataset) → [ontology_constraint_kge](https://github.com/Ikuuuu/ontology_constraint_kge)

---
송재익 · 충북대학교 산업인공지능학과 석사과정 (2025254013)
