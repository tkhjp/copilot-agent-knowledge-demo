# GitHub Repository における共有 Project Knowledge の管理・利用アーキテクチャ

**対象:** code graph、test code、test metadata、architecture information、domain rule など、Repository に紐づく共有プロジェクト知識  
**想定読者:** ソフトウェア設計・開発プロセスに習熟しているが、GitHub の周辺サービスには必ずしも詳しくないエンジニア  
**ステータス:** Architecture / Operation Proposal  
**更新日:** 2026-07-27

---

## 1. Executive Summary

本資料は、特定の GitHub Repository に紐づく共有 Project Knowledge を、どこに保存し、どのように versioning・review・同期し、Human と Copilot Agent がどう利用するかを定義します。

対象となる情報の例は次のとおりです。

- code graph: symbol、call、dependency、inheritance、test impact
- test code、test inventory、coverage summary、quality metadata
- module responsibility、architecture decision、domain rule、testing policy
- generator version、schema version、source digest、artifact digest

本設計の中心的な判断は、**Repository 内の versioned files を authoritative store とし、Wiki、Spaces、Agent Session を用途別の派生レイヤーとして扱う**ことです。

```text
Repository versioned files
        = authoritative store / system of record

Git branch / commit / Pull Request / CI
        = change control / validation / conflict detection

GitHub Wiki
        = human-facing derived view

Copilot Spaces
        = curated context for Copilot interaction

Copilot Agent
        = execution and change-proposal layer

Agent Session
        = execution provenance, not persistent knowledge
```

この構成では、整合性の基準は常に Repository 側にあります。Wiki や Spaces は Repository の状態を反映する派生ビューであり、同期には時間差が生じ得ます。Agent が作成した変更も通常の branch、Pull Request、CI、review を経由します。

### 1.1 推奨する基本構成

```text
Source code / tests
        ↓
Deterministic knowledge generator
        ↓
Repository Knowledge Pack
        ↓
Pull Request + CI + review
        ↓ merge
        ├── Tool / Copilot / Agent が参照
        ├── Wiki へ一方向 publish
        └── Issue を通じて feedback を受付
```

### 1.2 非目標

本設計は、次を直接実現するものではありません。

- GitHub Wiki を primary database として運用すること
- Agent Session を長期 Knowledge Store として検索・再利用すること
- Git の merge 機構だけで semantic conflict を自動解決すること
- 大規模 graph traversal を GitHub の標準機能だけで実現すること
- Repository と Wiki の content を双方向に自動同期すること

---

## 2. Architecture Principles

### P-01: Single Authoritative Store

Project Knowledge の正本は、原則として source code と同一 Repository 内の versioned files に置きます。

これにより、次の関係を同一の Git history 上で追跡できます。

```text
source state
↕
generated graph / knowledge view
↕
review / approval / validation evidence
```

### P-02: Separate Authoritative Data from Derived Views

Repository、Wiki、Spaces、Agent Session の責務を混在させません。

| Layer | 主な責務 | Authoritative か |
|---|---|---:|
| Repository Knowledge Pack | versioned knowledge、manifest、queryable artifact | Yes |
| GitHub Wiki | 人向け閲覧、説明、確認、feedback navigation | No |
| Copilot Spaces | task-specific に選別した Copilot context | No |
| Agent Session | prompt、tool call、変更理由、validation log | No |
| GitHub Pages | 検索・filter・graph visualization を含む presentation | No |

### P-03: Generated Artifacts Are Reproducible Outputs

Generated Markdown、raw graph、manifest は手編集対象にしません。競合時は target branch を取り込んだ上で generator を再実行します。

### P-04: Human Approval Remains the Control Boundary

Agent を導入しても、Source of Truth、review policy、merge gate は変更しません。Agent は変更案と検証結果を作成しますが、承認境界は Pull Request と CI に置きます。

### P-05: Scale by Externalizing Data, Not Governance

Graph が Repository に適さない規模になった場合、complete graph を external GraphDB または object storage に移します。ただし、source digest、snapshot ID、schema version、query client は Repository に残します。

---

## 3. 関連する GitHub 機能

今回の課題に直接関係する機能だけを比較します。

### 3.1 Repository Files + Git / Pull Request

#### 提供能力

- source code と knowledge を同一 branch / commit / Pull Request で管理
- diff、review comment、approval、merge history の保持
- manifest による source state と knowledge artifact の対応付け
- CODEOWNERS、Rulesets、branch protection による変更統制
- GitHub Actions による generation、freshness、integrity の検証
- Repository context を利用する Tool / Copilot / Agent からの参照

#### 制約・非適合ユースケース

- Git は semantic conflict を自動解決しない
- compressed graph、binary artifact、generated files の手動 merge には不向き
- 高頻度に更新される大量 artifact は Repository history を肥大化させる
- graph traversal や aggregate query の実行基盤ではない
- 人向け portal としての navigation / visualization は限定的

#### 本設計上の責務

```text
Repository Files + Git / Pull Request
        = authoritative store + change-control plane
```

---

### 3.2 GitHub Wiki

GitHub Wiki は Repository に紐づく人向け documentation surface です。Wiki の内容は本体 Repository とは別の Git Repository（`<repository>.wiki.git`）として管理されます。

#### 提供能力

- Markdown、image、link、Mermaid diagram の表示
- system overview、module responsibility、test impact の整理
- sidebar を利用した knowledge portal の構築
- onboarding、design review、knowledge confirmation の支援
- Wiki 自体の revision history の保持
- source file、Issue、Pull Request への navigation

#### 制約・非適合ユースケース

- 本体 Repository の Pull Request と atomic に更新できない
- raw code graph 全量や大量 generated artifacts の保存には不向き
- arbitrary graph traversal / query を提供しない
- Copilot Agent が必ず利用する primary context ではない
- Repository と Wiki の双方向同期は conflict と ownership を複雑化する

#### 本設計上の責務

```text
GitHub Wiki
        = human-facing derived view
        ≠ authoritative store
```

同期方向は Repository から Wiki への一方向とします。Wiki で検出した誤りは、Issue または Pull Request として Repository 側へ戻します。

---

### 3.3 Copilot Spaces

Copilot Spaces は、GitHub file、Issue、Pull Request、free text、Space instructions などを task-oriented に集約し、Copilot の回答 context として利用する機能です。

#### 提供能力

- 複数の情報源を domain / task 単位で curated context 化
- Space 単位の instructions 設定
- onboarding、support、特定業務向け Q&A の標準化
- GitHub 上の resource 更新を反映した context 利用
- IDE から GitHub MCP server を経由した参照

例:

```text
Space: Payment Test Knowledge
├── testing policy
├── payment module knowledge
├── related issues / pull requests
└── task instructions
```

#### 制約・非適合ユースケース

- generated artifact の authoritative store にはならない
- branch / Pull Request / review / conflict resolution を代替しない
- source commit と厳密に transactionally bound された snapshot ではない
- IDE 利用は GitHub MCP server と Agent mode が前提で、resource type に制約がある
- Space 内部 retrieval を任意の graph query API として利用できない

#### 本設計上の責務

```text
Repository Files = authoritative store
Copilot Spaces   = curated consumption layer
```

Spaces は Must ではありません。複数 document を task 別に選別し、Copilot の Q&A 品質と利用者体験を改善する場合に採用します。

---

### 3.4 Copilot Agent / Agent Session

Copilot Agent は Repository context を調査し、isolated environment で command を実行し、branch / Pull Request に変更を作成する execution layer です。Agent Session はその実行単位と履歴です。

#### 提供能力

- source、test、Repository knowledge の探索
- graph query tool を用いた target symbol 周辺の取得
- branch 上での code / test / knowledge change
- generator、test、lint、validation command の実行
- Pull Request の作成
- prompt、response、tool usage、changed files、validation result の記録

#### 制約・非適合ユースケース

- Custom Agent 定義を配置しただけでは Session は開始されない
- Session は長期共有 knowledge の authoritative store ではない
- Agent output にも CI と human review が必要
- Session URL を Agent 間の正式な handoff artifact にしない
- Wiki を直接更新する主体にはしない

#### 本設計上の責務

```text
Copilot Agent = execution / proposal layer
Agent Session = execution provenance
```

正式な handoff は、commit、branch、Pull Request、manifest、Repository knowledge files です。

---

### 3.5 GitHub Pages

GitHub Pages は Repository content から static site を build / publish する presentation mechanism です。

#### 提供能力

- custom layout、全文検索、filter を備えた portal
- interactive graph visualization
- Wiki より高度な navigation と UI
- Repository source からの automated deployment

#### 制約・非適合ユースケース

- authoritative store にはしない
- GraphDB や test DB の代替ではない
- content の変更・review は元 Repository で実施する
- site generator、frontend、deployment の maintenance cost が追加される

#### 本設計上の責務

Wiki で満たせない interactive visualization、検索、filter 要件が明確になった場合に追加する optional presentation layer です。

---

### 3.6 Supporting GitHub Mechanisms

以下は独立した Knowledge Store ではありませんが、運用上の control plane を構成します。

| Mechanism | 本設計での用途 |
|---|---|
| GitHub Actions | generation、freshness / integrity check、Wiki / Pages publish |
| CODEOWNERS / Rulesets | path ownership、required review、required checks、merge policy |
| Issues / Issue Forms | Wiki からの defect、stale、update request の受付 |
| Releases / Release Assets | immutable snapshot の配布 |
| Actions Artifacts | CI run 単位の一時 report、test result、diagnostic artifact |
| MCP | external GraphDB、test DB、internal API と Agent の接続 |

---

## 4. Requirements

### 4.1 Must Requirements

以下は、code graph や test knowledge をチームで継続的に共有するための必須要件です。

| ID | Requirement | Acceptance Criteria | Mechanism |
|---|---|---|---|
| M-01 | Authoritative store | 正本が一意で、派生ビューと区別できる | Repository versioned files |
| M-02 | Source-to-knowledge binding | 各 artifact が対象 source state を識別できる | manifest / source digest / commit history |
| M-03 | Controlled update | 変更が diff、review、approval を経由する | branch / Pull Request |
| M-04 | Reproducible generation | 同一 logical input から同一 logical output を生成できる | deterministic generator |
| M-05 | Freshness / integrity gate | STALE、BROKEN、missing artifact を merge 前に検出する | CI required check |
| M-06 | Conflict policy | artifact 種別ごとの解決方法が定義されている | Git + regeneration rule |
| M-07 | Human inspection | 非実装者でも概要・状態・source link を確認できる | GitHub Wiki |
| M-08 | Tool / Agent access | 全量ではなく必要な knowledge slice を取得できる | Repository context + query tool |
| M-09 | Access control | Repository permission と同等以上の境界で保護される | Repository permission / ruleset |
| M-10 | Traceability | actor、change、review、validation result を追跡できる | commit / PR / CI |
| M-11 | Size / retention policy | Repository に保持する artifact の上限と外部化条件がある | threshold + manifest / snapshot pointer |

### 4.2 Must Baseline

```text
Repository Knowledge Pack
+ Git / Pull Request
+ Deterministic Generator
+ GitHub Actions
+ GitHub Wiki
+ Issue Feedback
```

この baseline を導入しないまま Spaces や Agent を追加すると、context は増えても version consistency と governance が保証されません。

### 4.3 Nice-to-Have Requirements

| ID | Requirement | Adoption Trigger | Mechanism |
|---|---|---|---|
| N-01 | Curated Copilot context | 複数 document の探索コストが高い | Copilot Spaces |
| N-02 | Agent execution | test generation、knowledge refresh、validation を委譲したい | Custom Agent / Skill / Hook |
| N-03 | Execution provenance | Agent の command と判断経緯を確認したい | Agent Session |
| N-04 | Rich visualization | Wiki では interactive graph / search を満たせない | GitHub Pages |
| N-05 | Large graph query | traversal、cross-repository query、低 latency が必要 | External GraphDB + MCP |
| N-06 | Immutable distribution | 特定時点の graph / report を再現可能に配布したい | Release Assets |
| N-07 | Per-run diagnostics | CI run ごとの test result を一定期間保持したい | Actions Artifacts |
| N-08 | Stronger governance | owner approval と required checks を強制したい | CODEOWNERS / Rulesets |
| N-09 | Long-term quality analytics | coverage / mutation / quality trend を横断集計したい | External Test DB |

Nice-to-Have は Must baseline を置き換えません。追加レイヤーは必ず authoritative store と version binding を参照します。

---

## 5. Artifact Classification and Storage Policy

| Artifact Class | 推奨保存先 | Versioning / Retention Policy |
|---|---|---|
| Source code / test code | Repository | source と同一 branch / PR |
| Curated policy / domain rule | Repository Markdown + Wiki mirror | human review 必須 |
| Generated module / test-impact summary | Repository Markdown + Wiki mirror | generator 管理、手編集禁止 |
| Code graph: small / medium | Repository compressed artifact + manifest | source digest と一体管理 |
| Code graph: large / high-frequency | External GraphDB / object storage + Repository manifest | snapshot ID / URI / schema を記録 |
| Test execution result | Actions Artifact または external Test DB | per-run data。通常は Git history に常設しない |
| Coverage / quality trend | compact Repository summary または external Test DB | retention と aggregation 要件で判断 |
| Immutable graph / report bundle | Release Asset | tag / release 単位 |
| Agent execution history | Agent Session | provenance。authoritative knowledge ではない |
| Branch-local runtime knowledge | `.agent-runtime/` | temporary、commit しない |

### 5.1 Repository-contained Mode

次の条件を満たす場合は、raw graph を Repository に保持できます。

- artifact size が小規模または中規模
- update frequency が限定的
- clone / checkout performance に影響しない
- graph query が file-based tool で足りる

### 5.2 External Graph Mode

次の条件のいずれかを満たす場合、complete graph を外部化します。

- Repository size / history growth が無視できない
- graph update が高頻度
- cross-repository graph が必要
- traversal、path search、aggregate query が主要ユースケース
- Agent に必要な subgraph だけを低 latency で返したい

```text
Repository
├── manifest
├── source digest
├── compact knowledge views
├── graph snapshot ID / URI
└── query client / Agent Skill

External GraphDB / Object Storage
└── complete graph
```

---

## 6. Composition Patterns

### 6.1 Baseline: Shared Knowledge + Human Review

```text
Source code / tests
        ↓
Knowledge generator
        ↓
Repository Knowledge Pack
        ↓
Pull Request + CI + review
        ↓ merge
        ├── Tool / Copilot が参照
        └── Wiki へ one-way publish
                     ↓
                Issue feedback
```

構成要素:

- Repository versioned files
- Git / Pull Request
- deterministic generator
- GitHub Actions
- GitHub Wiki
- Issue Form

この構成を標準とします。

### 6.2 Add Copilot Q&A

Baseline に Copilot Spaces を追加します。

```text
Repository authoritative data
        ↓ selected resources
Copilot Space
        ↓
Copilot Chat / onboarding / task-specific Q&A
```

採用条件:

- 利用者が複数 file / Issue / Pull Request を毎回探索している
- domain または task ごとに context boundary を設けたい
- Copilot に共通 instructions を付与したい

Spaces は Repository snapshot や change-control mechanism の代替ではありません。

### 6.3 Add Agent-based Change Execution

Baseline に Agent layer を追加します。

```text
Human starts Agent task
        ↓
Agent Session / isolated workspace
        ↓
Freshness check
        ↓
Repository knowledge + graph slice
        ↓
Branch change
        ↓
Tests / generator / validation
        ↓
Pull Request
        ↓
Human review + merge
        ↓
Wiki refresh
```

追加要素:

- Custom Agent
- Agent Skill
- Hook
- Agent Session

Source of Truth、approval boundary、merge rule は変更しません。

### 6.4 Add Rich Visualization

Baseline に GitHub Pages を追加します。

```text
Repository compact graph / metadata
        ↓ static build
GitHub Pages
        = search / filter / interactive graph
```

Wiki は summary と navigation、Pages は detail visualization を担当します。

### 6.5 Add Large Graph Query for Agents

```text
Repository manifest / compact views
        ↓
Agent Skill / MCP client
        ↓
External GraphDB
        ↓
Relevant subgraph only
```

採用条件:

- graph が Repository-contained mode の上限を超える
- path / traversal query が必要
- cross-repository dependency を扱う
- query result を context budget に合わせて縮約する必要がある

---

## 7. Logical Architecture

```text
                              Human
                                │
                         browse / confirm
                                ▼
                         GitHub Wiki / Pages
                                │
                         Issue / PR feedback
                                │
                                ▼
Source / Tests ──→ Generator ──→ Repository Knowledge Pack
                                        │
               ┌────────────────────────┼─────────────────────────┐
               │                        │                         │
        Pull Request / CI         Copilot Context          External Pointer
        review / approval        Repository / Space       Graph snapshot URI
               │                        │                         │
               └───────────────┬────────┴───────────┬─────────────┘
                               │                    │
                         Human Tooling        Copilot Agent
                                                  │
                                          Agent Session
                                                  │
                                        branch + validation
                                                  │
                                              Pull Request
```

### 7.1 Plane Separation

| Plane | Components | Responsibility |
|---|---|---|
| Data Plane | Repository artifacts、external GraphDB / Test DB | knowledge content と query data |
| Control Plane | Git、PR、Rulesets、CI、manifest | version、approval、integrity、conflict policy |
| Presentation Plane | Wiki、Pages、Spaces | human / Copilot consumption |
| Execution Plane | Agent、Skills、Hooks、Sessions | exploration、change proposal、validation |

この分離により、presentation や Agent implementation を変更しても authoritative data と governance を維持できます。

---

## 8. Repository Layout and Metadata Contract

```text
repository/
├── src/
├── tests/
├── artifacts/
│   └── codegraph/
│       ├── nodes.jsonl.gz
│       └── edges.jsonl.gz
├── docs/
│   └── agent-knowledge/
│       ├── generated/
│       │   ├── manifest.json
│       │   ├── system-overview.md
│       │   ├── modules/
│       │   └── test-impact/
│       └── curated/
│           ├── domain-rules.md
│           └── testing-policy.md
├── .agent-runtime/
│   └── branch-local knowledge
└── .github/
    ├── agents/
    ├── skills/
    ├── hooks/
    ├── workflows/
    └── ISSUE_TEMPLATE/
```

### 8.1 Ownership by Artifact Type

| Artifact | Writer | Review / Merge Rule |
|---|---|---|
| source / tests | Human / Agent | normal PR review |
| raw graph | generator only | regenerate; do not hand-edit |
| generated knowledge | generator only | regenerate; inspect semantic diff |
| manifest | generator only | schema validation required |
| curated knowledge | Human; Agent may propose | domain / test owner review |
| runtime knowledge | Hook / Agent | temporary; never commit |

### 8.2 Manifest Contract

Knowledge Pack は machine-readable manifest を持ちます。

```json
{
  "schema_version": 1,
  "generator_version": "1.1.0",
  "source_digest": "sha256:...",
  "source_files": {
    "src/payment_service/service.py": "sha256:...",
    "tests/test_payment_service.py": "sha256:..."
  },
  "graph": {
    "node_count": 30,
    "edge_count": 101,
    "artifacts": {
      "nodes.jsonl.gz": "sha256:...",
      "edges.jsonl.gz": "sha256:..."
    }
  },
  "knowledge_artifacts": {
    "modules/payment-service.md": "sha256:...",
    "test-impact/payment-service.md": "sha256:..."
  },
  "external_graph": {
    "snapshot_id": null,
    "uri": null
  }
}
```

Manifest の必須責務:

- source state と knowledge state の対応付け
- generator / schema compatibility の判定
- artifact integrity の検証
- external snapshot の参照
- CI と Agent に共通の freshness contract を提供

### 8.3 Knowledge State

| State | Condition | Consumer Behavior |
|---|---|---|
| CURRENT | source digest と manifest が一致 | committed knowledge を利用可能 |
| STALE | source digest が不一致 | merge 前に再生成。Agent は runtime knowledge を生成可能 |
| BROKEN | artifact missing、digest mismatch、schema error | 利用停止し generator から再生成 |

---

## 9. Update and Validation Workflow

### 9.1 Source / Test Change

```text
Human / Agent
    ↓
feature branch
    ↓
source / tests change
    ↓
knowledge generation
    ↓
source + generated artifacts commit
    ↓
unit test / knowledge validation
    ↓
Pull Request
    ↓
review / required checks / merge
    ↓
Wiki publish
```

原則として、source change と影響を受ける knowledge change は同一 Pull Request に含めます。

### 9.2 Curated Knowledge Change

```text
Human / Agent proposal
    ↓
curated Markdown change
    ↓
Pull Request
    ↓
domain / test owner review
    ↓
merge
    ↓
Wiki publish
```

Generator は curated knowledge を変更しません。

### 9.3 Generator / Schema Change

同一 Pull Request に次を含めます。

- generator implementation
- generator version / schema version
- regenerated graph
- regenerated knowledge views
- migration note
- regression tests

CI は byte identity ではなく、必要に応じて canonical logical content の再現性を検証します。

### 9.4 Required CI Gates

- source digest と manifest の一致
- artifact existence と digest validation
- schema validation
- deterministic regeneration comparison
- unit / integration test
- Wiki export smoke test
- secret / sensitive data exclusion check（本番導入時）

---

## 10. Conflict and Concurrency Model

Git は conflict detection と history management を提供します。解決方式は artifact class ごとに定義します。

| Artifact | Resolution Strategy |
|---|---|
| Source code | merge / rebase 後に semantic review |
| Curated Markdown | three-way merge。owner が内容を判断 |
| Generated Markdown | hand merge しない。latest target branch で再生成 |
| Raw graph | hand merge しない。latest target branch で再生成 |
| Manifest | hand merge しない。generator で再生成 |
| Wiki managed page | Repository を正とし、次回 publish で置換 |
| External graph snapshot | new source digest に対して新 snapshot を publish |

### 10.1 Parallel Agent / Developer Changes

```text
PR A merges
    ↓
PR B rebases onto latest default branch
    ↓
regenerate knowledge
    ↓
run validation
    ↓
review / merge
```

Generated artifact の conflict を editor で修正してはいけません。再生成により、source state と artifact state の一貫性を回復します。

### 10.2 Concurrency Invariants

- default branch の knowledge は、その branch の source digest と一致する
- Wiki publisher は single-writer として動作する
- 古い publish job が新しい Wiki state を後から上書きしない
- external graph snapshot は immutable ID で参照する

---

## 11. Wiki Publication Model

### 11.1 Consistency Model

Repository が authoritative、Wiki は eventually consistent な derived view です。

```text
Repository merge
    ↓ asynchronous publish
Wiki update
```

Wiki publish failure は authoritative knowledge を破壊しません。Repository merge は保持し、publish job を再実行します。

### 11.2 Managed and Manual Pages

| Page Type | Ownership | Rule |
|---|---|---|
| Managed page | Repository + Actions | Wiki 上で直接編集しない |
| Manual page | Human on Wiki | Workflow は削除しない。確定 knowledge は Repository へ昇格 |

Managed page の例:

- System Overview
- Module Knowledge
- Test Impact
- Domain Rules
- Testing Policy
- Architecture / Operation Guide

Manual page の例:

- meeting note
- temporary discussion memo
- onboarding memo

### 11.3 Publish Workflow

```text
1. default branch checkout
2. Wiki Markdown export
3. <repository>.wiki.git clone
4. previous managed-page manifest read
5. managed pages only replace
6. new managed-page manifest write
7. Wiki commit / push
```

```yaml
concurrency:
  group: mirror-agent-knowledge-wiki
  cancel-in-progress: true
```

### 11.4 Page Metadata

Managed page には次の metadata を表示することを推奨します。

```markdown
> **Management:** generated and published from the source Repository
> **Source repository:** `owner/repository`
> **Published from commit:** `abcdef1`
> **Source digest:** `sha256:...`
> **Generator version:** `1.1.0`
> **Knowledge state:** `CURRENT`
> **Source file:** `docs/agent-knowledge/generated/...`
> **Change request:** use Issue or Pull Request; do not edit this page directly
```

### 11.5 Feedback Path

```text
Wiki page
    ↓
Knowledge Feedback Issue / Pull Request
    ↓
Repository change
    ↓
review / merge
    ↓
Wiki republish
```

Content synchronization is one-way; feedback flow is bidirectional through GitHub workflow objects.

---

## 12. Agent Execution Model

### 12.1 Without Agent

```text
Human
  ↓ source / knowledge investigation
  ↓ graph query
  ↓ code / test / knowledge change
  ↓ generation / validation
  ↓ Pull Request
  ↓ review / merge
  ↓ Wiki publish
```

### 12.2 With Agent

```text
Human starts Agent task
        ↓
Agent Session starts
        ↓
sessionStart freshness check
        ↓
CURRENT or runtime knowledge selected
        ↓
relevant graph slice queried
        ↓
source / generated / curated knowledge inspected
        ↓
branch change
        ↓
knowledge regeneration when required
        ↓
test / validation
        ↓
Pull Request
        ↓
human review / merge
        ↓
Wiki publish
```

### 12.3 Agent Information Precedence

```text
1. current branch source code
2. current branch runtime knowledge
3. committed generated knowledge
4. curated knowledge
5. Space / Wiki / Issue / PR / Session history
```

Current source code remains authoritative when any derived context conflicts with implementation.

### 12.4 Agent Pull Request Provenance

```markdown
## Knowledge Provenance

- Base branch: `develop`
- Source digest: `sha256:...`
- Knowledge state: `CURRENT` / `RUNTIME`
- Generated artifacts used:
  - `docs/agent-knowledge/generated/modules/...`
- Curated artifacts used:
  - `docs/agent-knowledge/curated/...`
- Graph query:
  - symbol: `PaymentService.authorize`
  - depth: `1`
- Validation:
  - `make test`
  - `make check`
```

### 12.5 Agent Failure Boundaries

- Agent が knowledge を誤解しても、PR review と CI で default branch への反映を防ぐ
- Agent Session が失われても、commit / PR / manifest に正式な handoff を残す
- external GraphDB が unavailable の場合、Agent は compact Repository view に degrade するか task を停止する
- runtime knowledge が BROKEN の場合、Agent は generated claims を利用せず current source を直接調査する

---

## 13. Security and Operational Considerations

### 13.1 Access Control

- Knowledge は原則として source Repository と同じ visibility / permission boundary に置く
- Wiki、Pages、Spaces、Artifacts の visibility が source より広くならないことを確認する
- external GraphDB / MCP credential は Secrets / Environments で管理する
- Agent tool permissions は least privilege とする

### 13.2 Sensitive Data

Knowledge generator の input から次を除外します。

- secrets / credentials
- production payload
- customer data
- unrestricted logs
- personally identifiable information
- license 上再配布できない content

### 13.3 Observability

最低限記録する情報:

- generator version / schema version
- source digest / artifact digest
- CI run and validation result
- Wiki publish source commit
- external graph snapshot ID
- Agent Session / PR linkage

### 13.4 Backup and Recovery

- Repository と Wiki はそれぞれ Git Repository として backup 可能
- external graph は snapshot / backup policy を別途持つ
- Wiki は再生成可能な派生データとし、disaster recovery の優先順位を Repository より下げる

---

## 14. Recommended Adoption Path

### Phase 1: Baseline Governance

- Repository Knowledge Pack
- manifest / source digest
- deterministic generator
- PR / CI validation
- Wiki one-way publish
- Issue feedback

### Phase 2: Copilot Consumption

- task-specific Copilot Spaces
- repository instructions
- query tool の標準化

### Phase 3: Agent Execution

- Custom Agent / Skill / Hook
- Agent Session provenance
- Agent PR template

### Phase 4: Scale-out

- GitHub Pages for rich visualization
- external GraphDB / Test DB
- MCP integration
- organization-level rules / common agents

導入順序は、presentation や Agent convenience より先に、authoritative store と consistency contract を確立することを原則とします。

---

## 15. Decision for This Demo

| Capability | Current Decision |
|---|---|
| Repository Knowledge Pack | adopted as authoritative store |
| Git / Pull Request / CI | adopted for change control and validation |
| Wiki | adopted as human-facing derived view |
| Issue Form | adopted as Wiki feedback entry point |
| Copilot Agent / Session | agent definitions available; validate with actual sessions |
| Copilot Spaces | optional; adopt when curated Q&A is required |
| GitHub Pages | optional; adopt when interactive visualization is required |
| External GraphDB / MCP | optional; adopt when size or query complexity exceeds Repository mode |

---

## 16. Operational Rules

1. Authoritative knowledge is stored in the Repository.
2. Generated artifacts are never edited manually.
3. Curated knowledge changes require Pull Request review.
4. Source changes and affected knowledge changes are included in the same Pull Request whenever feasible.
5. STALE or BROKEN knowledge blocks merge.
6. Wiki managed pages are not edited directly.
7. Wiki feedback returns through Issue or Pull Request.
8. Agents use isolated branches and normal merge controls.
9. Agent Sessions are provenance, not persistent knowledge.
10. Large graphs retain manifest and compact views in the Repository while externalizing complete data.

---

## 17. Official References

- [About wikis](https://docs.github.com/en/communities/documenting-your-project-with-wikis/about-wikis)
- [Adding or editing wiki pages](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages)
- [Using GitHub Copilot Spaces](https://docs.github.com/en/copilot/how-tos/provide-context/use-copilot-spaces/use-copilot-spaces)
- [Using Copilot cloud agent on GitHub](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-on-github)
- [Managing agent sessions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/use-copilot-agents/manage-and-track-agents)
- [GitHub Pages documentation](https://docs.github.com/en/pages)
- [Workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
