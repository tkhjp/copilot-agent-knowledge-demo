# GitHub Repository における共有 Project Knowledge の管理・利用設計

**対象:** code graph、test code、test metadata、architecture information、domain rule など、Repository 内で共有するプロジェクト知識  
**想定利用者:** 開発者、テスト担当者、GitHub Copilot 利用者、CI/CD 管理者、プロジェクト管理者  
**ステータス:** 実装・運用方針案  
**更新日:** 2026-07-27

---

## 1. 本資料の目的

本資料では、ある GitHub Repository において共有前提となる Project Knowledge を、次の観点で整理します。

1. GitHub 上の関連機能は何ができ、何ができないか
2. code graph や test 関連情報を共有するために必要な機能は何か
3. 必須機能（Must）と追加機能（Nice to Have）をどう分けるか
4. それらの機能をどのように組み合わせるか
5. 更新、conflict、Wiki 同期、Agent 利用時の workflow をどう設計するか

対象となる knowledge の例:

- code graph
- symbol / call / dependency / inheritance relationship
- module responsibility
- test code
- test inventory / test impact
- test policy
- domain rule
- architecture decision
- generator / schema metadata
- test execution result / coverage summary

本資料の基本結論は次です。

```text
Repository 内の versioned knowledge files
        = Source of Truth

Git branch / commit / Pull Request / review / CI
        = 更新、差分確認、競合検出、承認

GitHub Wiki
        = 人向けの閲覧、可視化、確認、feedback 入口

Copilot Spaces
        = Copilot 問答用に選別した context

Copilot Agent / Session
        = knowledge の利用・変更提案・検証と、その実行履歴
```

---

## 2. 関連する GitHub 機能

今回の目的に直接関係する機能だけを比較します。

### 2.1 Repository files + Git / Pull Request

#### できること

- source code と knowledge を同じ branch / commit で管理する
- Pull Request で diff、review、approval、merge を行う
- knowledge がどの source version に対応するかを記録する
- CODEOWNERS、Rulesets、Branch protection で承認ルールを強制する
- GitHub Actions で generation、freshness、integrity を検証する
- Repository index を通じて Copilot が text knowledge を検索する

#### できないこと・注意点

- Git が意味上の conflict を自動解決するわけではない
- generated file や compressed graph を人が手作業で merge する運用には向かない
- 大規模 raw graph を長期間 commit すると clone size と history size が増える
- 人向けの navigation や可視化は Wiki / Pages より弱い

#### 本設計での位置付け

```text
Repository files + Git / Pull Request
        = Knowledge の Source of Truth
```

---

### 2.2 GitHub Wiki

#### できること

- Markdown、画像、link、Mermaid diagram を人向けに表示する
- system overview、module responsibility、test impact を見やすく整理する
- sidebar を使って knowledge portal を構成する
- onboarding、確認、説明、feedback の入口にする
- Wiki 自体の Git history を保持する

#### できないこと・注意点

- 本体 Repository の Pull Request と同じ transaction で更新できない
- raw code graph 全量や大量 generated files の保存先には向かない
- arbitrary graph traversal / query はできない
- Copilot Agent が必ず参照する primary context ではない
- Repository と Wiki の自動双方向同期は conflict が複雑になる

#### 本設計での位置付け

```text
GitHub Wiki
        = human-facing presentation / confirmation layer
        ≠ Source of Truth
```

Repository から Wiki へ一方向同期し、Wiki で見つかった問題は Issue または Pull Request に戻します。

---

### 2.3 Copilot Spaces

#### できること

- Repository file、Issue、Pull Request、free text などをテーマ単位でまとめる
- Space ごとの instructions を設定する
- 複数 document を横断した Copilot Chat の context として利用する
- onboarding や特定業務向けの curated context を作る

例:

```text
Space: Payment Test Knowledge
├── testing policy
├── payment module knowledge
├── related Issue / Pull Request
└── task instructions
```

#### できないこと・注意点

- generated artifact の Source of Truth には向かない
- Git branch / Pull Request の代わりにはならない
- conflict resolution や厳密な version binding の仕組みではない
- IDE からの利用は MCP を経由し、resource type に制約がある
- Space の内部検索を任意の graph query API として利用することはできない

#### 本設計での位置付け

```text
Repository files = Source of Truth
Copilot Spaces   = Copilot consumption / curation layer
```

Space は必須ではありません。複数 document を選別して Copilot 問答に利用したい場合に追加します。

---

### 2.4 Copilot Agent / Agent Session

#### できること

- Repository の source / knowledge を調査する
- target symbol の graph slice を query する
- test または code change を branch 上で作成する
- generator、test、validation command を実行する
- Pull Request を作成する
- Session に prompt、command、tool usage、changed files、validation result を残す

#### できないこと・注意点

- Agent 定義を置いただけでは Session は作成されない
- Session は長期共有 knowledge の保存先ではない
- Agent が生成した内容も human review と CI を必要とする
- Agent Session を次の Agent の正式な handoff artifact にしない
- Wiki を直接変更する主体にはしない

#### 本設計での位置付け

```text
Copilot Agent = Knowledge を利用して作業する execution layer
Agent Session = 実行履歴 / provenance
```

正式な handoff は commit、branch、Pull Request、Repository knowledge です。

---

### 2.5 GitHub Pages

#### できること

- custom layout、全文検索、filter を持つ static portal を構築する
- interactive graph visualization を表示する
- Wiki より高度な navigation と UI を提供する
- Repository content から自動 build / deploy する

#### できないこと・注意点

- Knowledge の Source of Truth にはしない
- graph database の代わりにはならない
- 編集・review は元の Repository で行う必要がある
- UI の build / maintenance cost が追加される

#### 本設計での位置付け

Wiki で不足する可視化・検索要件が発生した場合に追加する Nice to Have です。

---

### 2.6 周辺機能

次の機能は独立した knowledge 保存先ではありませんが、運用を成立させるために利用します。

| 機能 | 用途 |
|---|---|
| GitHub Actions | generation、freshness、integrity、Wiki / Pages publish |
| CODEOWNERS / Rulesets | owner review、required checks、merge rule |
| Issues / Issue Forms | Wiki からの誤り・stale・更新要求の受付 |
| MCP | external GraphDB / test DB / internal API を Agent に接続 |
| Releases / Actions Artifacts | snapshot や一時的 test result の配布・保存 |

---

## 3. 共有 Project Knowledge に必要な機能

### 3.1 Must

code graph や test 関連 knowledge をチームで共有するために、最低限必要な機能です。

| Must requirement | 内容 | 採用する仕組み |
|---|---|---|
| 正本の明確化 | どの情報が authoritative かを一意にする | Repository versioned files |
| Version 対応 | Knowledge がどの source state に対応するか記録する | manifest / source digest / commit history |
| 更新・差分管理 | 変更内容を確認し、review できる | branch / commit / Pull Request |
| Conflict 管理 | 並行変更を検出し、artifact 種別に応じて解決する | Git + regeneration rule |
| Freshness / integrity | stale、missing、broken artifact を検出する | deterministic generator + CI |
| 人向け確認 | チームメンバーが内容を閲覧・確認できる | GitHub Wiki |
| Agent / Tool 参照 | Copilot や script が必要な knowledge を取得できる | Repository context + query tool |
| Access control | Repository と同じ権限境界で保護する | Repository permission / branch rule |
| Traceability | 誰が、何を、なぜ変更したか追跡する | commit / Pull Request / CI result |
| Size policy | Repository に置くものと外部保存するものを分ける | threshold + manifest / snapshot pointer |

Must の最小構成:

```text
Repository Knowledge Pack
+ Git / Pull Request
+ GitHub Actions
+ GitHub Wiki
+ Issue feedback
```

---

### 3.2 Nice to Have

要件に応じて追加する機能です。

| Nice-to-have requirement | 目的 | 追加する仕組み |
|---|---|---|
| Copilot 用 curated context | 複数 document をまとめて質問する | Copilot Spaces |
| Agent による作業自動化 | test generation、knowledge update、validation | Custom Agent / Skill / Hook |
| 実行経緯の確認 | Agent の command、tool、変更理由を見る | Agent Session |
| 高度な可視化 | interactive graph、検索、filter | GitHub Pages |
| 大規模 graph query | traversal、cross-repository query | external GraphDB + MCP |
| Immutable snapshot | 特定時点の graph / report を配布する | Release assets |
| 一時的 test result | CI run ごとの report を保持する | Actions Artifacts |
| 厳格な承認 | path owner と required approval を強制する | CODEOWNERS / Rulesets |

Nice to Have は、Must の Source of Truth と変更管理を置き換えません。

---

## 4. 共有対象ごとの保存方針

| 共有対象 | 推奨保存先 | 理由 |
|---|---|---|
| Test code | Repository | source と同じ branch / PR で管理する必要がある |
| Test policy / domain rule | Repository curated files + Wiki mirror | review 可能な正本と人向け表示が必要 |
| Code graph（小・中規模） | Repository artifact + manifest | source version と一体管理できる |
| Code graph（大規模） | External GraphDB / object storage + Repository manifest | Repository size と query 性能を分離する |
| Module / test-impact summary | Repository generated Markdown + Wiki | Agent retrieval と人向け確認の両方に使う |
| Test execution result | Actions Artifacts、必要なら外部 test DB | run ごとに大量発生し、source history に常設しない |
| Coverage summary / quality trend | Repository summary または外部 test DB | 長期比較要件に応じて選択する |
| Agent execution history | Agent Session | provenance 用。knowledge の正本にはしない |

---

## 5. 機能の組み合わせ方

### 5.1 標準構成: Knowledge を共有し、人が確認する

Must を満たす基本構成です。

```text
Source code / tests
        ↓
Knowledge generator
        ↓
Repository Knowledge Pack
        ↓
Pull Request + CI + review
        ↓ merge
        ├── Copilot / script が参照
        └── Wiki へ一方向同期
                     ↓
               Issue feedback
```

構成要素:

- Repository versioned files
- Git / Pull Request
- GitHub Actions
- GitHub Wiki
- Issue Form

これを本 Project の標準構成とします。

---

### 5.2 Copilot 問答を追加する

標準構成に Spaces を追加します。

```text
Repository Source of Truth
        ↓ selected resources
Copilot Space
        ↓
Copilot Chat / onboarding / task-specific Q&A
```

適用条件:

- 複数 file、Issue、Pull Request をテーマ別にまとめたい
- 利用者ごとに探す負荷を減らしたい
- Copilot に共通 instructions を与えたい

Space は Repository の代替ではありません。

---

### 5.3 Agent に test generation / knowledge update を行わせる

標準構成に Agent layer を追加します。

```text
Human starts Agent task
        ↓
Agent Session starts
        ↓
sessionStart freshness check
        ↓
Repository knowledge / graph slice を取得
        ↓
branch 上で test / knowledge を変更
        ↓
make test / make check
        ↓
Pull Request
        ↓
human review / merge
        ↓
Wiki refresh
```

追加する構成要素:

- Custom Agent
- Agent Skill
- Hook
- Agent Session

Source of Truth、review、merge rule は Agent 導入後も変更しません。

---

### 5.4 Graph を高度に可視化する

標準構成に Pages を追加します。

```text
Repository graph / compact view
        ↓ static build
GitHub Pages
        = search / filter / interactive graph
```

Wiki には overview と主要 diagram を置き、Pages は詳細 visualization を担当します。

---

### 5.5 大規模 graph を Agent が query する

```text
Repository
├── manifest
├── source digest
├── compact knowledge view
├── graph snapshot ID / URI
└── query client / Agent Skill

External GraphDB / object storage
└── complete graph

Copilot Agent
└── MCP 経由で必要な subgraph を取得
```

適用条件:

- graph が Repository に収まりにくい
- update frequency が高い
- 複数 Repository を横断する
- path / traversal query が必要
- Agent が必要な subgraph だけ取得する必要がある

---

## 6. 推奨 Architecture

```text
                          Human
                            │
                    browse / confirm
                            ▼
                      GitHub Wiki
                            │
                      Issue feedback
                            │
                            ▼
Source code ──→ Knowledge generator ──→ Repository Knowledge Pack
                                           │
                                           ├── Pull Request / review
                                           ├── CI freshness / integrity
                                           ├── Copilot repository context
                                           ├── optional Copilot Space
                                           └── Wiki / optional Pages publish

User starts task
      ↓
Copilot Agent Session
      ↓
read source + Repository Knowledge
      ↓
query graph slice
      ↓
branch change + validation
      ↓
Pull Request
      ↓
human review / merge
      ↓
Wiki / Pages refresh
```

責務分担:

| 責務 | Mechanism |
|---|---|
| Knowledge の正本 | Repository versioned files |
| 更新と競合検出 | Git branch / commit / Pull Request |
| 承認 | review / CODEOWNERS / Rulesets |
| 生成と検証 | GitHub Actions / local command |
| 人向け表示 | Wiki、必要なら Pages |
| Copilot 問答 | Repository context、必要なら Spaces |
| Agent 実行 | Custom Agent / Skill / Hook |
| Agent 履歴 | Agent Session |
| 外部 graph query | MCP + external GraphDB |

---

## 7. Repository 内の保存構成

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

分類:

| 種別 | 更新者 | 管理方法 |
|---|---|---|
| source / tests | Human / Agent | normal Pull Request |
| raw graph | generator | regeneration only |
| generated knowledge | generator | regeneration only |
| manifest | generator | regeneration only |
| curated knowledge | Human、Agent proposal | content review required |
| runtime knowledge | Hook / Agent | temporary、not committed |

---

## 8. Version と鮮度

Knowledge Pack は machine-readable manifest を持ちます。

```json
{
  "schema_version": 1,
  "generator_version": "1.1.0",
  "source_digest": "sha256:...",
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
  }
}
```

Status:

| Status | 条件 | 動作 |
|---|---|---|
| CURRENT | source digest が一致 | committed knowledge を利用 |
| STALE | source digest が不一致 | merge 前に再生成。Agent task では runtime knowledge を生成可能 |
| BROKEN | artifact 不足、hash / schema error | 利用停止し再生成 |

---

## 9. 更新 Workflow

### 9.1 Source code を変更する

```text
Human / Agent
    ↓
feature branch
    ↓
source / tests を変更
    ↓
knowledge generator を実行
    ↓
source + generated knowledge を commit
    ↓
make test / make check
    ↓
Pull Request
    ↓
review / merge
    ↓
Wiki publish
```

原則として source change と影響を受ける knowledge を同じ Pull Request に含めます。

### 9.2 Curated knowledge を変更する

```text
Human / Agent proposal
    ↓
curated Markdown を変更
    ↓
Pull Request
    ↓
owner review
    ↓
merge
    ↓
Wiki publish
```

Generator は curated knowledge を上書きしません。

### 9.3 Generator を変更する

同じ Pull Request に次を含めます。

- generator code
- generator / schema version
- regenerated graph
- regenerated knowledge views
- regression tests

CI は同じ input から同じ logical output が得られることを確認します。

---

## 10. Conflict 解決

Git は conflict の検出と履歴管理を行います。解決方法は artifact 種別で分けます。

| 対象 | 解決方法 |
|---|---|
| Source code | merge / rebase 後に人が確認 |
| Curated Markdown | three-way merge。内容 owner が判断 |
| Generated Markdown | 手動 merge しない。最新 branch で再生成 |
| Raw graph | 手動 merge しない。最新 branch で再生成 |
| Manifest | 手動 merge しない。最新 branch で再生成 |
| Wiki managed page | Repository を正とし、次回 publish で置換 |

複数 Agent が並行作業する場合:

```text
Agent A branch ──→ PR A ──→ merge
Agent B branch ──→ rebase latest develop
                 ──→ regenerate knowledge
                 ──→ make check
                 ──→ merge
```

Compressed graph や binary artifact を conflict editor で直接修正しません。

---

## 11. Wiki 更新・同期

### 11.1 同期方向

```text
Repository → Wiki
```

Content の自動双方向同期は行いません。

Feedback は次の経路で戻します。

```text
Wiki
  ↓
Knowledge Feedback Issue / Pull Request
  ↓
Repository change
  ↓ merge
Wiki refresh
```

### 11.2 Managed page と Manual page

| Page | 管理方法 |
|---|---|
| Managed page | Repository から Actions で生成・上書き |
| Manual page | Wiki 上で人が管理。Workflow は削除しない |

Manual page は meeting note や一時的な説明に使えますが、Agent の正式な knowledge source にはしません。

### 11.3 Publish workflow

```text
1. develop を checkout
2. Wiki 用 Markdown を export
3. <repository>.wiki.git を clone
4. 前回の managed page だけを削除
5. 新しい managed page を copy
6. .managed-pages を更新
7. Wiki commit / push
```

同時実行制御:

```yaml
concurrency:
  group: mirror-agent-knowledge-wiki
  cancel-in-progress: true
```

---

## 12. Agent 利用時の Workflow

### 12.1 Agent を使用しない場合

```text
Human
  ↓ source / knowledge を調査
  ↓ graph を確認
  ↓ code / test / knowledge を変更
  ↓ generator / validation
  ↓ Pull Request
  ↓ review / merge
  ↓ Wiki publish
```

### 12.2 Agent を使用する場合

```text
Human starts Agent task
        ↓
Agent Session starts
        ↓
sessionStart freshness check
        ↓
CURRENT または runtime knowledge を選択
        ↓
target symbol の graph slice を query
        ↓
source / generated / curated knowledge を確認
        ↓
branch 上で変更
        ↓
必要なら knowledge を再生成
        ↓
make test / make check
        ↓
Pull Request
        ↓
human review / merge
        ↓
Wiki publish
```

Agent の情報優先順位:

```text
1. 現在 branch の source code
2. 現在 branch 用 runtime knowledge
3. committed generated knowledge
4. curated knowledge
5. Space / Wiki / Issue / PR / Session history
```

### 12.3 Agent Pull Request の provenance

```markdown
## Knowledge provenance

- Base branch: `develop`
- Source digest: `sha256:...`
- Knowledge status: `CURRENT` / `RUNTIME`
- Generated files used:
  - `docs/agent-knowledge/generated/modules/...`
- Curated files used:
  - `docs/agent-knowledge/curated/...`
- Graph query:
  - symbol: `PaymentService.authorize`
  - depth: `1`
- Validation:
  - `make test`
  - `make check`
```

---

## 13. 本 Demo での採用判断

| 機能 | 現在の扱い |
|---|---|
| Repository Knowledge Pack | Source of Truth として採用 |
| Git / Pull Request / CI | 更新・検証に採用 |
| Wiki | human-facing mirror として採用 |
| Issue Form | Wiki feedback 入口として採用 |
| Copilot Agent / Session | Agent 定義済み。実 Session で利用確認 |
| Copilot Spaces | 未採用。Copilot 問答用 curated context が必要な場合に追加 |
| GitHub Pages | 未採用。interactive graph / search が必要な場合に追加 |
| External GraphDB / MCP | 未採用。graph size と query 要件で判断 |

---

## 14. 運用ルール

1. Source of Truth は Repository に置く
2. Generated knowledge を直接編集しない
3. Curated knowledge は Pull Request で review する
4. Source change と knowledge change は原則同じ Pull Request に含める
5. CI が STALE / BROKEN を検出した場合は merge しない
6. Wiki managed page を直接編集しない
7. Wiki feedback は Issue / Pull Request に戻す
8. Agent は独立 branch を使用する
9. Agent Session を長期 knowledge として参照しない
10. Large graph は manifest と compact view を Repository に残す

---

## 15. 公式仕様参照

- [About wikis](https://docs.github.com/en/communities/documenting-your-project-with-wikis/about-wikis)
- [Adding or editing wiki pages](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages)
- [About GitHub Copilot Spaces](https://docs.github.com/en/copilot/concepts/context/spaces)
- [Using GitHub Copilot Spaces](https://docs.github.com/en/copilot/how-tos/provide-context/use-copilot-spaces/use-copilot-spaces)
- [Using Copilot cloud agent on GitHub](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-on-github)
- [GitHub Pages documentation](https://docs.github.com/en/pages)
- [Workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
