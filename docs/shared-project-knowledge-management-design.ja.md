# GitHub Repository における共有プロジェクト知識の管理・利用アーキテクチャ

**対象:** code graph、test code、test metadata、architecture information、domain rule など、Repository に紐づく共有プロジェクト知識  
**想定読者:** ソフトウェア設計・開発プロセスに習熟しているが、GitHub の周辺サービスには必ずしも詳しくないエンジニア  
**位置付け:** アーキテクチャ・運用方針案  
**更新日:** 2026-07-27

> GitHub のサービス名、ファイル名、コマンド、一般的な Git 用語は原語で記載します。それ以外の設計概念は、可能な限り日本語で説明します。

---

## 1. 要約

本資料は、特定の GitHub Repository に紐づく共有プロジェクト知識を、どこに保存し、どのように版管理・レビュー・同期し、人と Copilot Agent がどのように利用するかを定義します。

対象となる情報の例は次のとおりです。

- code graph: symbol、call、dependency、inheritance、test impact
- test code、test inventory、coverage summary、quality metadata
- module responsibility、architecture decision、domain rule、testing policy
- generator version、schema version、source digest、artifact digest

中心となる設計判断は、**Repository 内の版管理対象ファイルを正本（Source of Truth）とし、Wiki、Spaces、Agent Session を用途別の派生レイヤーとして扱う**ことです。

```text
Repository 内の版管理対象ファイル
        = 正本 / 正式な記録元

Git branch / commit / Pull Request / CI
        = 変更管理 / 検証 / 競合検出

GitHub Wiki
        = 人向けの派生表示

Copilot Spaces
        = Copilot 利用向けに選別したコンテキスト

Copilot Agent
        = 実行・変更提案の担い手

Agent Session
        = 実行履歴・追跡情報
```

整合性の基準は常に Repository 側に置きます。Wiki や Spaces は Repository の状態を反映する派生情報であり、反映には時間差が生じる可能性があります。Agent が作成した変更も、通常の branch、Pull Request、CI、レビューを経由します。

### 1.1 推奨する基本構成

```text
Source code / tests
        ↓
決定的に再生成可能な知識生成処理
        ↓
Repository 内知識パック
        ↓
Pull Request + CI + review
        ↓ merge
        ├── Tool / Copilot / Agent が参照
        ├── Wiki へ一方向に公開
        └── Issue で feedback を受付
```

### 1.2 対象外

本設計は、次を直接実現するものではありません。

- GitHub Wiki を主データベースとして運用すること
- Agent Session を長期知識ストアとして検索・再利用すること
- Git の merge 機構だけで意味上の競合を自動解決すること
- 大規模な graph traversal を GitHub の標準機能だけで実現すること
- Repository と Wiki の内容を双方向に自動同期すること

---

## 2. 設計原則

### P-01: 正本を一つにする

プロジェクト知識の正本は、原則として source code と同一 Repository 内の版管理対象ファイルに置きます。

これにより、次の関係を同一の Git history 上で追跡できます。

```text
source の状態
↕
自動生成 graph / knowledge view
↕
review / approval / CI result
```

### P-02: 正本と派生表示を分離する

Repository、Wiki、Spaces、Agent Session の責務を混在させません。

| レイヤー | 主な責務 | 正本か |
|---|---|---:|
| Repository 内知識パック | 版管理された知識、manifest、検索可能な生成物 | はい |
| GitHub Wiki | 人向け閲覧、説明、確認、feedback 導線 | いいえ |
| Copilot Spaces | タスク単位に選別した Copilot 用コンテキスト | いいえ |
| Agent Session | prompt、tool call、変更理由、検証結果 | いいえ |
| GitHub Pages | 検索、filter、graph visualization を含む表示画面 | いいえ |

### P-03: 自動生成物は再生成可能な出力として扱う

自動生成 Markdown、raw graph、manifest は手編集対象にしません。競合時は対象 branch を最新化した上で generator を再実行します。

### P-04: 承認境界は人と Pull Request に残す

Agent を導入しても、正本、review policy、merge gate は変更しません。Agent は変更案と検証結果を作成しますが、承認境界は Pull Request と CI に置きます。

### P-05: 大規模化ではデータを外部化し、管理情報は Repository に残す

Graph が Repository に適さない規模になった場合、complete graph を external GraphDB または object storage に移します。ただし、source digest、snapshot ID、schema version、query client は Repository に残します。

---

## 3. 関連する GitHub 機能

今回の課題に直接関係する機能だけを比較します。

### 3.1 Repository Files + Git / Pull Request

#### 提供できること

- source code と knowledge を同一 branch / commit / Pull Request で管理する
- diff、review comment、approval、merge history を保持する
- manifest により source の状態と knowledge artifact を対応付ける
- CODEOWNERS、Rulesets、branch protection で変更ルールを強制する
- GitHub Actions で生成、鮮度、整合性を検証する
- Repository context を利用する Tool / Copilot / Agent から参照する

#### 制約・適さない用途

- Git は意味上の競合を自動解決しない
- compressed graph、binary artifact、自動生成ファイルの手動 merge には向かない
- 高頻度に更新される大量 artifact は Repository history を肥大化させる
- graph traversal や集計 query の実行基盤ではない
- 人向け portal としての navigation / visualization は限定的

#### 本設計での責務

```text
Repository Files + Git / Pull Request
        = 正本 + 変更管理の仕組み
```

---

### 3.2 GitHub Wiki

GitHub Wiki は Repository に紐づく人向け documentation 画面です。Wiki の内容は本体 Repository とは別の Git Repository（`<repository>.wiki.git`）で管理されます。

#### 提供できること

- Markdown、画像、link、Mermaid diagram を表示する
- system overview、module responsibility、test impact を整理する
- sidebar を利用して knowledge portal を構成する
- onboarding、design review、knowledge confirmation を支援する
- Wiki 自体の revision history を保持する
- source file、Issue、Pull Request への navigation を提供する

#### 制約・適さない用途

- 本体 Repository の Pull Request と同一トランザクションで更新できない
- raw code graph 全量や大量の自動生成物の保存には向かない
- 任意の graph traversal / query を提供しない
- Copilot Agent が必ず利用する primary context ではない
- Repository と Wiki の双方向同期は競合と ownership を複雑化する

#### 本設計での責務

```text
GitHub Wiki
        = 人向けの派生表示
        ≠ 正本
```

同期方向は Repository から Wiki への一方向とします。Wiki で検出した誤りは、Issue または Pull Request として Repository 側へ戻します。

---

### 3.3 Copilot Spaces

Copilot Spaces は、GitHub file、Issue、Pull Request、free text、Space instructions などをタスク単位に集約し、Copilot の回答コンテキストとして利用する機能です。

#### 提供できること

- 複数の情報源を domain / task 単位で選別する
- Space 単位で instructions を設定する
- onboarding、support、特定業務向け Q&A を標準化する
- GitHub 上の resource 更新を反映したコンテキストを利用する
- IDE から GitHub MCP server を経由して参照する

例:

```text
Space: Payment Test Knowledge
├── testing policy
├── payment module knowledge
├── related issues / pull requests
└── task instructions
```

#### 制約・適さない用途

- 自動生成物の正本にはならない
- branch / Pull Request / review / conflict resolution を代替しない
- source commit と厳密に結び付いた snapshot 管理ではない
- IDE 利用は GitHub MCP server と Agent mode が前提で、resource type に制約がある
- Space 内部の検索を任意の graph query API として利用できない

#### 本設計での責務

```text
Repository Files = 正本
Copilot Spaces   = Copilot 利用向けの選別済みコンテキスト
```

Spaces は必須ではありません。複数 document をタスク別に選別し、Copilot の Q&A 品質と利用者体験を改善する場合に採用します。

---

### 3.4 Copilot Agent / Agent Session

Copilot Agent は Repository context を調査し、隔離された実行環境で command を実行し、branch / Pull Request に変更を作成する機能です。Agent Session はその実行単位と履歴です。

#### 提供できること

- source、test、Repository knowledge を探索する
- graph query tool を使って対象 symbol 周辺を取得する
- branch 上で code / test / knowledge を変更する
- generator、test、lint、validation command を実行する
- Pull Request を作成する
- prompt、response、tool usage、changed files、validation result を記録する

#### 制約・適さない用途

- Custom Agent 定義を配置しただけでは Session は開始されない
- Session は長期共有 knowledge の正本ではない
- Agent output にも CI と人の review が必要
- Session URL を Agent 間の正式な引継ぎ情報にしない
- Wiki を直接更新する主体にはしない

#### 本設計での責務

```text
Copilot Agent = 実行・変更提案の担い手
Agent Session = 実行履歴・追跡情報
```

正式な引継ぎは、commit、branch、Pull Request、manifest、Repository knowledge files です。

---

### 3.5 GitHub Pages

GitHub Pages は Repository content から static site を build / publish する表示機能です。

#### 提供できること

- custom layout、全文検索、filter を備えた portal
- interactive graph visualization
- Wiki より高度な navigation と UI
- Repository source からの自動 deployment

#### 制約・適さない用途

- 正本にはしない
- GraphDB や test DB の代替ではない
- content の変更・review は元 Repository で実施する
- site generator、frontend、deployment の保守費用が追加される

#### 本設計での責務

Wiki で満たせない interactive visualization、検索、filter 要件が明確になった場合に追加する任意の表示レイヤーです。

---

### 3.6 周辺機能

以下は独立した knowledge store ではありませんが、運用を成立させるために使用します。

| 機能 | 本設計での用途 |
|---|---|
| GitHub Actions | generation、freshness / integrity check、Wiki / Pages publish |
| CODEOWNERS / Rulesets | path ownership、required review、required checks、merge policy |
| Issues / Issue Forms | Wiki からの defect、stale、update request の受付 |
| Releases / Release Assets | 不変 snapshot の配布 |
| Actions Artifacts | CI run 単位の一時 report、test result、diagnostic artifact |
| MCP | external GraphDB、test DB、internal API と Agent の接続 |

---

## 4. 要件

### 4.1 必須要件

| ID | 要件 | 受入条件 | 対応する仕組み |
|---|---|---|---|
| M-01 | 正本の一意性 | 正本と派生表示を明確に区別できる | Repository versioned files |
| M-02 | Source と knowledge の対応付け | 各 artifact が対象 source state を識別できる | manifest / source digest / commit history |
| M-03 | 統制された更新 | 変更が diff、review、approval を経由する | branch / Pull Request |
| M-04 | 再現可能な生成 | 同一 logical input から同一 logical output を生成できる | deterministic generator |
| M-05 | 鮮度・整合性 gate | STALE、BROKEN、missing artifact を merge 前に検出する | CI required check |
| M-06 | 競合解決方針 | artifact 種別ごとの解決方法が定義されている | Git + regeneration rule |
| M-07 | 人による確認 | 非実装者でも概要・状態・source link を確認できる | GitHub Wiki |
| M-08 | Tool / Agent からの参照 | 全量ではなく必要な knowledge slice を取得できる | Repository context + query tool |
| M-09 | Access control | Repository permission と同等以上の境界で保護される | Repository permission / ruleset |
| M-10 | 追跡可能性 | actor、change、review、validation result を追跡できる | commit / PR / CI |
| M-11 | Size / retention policy | Repository に保持する artifact の上限と外部化条件がある | threshold + manifest / snapshot pointer |

### 4.2 必須構成

```text
Repository 内知識パック
+ Git / Pull Request
+ 再生成可能な generator
+ GitHub Actions
+ GitHub Wiki
+ Issue Feedback
```

この構成を導入せずに Spaces や Agent を追加すると、コンテキストは増えても version consistency と governance を保証できません。

### 4.3 追加要件

| ID | 要件 | 採用条件 | 対応する仕組み |
|---|---|---|---|
| N-01 | Copilot 用の選別済みコンテキスト | 複数 document の探索コストが高い | Copilot Spaces |
| N-02 | Agent による実行 | test generation、knowledge refresh、validation を委譲したい | Custom Agent / Skill / Hook |
| N-03 | 実行経緯の確認 | Agent の command と判断経緯を確認したい | Agent Session |
| N-04 | 高度な可視化 | Wiki では interactive graph / search を満たせない | GitHub Pages |
| N-05 | 大規模 graph query | traversal、cross-repository query、低 latency が必要 | External GraphDB + MCP |
| N-06 | 不変形式での配布 | 特定時点の graph / report を再現可能に配布したい | Release Assets |
| N-07 | 実行単位の診断情報 | CI run ごとの test result を一定期間保持したい | Actions Artifacts |
| N-08 | 強い変更統制 | owner approval と required checks を強制したい | CODEOWNERS / Rulesets |
| N-09 | 長期品質分析 | coverage / mutation / quality trend を横断集計したい | External Test DB |

追加要件は必須構成を置き換えません。追加レイヤーは必ず Repository の正本と version binding を参照します。

---

## 5. 情報種別と保存方針

| 情報種別 | 推奨保存先 | Versioning / Retention Policy |
|---|---|---|
| Source code / test code | Repository | source と同一 branch / PR |
| 人手管理 policy / domain rule | Repository Markdown + Wiki mirror | human review 必須 |
| 自動生成 module / test-impact summary | Repository Markdown + Wiki mirror | generator 管理、手編集禁止 |
| Code graph: 小・中規模 | Repository compressed artifact + manifest | source digest と一体管理 |
| Code graph: 大規模・高頻度 | External GraphDB / object storage + Repository manifest | snapshot ID / URI / schema を記録 |
| Test execution result | Actions Artifact または external Test DB | 実行単位のデータ。通常は Git history に常設しない |
| Coverage / quality trend | compact Repository summary または external Test DB | retention と aggregation 要件で判断 |
| 不変 graph / report bundle | Release Asset | tag / release 単位 |
| Agent execution history | Agent Session | 追跡用。正本ではない |
| Branch-local runtime knowledge | `.agent-runtime/` | 一時データ、commit しない |

### 5.1 Repository 内保存方式

次の条件を満たす場合は、raw graph を Repository に保持できます。

- artifact size が小規模または中規模
- update frequency が限定的
- clone / checkout performance に影響しない
- graph query が file-based tool で足りる

### 5.2 外部 graph 保存方式

次の条件のいずれかを満たす場合、complete graph を外部化します。

- Repository size / history growth が無視できない
- graph update が高頻度
- cross-repository graph が必要
- traversal、path search、aggregate query が主要用途
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

## 6. 機能の組み合わせ方

### 6.1 標準構成: Knowledge 共有 + 人による確認

```text
Source code / tests
        ↓
Knowledge generator
        ↓
Repository 内知識パック
        ↓
Pull Request + CI + review
        ↓ merge
        ├── Tool / Copilot が参照
        └── Wiki へ一方向に publish
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

### 6.2 Copilot Q&A を追加する

標準構成に Copilot Spaces を追加します。

```text
Repository の正本
        ↓ selected resources
Copilot Space
        ↓
Copilot Chat / onboarding / task-specific Q&A
```

採用条件:

- 利用者が複数 file / Issue / Pull Request を毎回探索している
- domain または task ごとに context boundary を設けたい
- Copilot に共通 instructions を付与したい

Spaces は Repository snapshot や変更管理の代替ではありません。

### 6.3 Agent に変更作業を実行させる

標準構成に Agent layer を追加します。

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

正本、承認境界、merge rule は変更しません。

### 6.4 高度な可視化を追加する

標準構成に GitHub Pages を追加します。

```text
Repository compact graph / metadata
        ↓ static build
GitHub Pages
        = search / filter / interactive graph
```

Wiki は summary と navigation、Pages は detail visualization を担当します。

### 6.5 Agent 向けに大規模 graph query を追加する

```text
Repository manifest / compact views
        ↓
Agent Skill / MCP client
        ↓
External GraphDB
        ↓
必要な subgraph のみ返却
```

採用条件:

- graph が Repository 内保存方式の上限を超える
- path / traversal query が必要
- cross-repository dependency を扱う
- query result を context budget に合わせて縮約する必要がある

---

## 7. 論理構成

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
Source / Tests ──→ Generator ──→ Repository 内知識パック
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
source + Repository knowledge を参照
      ↓
graph slice を query
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

## 8. Repository 内の保存構成

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
| raw graph | generator | 再生成のみ |
| generated knowledge | generator | 再生成のみ |
| manifest | generator | 再生成のみ |
| curated knowledge | Human、Agent proposal | 内容 review 必須 |
| runtime knowledge | Hook / Agent | 一時データ、commit しない |

---

## 9. Version と整合性

### 9.1 Manifest の契約

Knowledge Pack は machine-readable manifest を持ちます。

```json
{
  "schema_version": 1,
  "generator_version": "1.1.0",
  "source_digest": "sha256:...",
  "source_files": {
    "src/payment_service/service.py": "sha256:..."
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
  }
}
```

必須項目:

- schema version
- generator version
- source digest
- source file digest
- graph artifact digest
- knowledge artifact digest
- external graph を利用する場合は snapshot ID / URI

### 9.2 Knowledge 状態

| 状態 | 条件 | 動作 |
|---|---|---|
| CURRENT | source digest が一致 | committed knowledge を利用 |
| STALE | source digest が不一致 | merge 前に再生成。Agent task では runtime knowledge を生成可能 |
| BROKEN | artifact 不足、hash / schema error | 利用停止し再生成 |

### 9.3 整合性モデル

| データ面 | 整合性 |
|---|---|
| Repository source + knowledge in same commit | 強い版対応 |
| Pull Request branch | branch 内で一貫 |
| Wiki | 遅延を許容する一方向同期 |
| Copilot Spaces | 選択した resource の更新反映に依存 |
| Agent Session runtime knowledge | Session 内で一時的に一貫 |
| External GraphDB | snapshot ID / source digest の一致が必要 |

Wiki や Spaces が一時的に古くても、Repository の正本は影響を受けません。

---

## 10. 更新の流れ

### 10.1 Source code を変更する

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

### 10.2 Curated knowledge を変更する

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

### 10.3 Generator を変更する

同じ Pull Request に次を含めます。

- generator code
- generator / schema version
- regenerated graph
- regenerated knowledge views
- regression tests

CI は同じ input から同じ logical output が得られることを確認します。

### 10.4 必須 CI gate

| Gate | 確認内容 |
|---|---|
| Unit / integration test | 実装が壊れていない |
| Freshness check | source digest と manifest が一致 |
| Deterministic regeneration | 再生成結果が commit 済み artifact と論理的に一致 |
| Schema validation | manifest / graph schema が有効 |
| Secret / size check | 機密情報と過大 artifact を拒否 |
| Wiki export check | managed Wiki pages を生成できる |

`STALE` または `BROKEN` の場合は merge しません。

---

## 11. 競合解決

Git は競合の検出と履歴管理を行います。解決方法は artifact 種別で分けます。

| 対象 | 解決方法 |
|---|---|
| Source code | merge / rebase 後に人が意味を確認 |
| Curated Markdown | three-way merge。内容 owner が判断 |
| Generated Markdown | 手動 merge しない。最新 branch で再生成 |
| Raw graph | 手動 merge しない。最新 branch で再生成 |
| Manifest | 手動 merge しない。最新 branch で再生成 |
| Wiki managed page | Repository を正とし、次回 publish で置換 |
| External graph snapshot | 新しい snapshot を生成し、manifest pointer を更新 |

複数 Agent / developer が並行作業する場合:

```text
Agent A branch ──→ PR A ──→ merge
Agent B branch ──→ rebase latest develop
                 ──→ regenerate knowledge
                 ──→ make check
                 ──→ merge
```

Compressed graph や binary artifact を conflict editor で直接修正しません。

---

## 12. Wiki の更新と feedback

### 12.1 同期方向

```text
Repository → Wiki
```

内容の自動双方向同期は行いません。

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

### 12.2 Managed page と Manual page

| Page | 管理方法 |
|---|---|
| Managed page | Repository から Actions で生成・上書き |
| Manual page | Wiki 上で人が管理。Workflow は削除しない |

Manual page は meeting note や一時的な説明に使えますが、Agent の正式な knowledge source にはしません。確定 knowledge になった内容は Repository に移します。

### 12.3 公開処理

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

### 12.4 Wiki page の metadata

Managed page の先頭には次の情報を表示します。

```markdown
> **管理方式:** Repository から自動同期される managed page
> **Source repository:** `owner/repository`
> **Published from commit:** `abcdef1`
> **Source digest:** `sha256:...`
> **Generator version:** `1.1.0`
> **Status:** CURRENT
> **Source file:** `docs/agent-knowledge/generated/...`
> **修正方法:** Wiki を直接編集せず、Issue または Pull Request を作成してください。
```

### 12.5 Wiki 公開失敗時

Wiki は派生表示であるため、publish failure で正本を巻き戻しません。

- Repository merge は保持する
- workflow failure を通知する
- manual rerun を可能にする
- 次回は最新 default branch から再生成する
- Wiki に source commit / status を表示し、古い表示を識別できるようにする

---

## 13. Agent 利用時の流れ

### 13.1 Agent を使用しない場合

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

### 13.2 Agent を使用する場合

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

### 13.3 Agent Pull Request の追跡情報

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

### 13.4 Agent 障害時の扱い

| 状況 | 方針 |
|---|---|
| Agent が knowledge を誤解した | Pull Request review と CI で default branch への混入を防ぐ |
| Session が失われた | commit、PR、manifest を正式な引継ぎとして利用する |
| External GraphDB が利用不能 | Repository compact view に降格するか task を停止する |
| runtime knowledge が BROKEN | generated claim を利用せず current source を直接確認する |
| Agent が過大な変更を作成した | Pull Request を分割し、変更範囲を限定する |

---

## 14. セキュリティと権限

### 14.1 Access control

- Repository knowledge は Repository permission に従う
- Wiki は Repository visibility と access policy を確認する
- External GraphDB credential は Secrets / Environment で管理する
- Agent / Workflow は least privilege とする
- write permission は publish / update job のみに限定する

### 14.2 Knowledge に含めない情報

- secret / token / private key
- production customer data
- unrestricted log
- personal data
- 機密性の高い prompt / Session transcript
- ライセンス上共有できない source / document

### 14.3 外部 GraphDB + MCP

- query result の最大件数と depth を制限する
- Repository / branch / source digest を query condition に含める
- read-only tool を基本とする
- write operation は別 tool と承認フローに分離する
- query log を監査可能にする

---

## 15. 運用監視、バックアップ、復旧

### 15.1 記録する情報

- current / stale / broken artifact 数
- generator duration
- graph node / edge count
- artifact size
- Wiki publish source commit
- Wiki publish lag
- Agent task success / failure
- external query failure rate

### 15.2 バックアップ対象

| 対象 | 復旧元 |
|---|---|
| Repository knowledge | Git clone / mirror backup |
| Wiki | `<repository>.wiki.git` clone |
| Release snapshot | Release assets |
| External GraphDB | DB snapshot / object storage backup |
| Agent Session | 補助情報。正式復旧元にはしない |

### 15.3 復旧原則

- 自動生成 artifact は source + generator から再生成する
- Wiki managed page は Repository から再publishする
- curated knowledge は Git history から復旧する
- external graph は snapshot ID と manifest の対応を検証する

---

## 16. 段階導入

### Phase 1: 基本管理

```text
Repository Knowledge Pack
+ manifest
+ deterministic generator
+ CI freshness / integrity
+ Pull Request review
+ Wiki mirror
```

### Phase 2: Copilot 利用

```text
+ Repository instructions
+ graph query tool
+ optional Copilot Spaces
```

### Phase 3: Agent 実行

```text
+ Custom Agent
+ Skill
+ Hook
+ Agent Session
+ PR provenance rule
```

### Phase 4: 大規模化

```text
+ External GraphDB / Test DB
+ MCP
+ Pages visualization
+ release / retention policy
```

まず正本、版対応、整合性の契約を確立し、その後に Spaces、Agent、Pages を追加します。

---

## 17. 本 Demo での採用判断

| 機能 | 現在の扱い |
|---|---|
| Repository Knowledge Pack | 正本として採用 |
| Git / Pull Request / CI | 更新・検証に採用 |
| Wiki | 人向け mirror として採用 |
| Issue Form | Wiki feedback 入口として採用 |
| Copilot Agent / Session | Agent 定義済み。実 Session で利用確認 |
| Copilot Spaces | 未採用。Copilot Q&A 用 context が必要な場合に追加 |
| GitHub Pages | 未採用。interactive graph / search が必要な場合に追加 |
| External GraphDB / MCP | 未採用。graph size と query 要件で判断 |

---

## 18. 運用ルール

1. 正本は Repository に置く
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

## 19. 公式仕様参照

- [About wikis](https://docs.github.com/en/communities/documenting-your-project-with-wikis/about-wikis)
- [Adding or editing wiki pages](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages)
- [About GitHub Copilot Spaces](https://docs.github.com/en/copilot/concepts/context/spaces)
- [Using GitHub Copilot Spaces](https://docs.github.com/en/copilot/how-tos/provide-context/use-copilot-spaces/use-copilot-spaces)
- [Using Copilot cloud agent on GitHub](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-on-github)
- [GitHub Pages documentation](https://docs.github.com/en/pages)
- [Workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
