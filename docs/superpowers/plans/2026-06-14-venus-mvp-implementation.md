# Venus MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first local, testable Venus MVP that can generate hotspot briefs, product research cards, persona-guided scripts, comment reply drafts, approval logs, and backup metadata without touching live platform accounts.

**Architecture:** A Python package under `src/venus` with focused modules for models, local JSON storage, persona memory, content intelligence, product research, comment analysis, approval logging, backup metadata, and a CLI orchestrator. The first slice is deterministic and evidence-driven so it can pass smoke tests without external API credentials; later plans can swap in OpenAI Agents SDK and platform connectors behind these interfaces.

**Tech Stack:** Python 3.11+, standard library dataclasses/json/argparse/pathlib, pytest for tests, local JSON fixtures, CLI entrypoint.

---

## Scope Check

The approved system design covers many independent subsystems: Douyin APIs, Qianchuan, Xingtu, Feishu, WeChat Mini Program, Enterprise WeChat, Airtable, dashboards, backups, and self-improvement. This implementation plan covers only the first working slice:

- Local command-line Venus MVP
- Three core workflows: hotspot to script, product research, persona learning
- Comment analysis and approval-gated reply drafts
- Evidence bundles, approval logs, backup metadata, and Xiaolongxia isolation checks

Separate plans should cover:

- Feishu application bot integration
- Airtable sync
- Douyin comment and publishing connectors
- Qianchuan/OceanEngine/Xingtu integrations
- WeChat Mini Program and Enterprise WeChat flows
- Analytics dashboards and recurring monitors

## File Structure

Create this structure:

```text
.
├── .env.example
├── .gitignore
├── README.md
├── pyproject.toml
├── data/
│   ├── samples/
│   │   ├── comments.json
│   │   ├── hotspots.json
│   │   ├── persona_samples.json
│   │   └── products.json
│   └── venus/
│       └── .gitkeep
├── src/
│   └── venus/
│       ├── __init__.py
│       ├── approvals.py
│       ├── backups.py
│       ├── cli.py
│       ├── comments.py
│       ├── content.py
│       ├── models.py
│       ├── orchestrator.py
│       ├── persona.py
│       ├── product_research.py
│       └── storage.py
└── tests/
    ├── conftest.py
    ├── test_approvals_backups.py
    ├── test_cli_smoke.py
    ├── test_comments.py
    ├── test_content.py
    ├── test_persona.py
    ├── test_product_research.py
    └── test_storage.py
```

Responsibilities:

- `models.py`: shared dataclasses and constants.
- `storage.py`: isolated local JSON read/write with `VENUS_` namespace rules.
- `persona.py`: build and apply the user's style profile.
- `content.py`: hotspot scoring and script pack generation.
- `product_research.py`: evidence-ranked product research cards.
- `comments.py`: comment classification and approval-gated reply drafts.
- `approvals.py`: approval records and policy enforcement.
- `backups.py`: backup metadata and verification status records.
- `orchestrator.py`: workflow router.
- `cli.py`: command-line interface for smoke workflows.
- `data/samples/*.json`: deterministic sample inputs for tests and demos.

---

### Task 1: Project Scaffold And Tooling

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`
- Create: `src/venus/__init__.py`
- Create: `data/venus/.gitkeep`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create the failing packaging smoke test**

Create `tests/conftest.py`:

```python
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "venus-workspace"
    workspace.mkdir()
    return workspace
```

Create `tests/test_storage.py`:

```python
from venus.storage import VenusPaths


def test_venus_paths_use_isolated_namespace(tmp_workspace):
    paths = VenusPaths(root=tmp_workspace)

    assert paths.root == tmp_workspace
    assert paths.data_dir == tmp_workspace / "data" / "venus"
    assert paths.logs_dir == tmp_workspace / "logs" / "venus"
    assert paths.env_prefix == "VENUS_"
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
pytest tests/test_storage.py::test_venus_paths_use_isolated_namespace -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'venus'`.

- [ ] **Step 3: Add Python packaging metadata**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "venus-agent"
version = "0.1.0"
description = "Local MVP for the Venus beauty and skincare agent system."
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
venus = "venus.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 4: Add repository hygiene files**

Create `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
.pytest_cache/
*.pyc
data/venus/*
!data/venus/.gitkeep
logs/
*.sqlite
*.db
```

Create `.env.example`:

```bash
VENUS_DATA_DIR=./data/venus
VENUS_LOG_DIR=./logs/venus
VENUS_APPROVAL_MODE=manual
VENUS_OPENAI_MODEL=gpt-5
```

Create `README.md`:

````markdown
# Venus

Venus is a beauty and skincare agent system for content intelligence, product research, persona learning, approval-gated reply drafting, and future platform integrations.

The first implementation slice runs locally and does not touch live Douyin, Feishu, WeChat, Qianchuan, Xingtu, Airtable, or Enterprise WeChat accounts.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Smoke Commands

```bash
venus hotspot data/samples/hotspots.json
venus product data/samples/products.json
venus comments data/samples/comments.json
```
````

- [ ] **Step 5: Create package marker and data directory marker**

Create `src/venus/__init__.py`:

```python
"""Venus local MVP package."""

__all__ = ["__version__"]

__version__ = "0.1.0"
```

Create `data/venus/.gitkeep` as an empty file.

- [ ] **Step 6: Run packaging test again**

Run:

```bash
pytest tests/test_storage.py::test_venus_paths_use_isolated_namespace -v
```

Expected: FAIL with `ModuleNotFoundError` or `ImportError` for `venus.storage` because `storage.py` is not created yet.

- [ ] **Step 7: Commit scaffold**

Run:

```bash
git add pyproject.toml .gitignore .env.example README.md src/venus/__init__.py data/venus/.gitkeep tests/conftest.py tests/test_storage.py
git commit -m "chore: scaffold Venus Python project"
```

---

### Task 2: Shared Models And Isolated Storage

**Files:**
- Create: `src/venus/models.py`
- Create: `src/venus/storage.py`
- Modify: `tests/test_storage.py`

- [ ] **Step 1: Extend storage tests**

Replace `tests/test_storage.py` with:

```python
from venus.models import Evidence
from venus.storage import JsonStore, VenusPaths


def test_venus_paths_use_isolated_namespace(tmp_workspace):
    paths = VenusPaths(root=tmp_workspace)

    assert paths.root == tmp_workspace
    assert paths.data_dir == tmp_workspace / "data" / "venus"
    assert paths.logs_dir == tmp_workspace / "logs" / "venus"
    assert paths.env_prefix == "VENUS_"


def test_json_store_round_trips_records(tmp_workspace):
    store = JsonStore(tmp_workspace)
    evidence = Evidence(
        source_id="nmpa-001",
        source_type="regulator",
        title="NMPA cosmetics filing lookup",
        url="https://www.nmpa.gov.cn/datasearch/home-index.html",
        retrieved_at="2026-06-14T00:00:00+08:00",
        confidence="high",
        notes=["Official regulator source"],
    )

    store.write_collection("sources", [evidence.to_dict()])

    records = store.read_collection("sources")
    assert records == [evidence.to_dict()]
    assert (tmp_workspace / "data" / "venus" / "sources.json").exists()


def test_json_store_rejects_xiaolongxia_collection_name(tmp_workspace):
    store = JsonStore(tmp_workspace)

    try:
        store.write_collection("xiaolongxia_secrets", [])
    except ValueError as exc:
        assert "Xiaolongxia" in str(exc)
    else:
        raise AssertionError("Expected Xiaolongxia isolation guard to reject collection")
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pytest tests/test_storage.py -v
```

Expected: FAIL because `venus.models`, `VenusPaths`, and `JsonStore` are not implemented.

- [ ] **Step 3: Implement shared models**

Create `src/venus/models.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Confidence = Literal["low", "medium", "high"]
RiskLevel = Literal["low", "medium", "high", "critical"]
ApprovalLevel = Literal[0, 1, 2, 3, 4]


@dataclass(frozen=True)
class Evidence:
    source_id: str
    source_type: str
    title: str
    url: str
    retrieved_at: str
    confidence: Confidence
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RiskTag:
    label: str
    level: RiskLevel
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovalRecord:
    action_type: str
    approval_level: ApprovalLevel
    draft: str
    evidence_ids: list[str]
    status: str
    reviewer: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

- [ ] **Step 4: Implement isolated JSON storage**

Create `src/venus/storage.py`:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VenusPaths:
    root: Path
    env_prefix: str = "VENUS_"

    @property
    def data_dir(self) -> Path:
        return self.root / "data" / "venus"

    @property
    def logs_dir(self) -> Path:
        return self.root / "logs" / "venus"


class JsonStore:
    def __init__(self, root: Path | str):
        self.paths = VenusPaths(Path(root))
        self.paths.data_dir.mkdir(parents=True, exist_ok=True)
        self.paths.logs_dir.mkdir(parents=True, exist_ok=True)

    def read_collection(self, name: str) -> list[dict[str, Any]]:
        self._validate_collection_name(name)
        path = self._collection_path(name)
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def write_collection(self, name: str, records: list[dict[str, Any]]) -> None:
        self._validate_collection_name(name)
        path = self._collection_path(name)
        path.write_text(
            json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def append_record(self, name: str, record: dict[str, Any]) -> None:
        records = self.read_collection(name)
        records.append(record)
        self.write_collection(name, records)

    def _collection_path(self, name: str) -> Path:
        return self.paths.data_dir / f"{name}.json"

    def _validate_collection_name(self, name: str) -> None:
        lowered = name.lower()
        if "xiaolongxia" in lowered or "小龙虾" in name:
            raise ValueError("Venus storage must not read or write Xiaolongxia collections")
        if not name.replace("_", "").isalnum():
            raise ValueError(f"Invalid Venus collection name: {name}")
```

- [ ] **Step 5: Run storage tests**

Run:

```bash
pytest tests/test_storage.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit models and storage**

Run:

```bash
git add src/venus/models.py src/venus/storage.py tests/test_storage.py
git commit -m "feat: add Venus models and isolated storage"
```

---

### Task 3: Persona Profile

**Files:**
- Create: `src/venus/persona.py`
- Create: `tests/test_persona.py`
- Create: `data/samples/persona_samples.json`

- [ ] **Step 1: Write persona tests**

Create `tests/test_persona.py`:

```python
from venus.persona import PersonaProfile, build_persona_profile, rewrite_in_persona


def test_build_persona_profile_extracts_style_rules():
    samples = [
        "姐妹们，别一上来就追猛药，先看自己的屏障状态。",
        "这个成分不是不能用，而是要看浓度、搭配和你的皮肤耐受。",
        "我不喜欢把护肤讲成玄学，证据和体验都要说清楚。",
    ]

    profile = build_persona_profile(samples)

    assert "先看屏障状态" in profile.principles
    assert "证据和体验都要说清楚" in profile.principles
    assert "姐妹们" in profile.preferred_phrases
    assert "包治" in profile.banned_claims


def test_rewrite_in_persona_adds_style_and_boundaries():
    profile = PersonaProfile(
        principles=["先看屏障状态", "证据和体验都要说清楚"],
        preferred_phrases=["姐妹们"],
        banned_claims=["包治", "根治", "100%有效"],
        tone="专业、口语化、克制",
    )

    draft = "这个产品可以修护皮肤。"

    rewritten = rewrite_in_persona(draft, profile)

    assert rewritten.startswith("姐妹们，")
    assert "先看屏障状态" in rewritten
    assert "包治" not in rewritten
    assert "100%有效" not in rewritten
```

- [ ] **Step 2: Run persona tests and verify failure**

Run:

```bash
pytest tests/test_persona.py -v
```

Expected: FAIL because `venus.persona` does not exist.

- [ ] **Step 3: Implement persona profile**

Create `src/venus/persona.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PersonaProfile:
    principles: list[str]
    preferred_phrases: list[str]
    banned_claims: list[str]
    tone: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_persona_profile(samples: list[str]) -> PersonaProfile:
    joined = "\n".join(samples)
    principles: list[str] = []
    preferred_phrases: list[str] = []

    if "屏障" in joined:
        principles.append("先看屏障状态")
    if "证据" in joined or "体验" in joined:
        principles.append("证据和体验都要说清楚")
    if "姐妹们" in joined:
        preferred_phrases.append("姐妹们")

    if not principles:
        principles.append("先判断肤质和使用场景")
    if not preferred_phrases:
        preferred_phrases.append("姐妹们")

    return PersonaProfile(
        principles=principles,
        preferred_phrases=preferred_phrases,
        banned_claims=["包治", "根治", "100%有效", "永久解决"],
        tone="专业、口语化、克制",
    )


def rewrite_in_persona(draft: str, profile: PersonaProfile) -> str:
    cleaned = draft
    for claim in profile.banned_claims:
        cleaned = cleaned.replace(claim, "")

    opener = profile.preferred_phrases[0] if profile.preferred_phrases else "姐妹们"
    principle = profile.principles[0] if profile.principles else "先判断肤质和使用场景"
    return f"{opener}，{cleaned}但我会先提醒一句：{principle}，再看证据和自己的耐受。"
```

- [ ] **Step 4: Add persona sample fixture**

Create `data/samples/persona_samples.json`:

```json
[
  "姐妹们，别一上来就追猛药，先看自己的屏障状态。",
  "这个成分不是不能用，而是要看浓度、搭配和你的皮肤耐受。",
  "我不喜欢把护肤讲成玄学，证据和体验都要说清楚。"
]
```

- [ ] **Step 5: Run persona tests**

Run:

```bash
pytest tests/test_persona.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit persona module**

Run:

```bash
git add src/venus/persona.py tests/test_persona.py data/samples/persona_samples.json
git commit -m "feat: add Venus persona profile"
```

---

### Task 4: Content Intelligence Core

**Files:**
- Create: `src/venus/content.py`
- Create: `tests/test_content.py`
- Create: `data/samples/hotspots.json`

- [ ] **Step 1: Write content tests**

Create `tests/test_content.py`:

```python
from venus.content import generate_hotspot_brief
from venus.persona import PersonaProfile


def test_generate_hotspot_brief_ranks_topics_and_scripts():
    profile = PersonaProfile(
        principles=["先看屏障状态", "证据和体验都要说清楚"],
        preferred_phrases=["姐妹们"],
        banned_claims=["包治", "根治", "100%有效"],
        tone="专业、口语化、克制",
    )
    hotspots = [
        {
            "topic": "早C晚A翻车",
            "type": "controversy",
            "freshness": 9,
            "relevance": 10,
            "controversy": 8,
            "evidence": ["douyin-export-001"],
        },
        {
            "topic": "夏季防晒补涂",
            "type": "routine",
            "freshness": 7,
            "relevance": 8,
            "controversy": 3,
            "evidence": ["manual-note-002"],
        },
    ]

    brief = generate_hotspot_brief(hotspots, profile)

    assert brief["top_topic"] == "早C晚A翻车"
    assert brief["ranked"][0]["score"] > brief["ranked"][1]["score"]
    assert brief["risk_tags"][0]["label"] == "争议话题"
    assert len(brief["scripts"]) == 3
    assert brief["scripts"][0]["hook"].startswith("姐妹们")
    assert "证据" in brief["analysis"]
```

- [ ] **Step 2: Run content tests and verify failure**

Run:

```bash
pytest tests/test_content.py -v
```

Expected: FAIL because `venus.content` does not exist.

- [ ] **Step 3: Implement content intelligence**

Create `src/venus/content.py`:

```python
from __future__ import annotations

from typing import Any

from venus.persona import PersonaProfile, rewrite_in_persona


def score_hotspot(item: dict[str, Any]) -> int:
    return int(item.get("freshness", 0)) * 3 + int(item.get("relevance", 0)) * 4 + int(item.get("controversy", 0)) * 2


def generate_hotspot_brief(hotspots: list[dict[str, Any]], profile: PersonaProfile) -> dict[str, Any]:
    if not hotspots:
        raise ValueError("At least one hotspot is required")

    ranked = sorted(
        [{**item, "score": score_hotspot(item)} for item in hotspots],
        key=lambda item: item["score"],
        reverse=True,
    )
    top = ranked[0]
    topic = top["topic"]
    risk_tags = []
    if int(top.get("controversy", 0)) >= 7:
        risk_tags.append({"label": "争议话题", "level": "high", "reason": "争议分高，需要证据和克制表达"})
    else:
        risk_tags.append({"label": "常规选题", "level": "low", "reason": "争议分较低，适合科普表达"})

    base = f"{topic}可以切入，但要把证据、肤质差异和使用场景讲清楚。"
    persona_line = rewrite_in_persona(base, profile)
    scripts = [
        {
            "hook": f"{profile.preferred_phrases[0]}，{topic}最近又吵起来了，但真正该看的不是情绪。",
            "body": persona_line,
            "cta": "你们把自己的肤质和正在用的搭配打在评论区，我帮你们拆风险。",
        },
        {
            "hook": f"别急着跟风{topic}，先用30秒判断你适不适合。",
            "body": f"第一看屏障，第二看频率，第三看有没有同类功效叠加。{base}",
            "cta": "收藏这条，下次买之前先对照。",
        },
        {
            "hook": f"{topic}不是不能讲，关键是别把护肤讲成玄学。",
            "body": f"我会把支持证据、争议点和适合人群分开说。{persona_line}",
            "cta": "想看我拆哪款产品，评论区留名字。",
        },
    ]

    return {
        "top_topic": topic,
        "analysis": f"围绕{topic}做内容，重点是证据、肤质差异和评论互动。",
        "filming_advice": "开头直接抛争议，中段给判断框架，结尾引导用户留下肤质和产品名。",
        "ranked": ranked,
        "risk_tags": risk_tags,
        "scripts": scripts,
        "evidence_ids": list(top.get("evidence", [])),
    }
```

- [ ] **Step 4: Add hotspot sample fixture**

Create `data/samples/hotspots.json`:

```json
[
  {
    "topic": "早C晚A翻车",
    "type": "controversy",
    "freshness": 9,
    "relevance": 10,
    "controversy": 8,
    "evidence": ["douyin-export-001"]
  },
  {
    "topic": "夏季防晒补涂",
    "type": "routine",
    "freshness": 7,
    "relevance": 8,
    "controversy": 3,
    "evidence": ["manual-note-002"]
  }
]
```

- [ ] **Step 5: Run content tests**

Run:

```bash
pytest tests/test_content.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit content core**

Run:

```bash
git add src/venus/content.py tests/test_content.py data/samples/hotspots.json
git commit -m "feat: add content intelligence core"
```

---

### Task 5: Product Research Core

**Files:**
- Create: `src/venus/product_research.py`
- Create: `tests/test_product_research.py`
- Create: `data/samples/products.json`

- [ ] **Step 1: Write product research tests**

Create `tests/test_product_research.py`:

```python
from venus.product_research import build_product_research_card


def test_build_product_research_card_separates_evidence_and_safe_claims():
    product = {
        "brand": "示例品牌",
        "name": "屏障修护精华",
        "filing_id": "国妆网备字20260001",
        "ingredients": ["烟酰胺", "泛醇", "神经酰胺NP"],
        "claims": ["修护", "维稳", "100%修复屏障"],
        "supplier_docs": ["泛醇供应商COA"],
        "controversies": ["用户反馈刺痛"],
        "evidence": [
            {"id": "nmpa-001", "type": "regulator", "title": "备案查询", "confidence": "high"},
            {"id": "ugc-001", "type": "social", "title": "用户评论截图", "confidence": "medium"}
        ],
    }

    card = build_product_research_card(product)

    assert card["product"] == "示例品牌 屏障修护精华"
    assert card["sections"]["filing"]["status"] == "has_filing_id"
    assert "100%修复屏障" in card["forbidden_claims"]
    assert "可以说支持屏障护理，但不要承诺修复结果" in card["safe_talking_points"]
    assert card["risk_level"] == "high"
```

- [ ] **Step 2: Run product tests and verify failure**

Run:

```bash
pytest tests/test_product_research.py -v
```

Expected: FAIL because `venus.product_research` does not exist.

- [ ] **Step 3: Implement product research**

Create `src/venus/product_research.py`:

```python
from __future__ import annotations

from typing import Any

ABSOLUTE_CLAIM_MARKERS = ["100%", "根治", "包治", "永久", "一定"]


def build_product_research_card(product: dict[str, Any]) -> dict[str, Any]:
    brand = product.get("brand", "").strip()
    name = product.get("name", "").strip()
    filing_id = product.get("filing_id", "").strip()
    ingredients = list(product.get("ingredients", []))
    claims = list(product.get("claims", []))
    controversies = list(product.get("controversies", []))
    supplier_docs = list(product.get("supplier_docs", []))
    evidence = list(product.get("evidence", []))

    forbidden_claims = [
        claim
        for claim in claims
        if any(marker in claim for marker in ABSOLUTE_CLAIM_MARKERS)
    ]
    risk_level = "high" if forbidden_claims or controversies else "medium"
    if filing_id and not forbidden_claims and not controversies:
        risk_level = "low"

    safe_talking_points = [
        "可以说支持屏障护理，但不要承诺修复结果",
        "把成分作用、适合人群和可能不耐受情况分开讲",
        "涉及功效宣称时提醒以备案、检测和个人耐受为准",
    ]

    return {
        "product": f"{brand} {name}".strip(),
        "risk_level": risk_level,
        "sections": {
            "filing": {
                "status": "has_filing_id" if filing_id else "missing_filing_id",
                "filing_id": filing_id,
            },
            "ingredients": {
                "items": ingredients,
                "notes": ["需要结合浓度、配方体系和使用场景判断"],
            },
            "claims": {
                "items": claims,
                "forbidden": forbidden_claims,
            },
            "supplier_testing": {
                "documents": supplier_docs,
                "status": "provided" if supplier_docs else "missing",
            },
            "controversy": {
                "items": controversies,
                "status": "has_controversy" if controversies else "none_recorded",
            },
        },
        "evidence": evidence,
        "safe_talking_points": safe_talking_points,
        "forbidden_claims": forbidden_claims,
    }
```

- [ ] **Step 4: Add product sample fixture**

Create `data/samples/products.json`:

```json
[
  {
    "brand": "示例品牌",
    "name": "屏障修护精华",
    "filing_id": "国妆网备字20260001",
    "ingredients": ["烟酰胺", "泛醇", "神经酰胺NP"],
    "claims": ["修护", "维稳", "100%修复屏障"],
    "supplier_docs": ["泛醇供应商COA"],
    "controversies": ["用户反馈刺痛"],
    "evidence": [
      {"id": "nmpa-001", "type": "regulator", "title": "备案查询", "confidence": "high"},
      {"id": "ugc-001", "type": "social", "title": "用户评论截图", "confidence": "medium"}
    ]
  }
]
```

- [ ] **Step 5: Run product tests**

Run:

```bash
pytest tests/test_product_research.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit product core**

Run:

```bash
git add src/venus/product_research.py tests/test_product_research.py data/samples/products.json
git commit -m "feat: add product research core"
```

---

### Task 6: Comment Analysis And Approval Drafts

**Files:**
- Create: `src/venus/comments.py`
- Create: `src/venus/approvals.py`
- Create: `tests/test_comments.py`
- Create: `tests/test_approvals_backups.py`
- Create: `data/samples/comments.json`

- [ ] **Step 1: Write comment and approval tests**

Create `tests/test_comments.py`:

```python
from venus.comments import analyze_comments
from venus.persona import PersonaProfile


def test_analyze_comments_classifies_risk_and_drafts_replies():
    profile = PersonaProfile(
        principles=["先看屏障状态"],
        preferred_phrases=["姐妹们"],
        banned_claims=["包治", "根治", "100%有效"],
        tone="专业、口语化、克制",
    )
    comments = [
        {"id": "c1", "text": "敏感肌用了会不会烂脸？"},
        {"id": "c2", "text": "这个是不是100%能修复屏障？"},
        {"id": "c3", "text": "求平价替代！"},
    ]

    result = analyze_comments(comments, profile)

    assert result["summary"]["total"] == 3
    assert result["items"][1]["risk"] == "high"
    assert result["items"][1]["approval_level"] == 3
    assert result["items"][0]["draft_reply"].startswith("姐妹们")
    assert "100%有效" not in result["items"][1]["draft_reply"]
```

Create `tests/test_approvals_backups.py`:

```python
from venus.approvals import create_approval_record, requires_manual_approval


def test_approval_policy_requires_manual_review_for_public_reply():
    assert requires_manual_approval(3) is True
    assert requires_manual_approval(1) is False


def test_create_approval_record_defaults_to_pending():
    record = create_approval_record(
        action_type="douyin_comment_reply",
        approval_level=3,
        draft="姐妹们，先看屏障状态。",
        evidence_ids=["comment-c1"],
        reviewer="user",
        created_at="2026-06-14T12:00:00+08:00",
    )

    assert record["status"] == "pending"
    assert record["approval_level"] == 3
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pytest tests/test_comments.py tests/test_approvals_backups.py -v
```

Expected: FAIL because `venus.comments` and `venus.approvals` do not exist.

- [ ] **Step 3: Implement approval helpers**

Create `src/venus/approvals.py`:

```python
from __future__ import annotations

from venus.models import ApprovalRecord


def requires_manual_approval(approval_level: int) -> bool:
    return approval_level >= 2


def create_approval_record(
    action_type: str,
    approval_level: int,
    draft: str,
    evidence_ids: list[str],
    reviewer: str,
    created_at: str,
) -> dict:
    record = ApprovalRecord(
        action_type=action_type,
        approval_level=approval_level,  # type: ignore[arg-type]
        draft=draft,
        evidence_ids=evidence_ids,
        status="pending",
        reviewer=reviewer,
        created_at=created_at,
    )
    return record.to_dict()
```

- [ ] **Step 4: Implement comment analysis**

Create `src/venus/comments.py`:

```python
from __future__ import annotations

from typing import Any

from venus.persona import PersonaProfile, rewrite_in_persona


HIGH_RISK_TERMS = ["烂脸", "过敏", "激素", "100%", "根治", "包治", "修复屏障"]


def analyze_comments(comments: list[dict[str, Any]], profile: PersonaProfile) -> dict[str, Any]:
    items = []
    for comment in comments:
        text = str(comment.get("text", ""))
        risk = "high" if any(term in text for term in HIGH_RISK_TERMS) else "medium"
        approval_level = 3 if risk == "high" else 1
        intent = _classify_intent(text)
        draft = rewrite_in_persona(_base_reply(intent), profile)
        items.append(
            {
                "id": comment.get("id"),
                "text": text,
                "intent": intent,
                "risk": risk,
                "approval_level": approval_level,
                "draft_reply": draft,
            }
        )

    return {
        "summary": {
            "total": len(items),
            "high_risk": sum(1 for item in items if item["risk"] == "high"),
            "approval_gated": sum(1 for item in items if item["approval_level"] >= 2),
        },
        "items": items,
    }


def _classify_intent(text: str) -> str:
    if "会不会" in text or "是不是" in text:
        return "risk_question"
    if "平价" in text or "替代" in text:
        return "shopping_advice"
    return "general_comment"


def _base_reply(intent: str) -> str:
    if intent == "risk_question":
        return "这个问题不能一刀切，要看肤质、屏障状态、使用频率和搭配。"
    if intent == "shopping_advice":
        return "先看你要解决的核心问题，再看预算和耐受，不要只看热门。"
    return "我会先看证据，再结合使用场景判断。"
```

- [ ] **Step 5: Add comment sample fixture**

Create `data/samples/comments.json`:

```json
[
  {"id": "c1", "text": "敏感肌用了会不会烂脸？"},
  {"id": "c2", "text": "这个是不是100%能修复屏障？"},
  {"id": "c3", "text": "求平价替代！"}
]
```

- [ ] **Step 6: Run comment and approval tests**

Run:

```bash
pytest tests/test_comments.py tests/test_approvals_backups.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit comment and approval modules**

Run:

```bash
git add src/venus/comments.py src/venus/approvals.py tests/test_comments.py tests/test_approvals_backups.py data/samples/comments.json
git commit -m "feat: add comment analysis and approvals"
```

---

### Task 7: Backup Metadata

**Files:**
- Create: `src/venus/backups.py`
- Modify: `tests/test_approvals_backups.py`

- [ ] **Step 1: Extend backup tests**

Append to `tests/test_approvals_backups.py`:

```python
from venus.backups import backup_status_record


def test_backup_status_record_tracks_verification():
    record = backup_status_record(
        target="./backups/venus",
        schedule="daily",
        last_backup_at="2026-06-14T03:00:00+08:00",
        last_verified_at="2026-06-14T03:05:00+08:00",
        status="verified",
    )

    assert record["target"] == "./backups/venus"
    assert record["status"] == "verified"
    assert record["recovery_note"] == "Use the latest verified Venus backup before restoring."
```

- [ ] **Step 2: Run backup test and verify failure**

Run:

```bash
pytest tests/test_approvals_backups.py::test_backup_status_record_tracks_verification -v
```

Expected: FAIL because `venus.backups` does not exist.

- [ ] **Step 3: Implement backup metadata**

Create `src/venus/backups.py`:

```python
from __future__ import annotations


def backup_status_record(
    target: str,
    schedule: str,
    last_backup_at: str,
    last_verified_at: str,
    status: str,
) -> dict[str, str]:
    return {
        "target": target,
        "schedule": schedule,
        "last_backup_at": last_backup_at,
        "last_verified_at": last_verified_at,
        "status": status,
        "recovery_note": "Use the latest verified Venus backup before restoring.",
    }
```

- [ ] **Step 4: Run approval and backup tests**

Run:

```bash
pytest tests/test_approvals_backups.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit backup metadata**

Run:

```bash
git add src/venus/backups.py tests/test_approvals_backups.py
git commit -m "feat: add backup metadata records"
```

---

### Task 8: Orchestrator And CLI

**Files:**
- Create: `src/venus/orchestrator.py`
- Create: `src/venus/cli.py`
- Create: `tests/test_cli_smoke.py`

- [ ] **Step 1: Write orchestrator and CLI smoke tests**

Create `tests/test_cli_smoke.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

from venus.orchestrator import VenusOrchestrator


def test_orchestrator_routes_hotspot_workflow():
    orchestrator = VenusOrchestrator()
    result = orchestrator.run(
        "hotspot",
        {
            "hotspots": [
                {
                    "topic": "早C晚A翻车",
                    "type": "controversy",
                    "freshness": 9,
                    "relevance": 10,
                    "controversy": 8,
                    "evidence": ["douyin-export-001"],
                }
            ],
            "persona_samples": ["姐妹们，先看屏障状态，证据和体验都要说清楚。"],
        },
    )

    assert result["workflow"] == "hotspot"
    assert result["result"]["top_topic"] == "早C晚A翻车"


def test_cli_hotspot_outputs_json(tmp_path):
    payload = [
        {
            "topic": "早C晚A翻车",
            "type": "controversy",
            "freshness": 9,
            "relevance": 10,
            "controversy": 8,
            "evidence": ["douyin-export-001"],
        }
    ]
    input_file = tmp_path / "hotspots.json"
    input_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "-m", "venus.cli", "hotspot", str(input_file)],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)
    assert output["workflow"] == "hotspot"
    assert output["result"]["top_topic"] == "早C晚A翻车"
```

- [ ] **Step 2: Run CLI smoke tests and verify failure**

Run:

```bash
pytest tests/test_cli_smoke.py -v
```

Expected: FAIL because `venus.orchestrator` and `venus.cli` do not exist.

- [ ] **Step 3: Implement orchestrator**

Create `src/venus/orchestrator.py`:

```python
from __future__ import annotations

from typing import Any

from venus.comments import analyze_comments
from venus.content import generate_hotspot_brief
from venus.persona import build_persona_profile
from venus.product_research import build_product_research_card


class VenusOrchestrator:
    def run(self, workflow: str, payload: dict[str, Any]) -> dict[str, Any]:
        persona_samples = payload.get(
            "persona_samples",
            ["姐妹们，先看屏障状态，证据和体验都要说清楚。"],
        )
        profile = build_persona_profile(list(persona_samples))

        if workflow == "hotspot":
            result = generate_hotspot_brief(list(payload["hotspots"]), profile)
        elif workflow == "product":
            products = list(payload["products"])
            result = build_product_research_card(products[0])
        elif workflow == "comments":
            result = analyze_comments(list(payload["comments"]), profile)
        else:
            raise ValueError(f"Unsupported Venus workflow: {workflow}")

        return {
            "workflow": workflow,
            "approval_mode": "manual",
            "external_actions": [],
            "result": result,
        }
```

- [ ] **Step 4: Implement CLI**

Create `src/venus/cli.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from venus.orchestrator import VenusOrchestrator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="venus")
    parser.add_argument("workflow", choices=["hotspot", "product", "comments"])
    parser.add_argument("input", help="Path to a JSON input file")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    records = json.loads(input_path.read_text(encoding="utf-8"))
    payload = _payload_for(args.workflow, records)
    result = VenusOrchestrator().run(args.workflow, payload)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _payload_for(workflow: str, records: Any) -> dict[str, Any]:
    if workflow == "hotspot":
        return {"hotspots": records}
    if workflow == "product":
        return {"products": records}
    if workflow == "comments":
        return {"comments": records}
    raise ValueError(f"Unsupported Venus workflow: {workflow}")


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run CLI smoke tests**

Run:

```bash
pytest tests/test_cli_smoke.py -v
```

Expected: PASS.

- [ ] **Step 6: Run all tests**

Run:

```bash
pytest -v
```

Expected: PASS for all tests.

- [ ] **Step 7: Commit orchestrator and CLI**

Run:

```bash
git add src/venus/orchestrator.py src/venus/cli.py tests/test_cli_smoke.py
git commit -m "feat: add Venus orchestrator and CLI"
```

---

### Task 9: End-To-End Demo Outputs

**Files:**
- Create: `tests/test_end_to_end_acceptance.py`
- Modify: `README.md`

- [ ] **Step 1: Write acceptance tests**

Create `tests/test_end_to_end_acceptance.py`:

```python
from venus.orchestrator import VenusOrchestrator


def test_first_slice_acceptance_workflows():
    orchestrator = VenusOrchestrator()

    hotspot = orchestrator.run(
        "hotspot",
        {
            "hotspots": [
                {
                    "topic": "早C晚A翻车",
                    "type": "controversy",
                    "freshness": 9,
                    "relevance": 10,
                    "controversy": 8,
                    "evidence": ["douyin-export-001"],
                }
            ],
            "persona_samples": ["姐妹们，先看屏障状态，证据和体验都要说清楚。"],
        },
    )
    product = orchestrator.run(
        "product",
        {
            "products": [
                {
                    "brand": "示例品牌",
                    "name": "屏障修护精华",
                    "filing_id": "国妆网备字20260001",
                    "ingredients": ["烟酰胺", "泛醇", "神经酰胺NP"],
                    "claims": ["修护", "100%修复屏障"],
                    "supplier_docs": ["泛醇供应商COA"],
                    "controversies": ["用户反馈刺痛"],
                    "evidence": [{"id": "nmpa-001", "type": "regulator", "title": "备案查询", "confidence": "high"}],
                }
            ]
        },
    )
    comments = orchestrator.run(
        "comments",
        {
            "comments": [
                {"id": "c1", "text": "敏感肌用了会不会烂脸？"},
                {"id": "c2", "text": "求平价替代！"},
            ]
        },
    )

    assert hotspot["external_actions"] == []
    assert product["result"]["forbidden_claims"] == ["100%修复屏障"]
    assert comments["result"]["summary"]["approval_gated"] == 1
```

- [ ] **Step 2: Run acceptance test and verify current behavior**

Run:

```bash
pytest tests/test_end_to_end_acceptance.py -v
```

Expected: PASS if prior tasks are complete.

- [ ] **Step 3: Update README with exact demo commands**

Replace the `## Smoke Commands` section in `README.md` with:

````markdown
## Smoke Commands

Run all tests:

```bash
pytest -v
```

Generate a hotspot brief:

```bash
venus hotspot data/samples/hotspots.json
```

Generate a product research card:

```bash
venus product data/samples/products.json
```

Analyze comments and draft approval-gated replies:

```bash
venus comments data/samples/comments.json
```

The local MVP never performs external actions. Public replies, publishing, lead routing, and ad spend remain approval-gated future integrations.
````

- [ ] **Step 4: Run full test suite**

Run:

```bash
pytest -v
```

Expected: PASS for all tests.

- [ ] **Step 5: Commit acceptance test and README**

Run:

```bash
git add tests/test_end_to_end_acceptance.py README.md
git commit -m "test: add Venus MVP acceptance smoke"
```

---

### Task 10: Final Verification And Handoff

**Files:**
- Modify: `task_plan.md`
- Modify: `progress.md`

- [ ] **Step 1: Update `task_plan.md` implementation status**

Modify the phase table rows:

```markdown
| 2. Implementation plan | Complete | Break the approved design into executable milestones, files, services, connectors, and tests. | Implementation plan saved and reviewed. |
| 3. Local project scaffold | In progress | Create the repo structure, environment templates, docs, and first runnable agent skeleton. | Local smoke command runs. |
```

- [ ] **Step 2: Update `progress.md` after implementation**

Append:

```markdown

## Implementation Progress

- Built the first local Venus MVP as a Python package.
- Added isolated Venus storage paths and Xiaolongxia collection guard.
- Added persona, content intelligence, product research, comment analysis, approval, backup, orchestrator, and CLI modules.
- Added deterministic sample data and smoke tests.
- Verified with `pytest -v`.
```

- [ ] **Step 3: Run final tests**

Run:

```bash
pytest -v
```

Expected: PASS for all tests.

- [ ] **Step 4: Run CLI smoke commands**

Run:

```bash
venus hotspot data/samples/hotspots.json
venus product data/samples/products.json
venus comments data/samples/comments.json
```

Expected:

- Each command prints valid JSON.
- `hotspot` output includes `"workflow": "hotspot"`.
- `product` output includes `"forbidden_claims"`.
- `comments` output includes `"approval_gated"`.

- [ ] **Step 5: Check git status**

Run:

```bash
git status --short
```

Expected: only intentional changes remain before final commit.

- [ ] **Step 6: Commit status updates**

Run:

```bash
git add task_plan.md progress.md
git commit -m "docs: update Venus MVP implementation progress"
```

---

## Self-Review Notes

Spec coverage:

- Content hotspot briefs and scripts: Task 4, Task 8, Task 9.
- Product research cards: Task 5, Task 8, Task 9.
- Persona learning: Task 3, Task 4, Task 8.
- Comment analysis and approval-gated replies: Task 6, Task 8, Task 9.
- Evidence and source discipline: Task 2 models, Task 4 evidence IDs, Task 5 evidence sections.
- Approval logs and levels: Task 6.
- Backup metadata: Task 7.
- Venus/Xiaolongxia isolation: Task 2 storage guard, Task 10 status.
- Platform connectors: intentionally excluded from this first implementation slice and listed as separate future plans.

Placeholder scan:

- This plan avoids unresolved planning markers.
- Each code-changing task includes concrete test code, implementation code, commands, expected results, and commit commands.

Type consistency:

- `Evidence`, `ApprovalRecord`, `PersonaProfile`, `VenusOrchestrator`, and workflow result keys are defined before use.
- Workflow names are consistently `hotspot`, `product`, and `comments`.
