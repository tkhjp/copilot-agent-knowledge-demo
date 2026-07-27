# GitHub Repository における共有 Project Knowledge の管理・利用設計

**対象:** code graph、test knowledge、architecture metadata、domain rule など、Repository 内で共有するプロジェクト知識  
**想定利用者:** 開発者、テスト担当者、GitHub Copilot 利用者、CI/CD 管理者、プロジェクト管理者  
**ステータス:** 実装・運用方針案  
**更新日:** 2026-07-27

---

## 1. 目的と結論

本資料の目的は、ある Repository に紐づく共有 Project Knowledge を、GitHub 上でどのように保存・更新・確認・利用するかを定義することです。

対象となる knowledge の例:

- code graph
- symbol / call / dependency / inheritance relationship
- module responsibility
- test impact
- test policy
- domain rule
- architecture decision
- generator / schema metadata

推奨する基本構成は次です。

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

基本原則:

1. Knowledge の正本は Repository に置く
2. Wiki は Repository から一方向同期する
3. Wiki の feedback は Issue / Pull Request に戻す
4. generated artifact の conflict は手動 merge せず再生成する
5. Agent も branch と Pull Request を経由する
6. Agent Session は knowledge database ではなく provenance として扱う
7. 大規模 raw graph は Repository に無制限に蓄積しない

---

## 2. 今回比較する GitHub 機能

今回の目的に直接関係する機能だけを比較します。

| 機能 | 主な役割 | 適している用途 | 適していない用途 |
|---|---|---|---|
| Repository files + Git / Pull Request | Knowledge の正本、version、review | source と knowledge の一体管理、変更履歴、CI | 人向けの見やすい portal、巨大 graph の対話検索 |
| GitHub Wiki | 人向けの閲覧・確認画面 | overview、diagram、onboarding、feedback 導線 | Source of Truth、raw graph 全量、Agent の必須 context |
| Copilot Spaces | Copilot 用の curated context | 複数 document をまとめた問答、onboarding、task-specific context | 厳密な version 管理、generated artifact の保存、競合解決 |
| Copilot Agent / Session | Knowledge を利用した作業と実行履歴 | 調査、test generation、validation、PR 作成、provenance | 長期共有 knowledge の保存先 |
| GitHub Pages | 高度な人向け表示 | 全文検索、interactive graph、custom UI | Knowledge の正本、PR を経由しない直接更新 |

周辺機能として、Pull Request、CODEOWNERS / Rulesets、GitHub Actions、Issues、MCP を組み合わせます。これらは独立した knowledge 保存先ではなく、更新・承認・自動化・feedback・外部接続のために利用します。

### 2.1 Repository files + Git / Pull Request

Repository 内の file を knowledge の Source of Truth とします。

```text
docs/agent-knowledge/generated/
docs/agent-knowledge/curated/
artifacts/codegraph/
```

できること:

- source code と同じ branch / commit / Pull Request で管理
- diff、review、approval、merge
- CI による freshness / integrity check
- branch protection や ruleset による運用強制
- Repository index を通じた Copilot retrieval

注意点:

- Git は競合を自動的に意味解決するわけではない
- generated file や binary graph は手動 merge に向かない
- graph が大きい場合は clone size と history size が増える

### 2.2 GitHub Wiki

Wiki は人が knowledge を閲覧・確認する presentation layer として利用します。

適する内容:

- system overview
- module responsibility
- dependency / test impact の要約
- Mermaid diagram
- domain rule / testing policy
- source file、Issue、Pull Request への link

本体 Repository とは別の Wiki Git Repository で管理されるため、Source of Truth にはしません。

```text
Repository knowledge
        ↓ one-way publish
GitHub Wiki
        ↓ human review
Issue / Pull Request
        ↓
Repository change
```

### 2.3 Copilot Spaces

Spaces は、Copilot が参照する context をテーマ単位でまとめる用途に適しています。

例:

```text
Space: Payment Test Knowledge
├── testing policy
├── payment module knowledge
├── related Issue / Pull Request
└── instructions
```

適する用途:

- Copilot Chat での質問
- 複数 document を横断した onboarding
- 特定テーマの curated context
- Repository file、Issue、Pull Request、free text の組み合わせ

本設計での位置付け:

```text
Repository files = Source of Truth
Space            = Copilot consumption view
```

GitHub file など GitHub 上の source は更新に追従しますが、Space 自体を generated artifact の正本や conflict resolution の場所にはしません。

IDE から Space を利用する場合は GitHub MCP server を利用します。IDE 利用時には repository context と uploaded file に制約があるため、Repository 内の knowledge files を主経路として残します。

### 2.4 Copilot Agent / Session

Agent は knowledge の保存先ではなく、knowledge を使って作業する実行主体です。

Agent が行うこと:

- knowledge freshness の確認
- target symbol の graph query
- source / generated / curated knowledge の確認
- test または code change の作成
- knowledge の再生成
- test / CI command の実行
- branch / Pull Request の作成

Session が残すもの:

- prompt
- response
- command
- tool usage
- read / changed files
- validation result
- branch / Pull Request

Session は実行理由を確認するための provenance であり、次の Agent が参照する正式な handoff は commit、branch、Pull Request、Repository knowledge です。

### 2.5 GitHub Pages

Wiki より高度な UI が必要な場合に Pages を追加します。

採用条件:

- graph の interactive visualization が必要
- client-side search が必要
- navigation や layout を自由に設計したい
- static site generator を利用したい

Pages も Repository から build する downstream view とし、Source of Truth にはしません。

---

## 3. 目的別の推奨編成

### 3.1 共有 Knowledge を version 管理し、人が確認する

最小構成:

```text
Repository knowledge files
+ Pull Request / review
+ GitHub Actions
+ GitHub Wiki
+ Issue feedback
```

利用方法:

1. Repository に knowledge を保存
2. Pull Request で変更・review
3. CI で freshness / integrity を確認
4. merge 後に Wiki へ publish
5. Wiki で確認した問題を Issue に登録

これは本 Project の基本構成です。

### 3.2 Copilot に knowledge を使った質問をさせる

```text
基本構成
+ Copilot Spaces
```

利用方法:

1. Source of Truth は Repository に維持
2. 重要 document、Issue、Pull Request を Space に追加
3. Space の instructions で利用目的を限定
4. Copilot Chat でテーマ単位の問答に利用

Space は knowledge のコピー先ではなく、Copilot 向けの selection / organization layer として扱います。

### 3.3 Agent に test generation / knowledge update を行わせる

```text
基本構成
+ Custom Agent
+ Agent Skill
+ Hook
+ Agent Session
```

利用方法:

1. User が Agent task を開始
2. Hook が freshness を確認
3. Skill が graph slice と knowledge を取得
4. Agent が branch 上で変更
5. Agent が `make test` / `make check` を実行
6. Agent が Pull Request を作成
7. Human が review / merge
8. Wiki が更新

Source of Truth と approval rule は Agent 導入後も変更しません。

### 3.4 Graph を見やすく可視化する

```text
基本構成
+ GitHub Pages
```

Wiki では module summary と主要 diagram を表示し、Pages では検索・filter・interactive graph を提供します。

```text
Repository graph / compact view
        ↓ build
GitHub Pages
        = rich visualization
```

### 3.5 大規模 graph を Agent が query する

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
└── MCP 経由で query
```

この構成を採用する条件:

- graph が Repository に収まりにくい
- update frequency が高い
- 複数 Repository を横断する
- traversal / path query が必要
- Agent が必要な subgraph だけ取得する必要がある

GitHub 内だけで任意の code graph を常時 traversal query する汎用 GraphDB を構成するのではなく、Repository に version pointer を置き、外部 GraphDB と MCP を組み合わせます。

---

## 4. 推奨 Architecture

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
                                           ├── Copilot Spaces source
                                           └── Wiki / Pages publish
                                                        
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

## 5. Repository 内の保存構成

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

## 6. Version と鮮度

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

## 7. 更新 Workflow

### 7.1 Source code を変更する

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

### 7.2 Curated knowledge を変更する

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

### 7.3 Generator を変更する

同じ Pull Request に次を含めます。

- generator code
- generator / schema version
- regenerated graph
- regenerated knowledge views
- regression tests

CI は同じ input から同じ logical output が得られることを確認します。

---

## 8. Conflict 解決

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

## 9. Wiki 更新・同期

### 9.1 同期方向

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

### 9.2 Managed page と Manual page

| Page | 管理方法 |
|---|---|
| Managed page | Repository から Actions で生成・上書き |
| Manual page | Wiki 上で人が管理。Workflow は削除しない |

Manual page は meeting note や一時的な説明に使えますが、Agent の正式な knowledge source にはしません。

### 9.3 Page metadata

Managed page には次を表示します。

```markdown
> **管理方式:** Repository から自動同期  
> **Source repository:** `owner/repository`  
> **Published from commit:** `abcdef1`  
> **Source digest:** `sha256:...`  
> **Generator version:** `1.1.0`  
> **Status:** CURRENT  
> **修正方法:** Wiki を直接編集せず Issue または Pull Request を作成してください。
```

### 9.4 Publish workflow

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

これにより、古い source commit の publish が新しい内容を後から上書きすることを防ぎます。

---

## 10. Agent 利用時の Workflow

### 10.1 Agent を使用しない場合

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

### 10.2 Agent を使用する場合

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

### 10.3 Agent Pull Request の provenance

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

## 11. 本 Demo での採用範囲

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

現在の標準 workflow:

```text
Repository Knowledge Pack
        ↓ Pull Request / CI
merge to develop
        ↓
Wiki mirror

必要に応じて:
- Copilot Spaces を consumption view として追加
- Agent を execution layer として追加
- Pages を visualization layer として追加
- External GraphDB + MCP を large graph query layer として追加
```

---

## 12. 運用ルール

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

## 13. 公式仕様参照

- [About wikis](https://docs.github.com/en/communities/documenting-your-project-with-wikis/about-wikis)
- [Adding or editing wiki pages](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages)
- [About GitHub Copilot Spaces](https://docs.github.com/en/copilot/concepts/context/spaces)
- [Using GitHub Copilot Spaces](https://docs.github.com/en/copilot/how-tos/provide-context/use-copilot-spaces/use-copilot-spaces)
- [Using Copilot cloud agent on GitHub](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-on-github)
- [GitHub Pages documentation](https://docs.github.com/en/pages)
- [Workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
