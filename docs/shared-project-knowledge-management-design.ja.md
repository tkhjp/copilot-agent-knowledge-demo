# GitHub Repository における共有プロジェクト知識の管理設計

**対象:** code graph、test knowledge、architecture metadata など、プロジェクト内で共有する前提知識  
**想定利用者:** 開発者、テスト担当者、GitHub Copilot Agent、CI/CD、プロジェクト管理者  
**ステータス:** 実装・運用方針案  
**更新日:** 2026-07-27

---

## 1. Executive Summary

本設計では、ある GitHub Repository に紐づく共有プロジェクト知識を、次の責務分担で管理します。

| 責務 | 採用する仕組み |
|---|---|
| 知識の正本 | 同一 Repository 内の versioned files |
| 変更管理 | Git branch、commit、Pull Request、review |
| 鮮度・整合性確認 | manifest、決定的 generator、CI check |
| 人向けの閲覧・確認画面 | GitHub Wiki |
| Wiki への反映 | default branch からの一方向自動同期 |
| Agent の参照先 | Repository 内の knowledge files と graph query tool |
| Agent による更新 | Agent branch → Pull Request → review → merge |
| 実行履歴 | Agent Session |

推奨構成は、**Repository を Source of Truth とし、Wiki を downstream の閲覧・確認画面として利用する方式**です。

```text
Source code / tests
        ↓
Knowledge generator
        ↓
Repository knowledge files
        ↓
Git branch / PR / CI / merge
        ├──────────────→ Agent が参照
        └──────────────→ Wiki へ一方向同期
```

重要な設計判断は次のとおりです。

1. Wiki を知識の正本にはしない
2. generated knowledge と人が管理する curated knowledge を分離する
3. source code と knowledge の更新を原則として同じ Pull Request で扱う
4. generated artifact の conflict は手動 merge せず、最新 branch 上で再生成する
5. Wiki の直接編集と Repository の双方向同期は行わない
6. Agent は Wiki を直接更新せず、必ず branch と Pull Request を経由する
7. 大規模な raw graph は、Repository に無制限に蓄積しない

---

## 2. 対象課題

プロジェクト内では、source code だけでは表現しにくい共有前提が発生します。

例:

- code graph
- symbol、call、dependency、inheritance の関係
- module responsibility
- test impact
- test policy
- domain rule
- architecture decision
- known limitation
- test execution metadata

これらを個人のローカル環境や一時的な Agent Session のみに置くと、次の問題が発生します。

- 他のメンバーが同じ知識を利用できない
- どの source version に対応する知識か分からない
- 更新競合を解決できない
- 古い知識を Agent が利用する
- 人が内容を確認しにくい
- 知識がどのように変更されたか追跡できない

本設計の目的は、共有前提となる知識を、GitHub の既存機能を利用して**共有、更新、review、同期、Agent 利用**できる状態にすることです。

---

## 3. 採用方針

### 3.1 選択肢

| 選択肢 | 概要 | 利点 | 主な問題 |
|---|---|---|---|
| A. Repository のみ | knowledge files を Repository に commit | version、PR、CI が利用可能 | 人向けの閲覧性が弱い |
| B. Wiki を正本にする | Wiki 上で knowledge を作成・更新 | 人が直接編集しやすい | source code と別 Git Repository になり、同期・競合・Agent 利用が複雑 |
| C. Repository 正本 + Wiki mirror | Repository で管理し、Wiki に一方向公開 | Git の変更管理と Wiki の閲覧性を両立 | publish workflow が必要 |

### 3.2 推奨

**C. Repository 正本 + Wiki mirror** を採用します。

理由:

- source code と knowledge を同じ review 単位で扱える
- Pull Request で差分を確認できる
- commit history により変更理由を追跡できる
- CI で knowledge の鮮度と再現性を検証できる
- Agent が同一 Repository 内のファイルを直接参照できる
- Wiki を人向けの可視化・確認画面として利用できる
- Wiki 側で内容が分岐することを防げる

---

## 4. 全体アーキテクチャ

```mermaid
flowchart TD
    S[Source code / tests] --> G[Deterministic knowledge generator]
    G --> R[Raw generated artifacts]
    G --> V[Generated knowledge views]
    H[Human-maintained curated knowledge] --> P[Repository knowledge pack]
    R --> P
    V --> P

    P --> B[Git branch]
    B --> CI[CI: freshness / deterministic check]
    CI --> PR[Pull Request review]
    PR --> M[Merge to default branch]

    M --> W[Wiki publish workflow]
    W --> UI[GitHub Wiki: browse / confirm]

    A[GitHub Copilot Agent] --> F[Freshness check]
    F --> Q[Read knowledge / query graph slice]
    Q --> B

    UI --> FB[Issue / Pull Request feedback]
    FB --> B
```

### 4.1 データフロー

```text
内容の流れ:
Repository → Wiki

確認・修正要求の流れ:
Wiki user → Issue / Pull Request → Repository → Wiki
```

Wiki から Repository へ knowledge file を自動的に戻す双方向同期は行いません。

---

## 5. Knowledge の分類

Knowledge は責務別に分離します。

### 5.1 Raw generated artifact

機械が生成する精密なデータです。

現在の Demo:

```text
artifacts/codegraph/
├── nodes.jsonl.gz
└── edges.jsonl.gz
```

用途:

- Agent tool からの graph query
- 別形式への変換
- test impact の算出
- debugging
- downstream system への import

運用ルール:

- 人が直接編集しない
- conflict 時に手動 merge しない
- generator から再生成する
- generator と schema の version を manifest に記録する

### 5.2 Generated knowledge view

Raw artifact から生成する、人と Agent が読みやすい投影です。

現在の Demo:

```text
docs/agent-knowledge/generated/
├── manifest.json
├── system-overview.md
├── modules/
└── test-impact/
```

用途:

- module 概要
- symbol inventory
- static branch candidate
- dependency summary
- test impact summary
- Wiki 表示

運用ルール:

- 人が直接編集しない
- raw graph と同じ generator lifecycle で更新する
- 変更差分は Pull Request 上で review する

### 5.3 Curated knowledge

人が判断し、管理するルールや前提です。

現在の Demo:

```text
docs/agent-knowledge/curated/
├── domain-rules.md
└── testing-policy.md
```

用途:

- domain rule
- test policy
- architecture decision
- forbidden operation
- review guideline

運用ルール:

- 通常の Markdown として branch / PR で変更する
- CODEOWNERS による review owner を設定する
- generator から上書きしない

### 5.4 Runtime branch knowledge

feature branch が default branch の knowledge より新しい場合に、一時生成する branch 用 knowledge です。

現在の Demo:

```text
.agent-runtime/
```

用途:

- Agent Session 内で現在 branch の source を正しく解釈する
- merge 前の変更に対する graph query

運用ルール:

- commit しない
- Session または working tree 内のみで利用する
- merge する knowledge baseline の代替にはしない

### 5.5 Wiki pages

Repository knowledge を人向けに表示する downstream copy です。

用途:

- browse
- onboarding
- visual confirmation
- knowledge review の入口
- Issue / Pull Request への導線

運用ルール:

- managed page は直接編集しない
- Repository からの publish workflow のみが更新する
- Wiki の記述より Repository と現在 source code を優先する

---

## 6. Repository 構成

本 Demo の構成を、そのまま基本形として利用できます。

```text
repository/
├── src/                                  source code
├── tests/                                tests
│
├── artifacts/codegraph/                  raw generated graph
│   ├── nodes.jsonl.gz
│   └── edges.jsonl.gz
│
├── docs/agent-knowledge/
│   ├── generated/                        generated knowledge views
│   │   ├── manifest.json
│   │   ├── system-overview.md
│   │   ├── modules/
│   │   └── test-impact/
│   └── curated/                          human-maintained knowledge
│       ├── domain-rules.md
│       └── testing-policy.md
│
├── tools/knowledge/                      generator / query / validator
│
└── .github/
    ├── agents/                           custom agents
    ├── skills/                           reusable knowledge procedure
    ├── hooks/                            session freshness check
    ├── workflows/
    │   ├── ci.yml
    │   ├── refresh-agent-knowledge.yml
    │   └── mirror-wiki.yml
    └── CODEOWNERS                        recommended
```

---

## 7. Version と鮮度の管理

### 7.1 Manifest

Knowledge Pack には machine-readable manifest を必須とします。

例:

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
  }
}
```

### 7.2 Source digest を主キーにする理由

Knowledge file 自体を同じ commit に含める場合、commit SHA を generated file 内に埋め込むと循環参照になります。

そのため、Repository 内の freshness 判定は source file の content digest を利用します。

```text
manifest.source_digest == current source digest
    → CURRENT

manifest.source_digest != current source digest
    → STALE
```

Wiki publish 時には、workflow が実行元 commit SHA をページ metadata または commit message に追加できます。

### 7.3 Knowledge status

| Status | 条件 | Agent / CI の動作 |
|---|---|---|
| CURRENT | source digest と manifest が一致 | committed knowledge を利用 |
| STALE | source digest が不一致 | merge 前は再生成必須。Agent Session 内では runtime knowledge を生成可能 |
| BROKEN | artifact 不足、hash 不一致、schema error | 利用停止。generator から再生成 |

---

## 8. 更新 Workflow

## 8.1 Source code を変更する場合

原則として、source code と影響を受ける knowledge を同じ Pull Request で更新します。

```text
Developer / Agent
    ↓
feature branch を作成
    ↓
source code / tests を変更
    ↓
make knowledge
    ↓
source + generated knowledge を commit
    ↓
make check
    ↓
Pull Request
    ↓
review / merge
    ↓
Wiki publish
```

推奨 command:

```bash
make knowledge
make check
```

CI は、source が変更されたのに generated knowledge が更新されていない場合、失敗させます。

Branch protection を使用する場合は、この CI を required check に設定します。

### 8.2 Curated knowledge を変更する場合

```text
Human / Agent proposal
    ↓
curated Markdown を branch 上で変更
    ↓
CODEOWNER review
    ↓
Pull Request merge
    ↓
Wiki publish
```

Curated knowledge は generator では変更しません。

Agent が変更案を作成することは可能ですが、最終承認は人が行います。

### 8.3 Generator を変更する場合

Generator 変更時は、次を同じ Pull Request に含めます。

- generator code
- schema version または generator version の更新
- regenerated raw graph
- regenerated knowledge views
- regression tests

CI は同じ input から同じ output が得られることを確認します。

---

## 9. Conflict 解決方針

Git commit と Pull Request により変更履歴と競合検出を行います。ただし、artifact 種別ごとに conflict の解決方法を分けます。

| 対象 | Conflict 解決方法 |
|---|---|
| Source code | 通常の Git merge / rebase と review |
| Curated Markdown | Git の three-way merge。内容を人が確認して解決 |
| Generated Markdown | 手動 merge しない。target branch を取り込み、generator で再生成 |
| Raw graph | 手動 merge しない。target branch を取り込み、generator で再生成 |
| Manifest | 手動 merge しない。generator で再生成 |
| Wiki managed page | Repository 側を正とし、次の publish で置換 |

### 9.1 複数 Agent が同時に変更する場合

各 Agent は独立 branch を使用します。

```text
Agent A branch ──→ PR A ──→ merge
Agent B branch ──→ PR B ──→ rebase on latest develop
                           ──→ regenerate knowledge
                           ──→ make check
                           ──→ merge
```

後から merge する Pull Request は、最新 default branch 上で generated artifact を再生成します。

Binary や compressed graph artifact を conflict editor で直接修正してはいけません。

---

## 10. Wiki の役割

Wiki は、ユーザーと knowledge のインタラクション画面として利用します。

### 10.1 Wiki で提供するもの

- System overview
- Module knowledge
- Test impact
- Domain rule
- Testing policy
- Update status
- Source Repository への link
- Issue / Pull Request 作成への導線

### 10.2 Wiki で行わないもの

- knowledge の正本管理
- generated page の直接編集
- Wiki と Repository の自動双方向同期
- Agent が参照する唯一の knowledge source
- raw graph の全量表示

### 10.3 ページ metadata

各 Wiki page の先頭に、次の情報を表示することを推奨します。

```markdown
> **管理方式:** Repository から自動同期される managed page  
> **Source repository:** `owner/repository`  
> **Published from commit:** `abcdef1`  
> **Source digest:** `sha256:...`  
> **Generator version:** `1.1.0`  
> **Status:** CURRENT  
> **修正方法:** Wiki を直接編集せず、source file の Pull Request を作成してください。
```

これにより、利用者は「何を見ているか」「どの source version に対応するか」を確認できます。

### 10.4 Wiki を確認・feedback の窓口にする

Content の同期は一方向ですが、feedback は逆方向に流します。

```text
Repository knowledge
        ↓ publish
Wiki page
        ↓ user review
Issue / Pull Request
        ↓
Repository change
        ↓ merge
Wiki page update
```

推奨する feedback 方法:

1. Wiki page から対応する Repository file を開く
2. 誤りまたは更新要求を Issue に登録する
3. Curated knowledge の変更は Pull Request を作成する
4. Generated knowledge の誤りは generator または source code の Issue として扱う
5. merge 後、Wiki が自動更新されたことを確認する

### 10.5 Wiki を正本にしない理由

GitHub Wiki は本体 Repository とは別の Git Repository として管理されます。

Wiki を正本にすると、次の追加問題が発生します。

- source code の Pull Request と knowledge change が分離する
- 本体 Repository と Wiki の version 対応が不明確になる
- Wiki 直接編集と自動 publish が競合する
- Agent が参照する context と人が見る Wiki が分岐する
- 双方向同期の conflict resolution が必要になる

そのため、本設計では Wiki を downstream mirror に限定します。

---

## 11. Wiki 同期 Workflow

### 11.1 Trigger

推奨 trigger:

- default branch への merge / push
- `docs/agent-knowledge/**` の変更
- Wiki exporter の変更
- manual `workflow_dispatch`

本 Demo:

```text
.github/workflows/mirror-wiki.yml
```

### 11.2 処理手順

```text
1. default branch を checkout
2. Wiki 用 Markdown を export
3. <repository>.wiki.git を clone
4. workflow 管理対象 page を置換
5. source commit / digest metadata を付与
6. Wiki commit を作成
7. Wiki default branch に push
8. publish result を記録
```

### 11.3 同時実行制御

Wiki publisher は単一 writer とします。

```yaml
concurrency:
  group: mirror-agent-knowledge-wiki
  cancel-in-progress: true
```

これにより、古い source commit の publish が新しい publish の後に上書きすることを防ぎます。

### 11.4 実装例

```yaml
name: Mirror Knowledge to Wiki

on:
  workflow_dispatch:
  push:
    branches: [develop]
    paths:
      - "docs/agent-knowledge/**"
      - "tools/knowledge/export_wiki.py"

permissions:
  contents: write

concurrency:
  group: mirror-agent-knowledge-wiki
  cancel-in-progress: true

jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: actions/setup-python@v6
        with:
          python-version: "3.13"

      - run: make wiki-export

      - name: Clone Wiki
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          git clone \
            "https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.wiki.git" \
            wiki

      - name: Publish managed pages
        run: |
          cp dist/wiki/*.md wiki/
          git -C wiki config user.name "github-actions[bot]"
          git -C wiki config user.email \
            "41898282+github-actions[bot]@users.noreply.github.com"
          git -C wiki add -A
          git -C wiki diff --cached --quiet && exit 0
          git -C wiki commit -m "mirror knowledge from ${GITHUB_SHA}"
          git -C wiki push origin HEAD:master
```

Wiki は最初の page を GitHub UI で保存した後、`.wiki.git` を clone できます。

### 11.5 Publish failure

Wiki は downstream view であるため、Wiki publish failure が knowledge の正本を壊すことはありません。

推奨動作:

- Repository merge は保持する
- workflow failure を通知する
- manual rerun を可能にする
- Wiki page に stale 表示がある場合は更新されるまで残す
- 次の publish は最新 default branch の内容から再実行する

---

## 12. Agent を利用する場合の Workflow

Agent を導入しても、Source of Truth と review rule は変更しません。

変わるのは、knowledge の探索、graph query、変更案作成、再生成、validation の一部を Agent が実行できる点です。

### 12.1 Agent 未使用時

```text
Human
  ↓ source / knowledge を調査
  ↓ graph を確認
  ↓ code / test / knowledge を変更
  ↓ generator を実行
  ↓ Pull Request
  ↓ review / merge
  ↓ Wiki publish
```

### 12.2 Agent 使用時

```text
Human starts Agent task
        ↓
Agent Session starts
        ↓
sessionStart freshness check
        ↓
CURRENT knowledge または runtime knowledge を選択
        ↓
target symbol の graph slice を query
        ↓
source / generated / curated knowledge を確認
        ↓
code / test / knowledge change を branch に作成
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

### 12.3 Agent の参照先

Agent は次の順序で情報を利用します。

```text
1. 現在 branch の source code
2. 現在 branch 用 runtime knowledge
3. committed generated knowledge
4. curated knowledge
5. Wiki / Issue / PR / Session history
```

Wiki は Agent の primary context ではありません。

### 12.4 Test Generator Agent

Test Generator Agent の責務:

1. knowledge freshness を確認する
2. target symbol の graph slice を query する
3. current source を読む
4. generated knowledge と curated rule を読む
5. test change を作成する
6. source / test change により graph が変わる場合は knowledge を再生成する
7. `make test` と `make check` を実行する
8. Pull Request に provenance を記載する

### 12.5 Knowledge Curator Agent

Knowledge Curator Agent の責務:

1. source change を確認する
2. generator を実行する
3. raw graph と generated views の差分を確認する
4. schema error、secret、不要な大量データを確認する
5. Pull Request を作成する
6. 人の review を受ける

Knowledge Curator Agent も Wiki を直接更新しません。

### 12.6 Agent Session の役割

Agent Session は次の情報を提供します。

- prompt
- response
- command
- tool usage
- read files
- changed files
- validation result
- branch / Pull Request

ただし、Session は knowledge の正本ではありません。

```text
正式な handoff:
commit + branch + Pull Request + Repository knowledge

補助的な provenance:
Agent Session
```

### 12.7 Agent Pull Request の必須記載事項

```markdown
## Knowledge provenance

- Base branch: `develop`
- Source digest: `sha256:...`
- Knowledge status: `CURRENT` / `RUNTIME`
- Generated files used:
  - `docs/agent-knowledge/generated/modules/...`
  - `docs/agent-knowledge/generated/test-impact/...`
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

## 13. Wiki と Agent を組み合わせた利用例

### 13.1 人が Wiki で確認する

1. Wiki の module page を開く
2. responsibility、dependency、test impact を確認する
3. Source commit と status を確認する
4. 問題があれば Issue または source file の Pull Request を作成する

### 13.2 Agent が修正する

1. Issue を Agent に assign、または Agents tab から task を開始する
2. Agent が Repository 内の knowledge を読む
3. Agent が graph slice を取得する
4. Agent が branch 上で修正する
5. Agent が knowledge を再生成する
6. Pull Request を作成する

### 13.3 人が review する

1. source diff を確認する
2. generated knowledge diff を確認する
3. Agent Session で実行履歴を確認する
4. CI 結果を確認する
5. merge する

### 13.4 Wiki が更新される

1. default branch merge を trigger に workflow が起動する
2. Repository knowledge を Wiki 用 Markdown に export する
3. Wiki を更新する
4. 利用者が新しい内容を確認する

---

## 14. Repository サイズと外部 DB の判断

Code graph が小規模または中規模であれば、compressed artifact を Repository に commit できます。

ただし、GitHub は 100 MiB を超える単一 file を通常の Git Repository に push できません。また、Repository は小さく保つことが推奨されています。

そのため、次の2段階で設計します。

### 14.1 Repository-contained mode

対象:

- graph artifact が小さい
- update frequency が低い
- clone performance に問題がない

保存:

```text
Repository
├── raw graph
├── generated views
├── manifest
└── query tool
```

### 14.2 External graph storage mode

対象:

- graph が大規模
- update frequency が高い
- 複数 Repository を横断する
- graph query の性能要件が高い

保存:

```text
Repository
├── manifest
├── compact knowledge views
├── graph snapshot ID / URI
└── query client / Agent Skill

External storage / GraphDB
└── complete graph
```

この場合も、どの graph snapshot がどの source digest に対応するかを Repository manifest に記録します。

Wiki は compact views のみを表示し、raw graph 全量は表示しません。

---

## 15. 権限と Governance

### 15.1 推奨 role

| Role | 責務 |
|---|---|
| Knowledge owner | Curated knowledge の承認 |
| Generator owner | Generator、schema、query tool の保守 |
| Developer / Agent | branch 上で source、test、knowledge change を作成 |
| Reviewer | source と knowledge diff を確認 |
| Wiki publisher | GitHub Actions bot |

### 15.2 CODEOWNERS 例

```text
/docs/agent-knowledge/curated/      @project-knowledge-owners
/tools/knowledge/                   @platform-team
/.github/workflows/mirror-wiki.yml  @platform-team
/.github/agents/                    @ai-agent-owners
```

### 15.3 Security rule

Knowledge に次を含めてはいけません。

- secret
- credential
- production customer data
- unrestricted production log
- personal information
- license 上共有できない third-party content

Generator の input path は allowlist 方式で管理します。

---

## 16. Failure と Recovery

| Failure | 対応 |
|---|---|
| Source と manifest が不一致 | knowledge を再生成。merge 前なら CI failure |
| Generated file が欠落 | generator から再生成 |
| Raw graph が破損 | source から再生成 |
| Generated conflict | rebase 後に再生成 |
| Curated conflict | 人が内容を確認して merge |
| Wiki clone failure | 初期 page、権限、Repository 名を確認 |
| Wiki push failure | workflow rerun。Repository knowledge は保持 |
| 古い workflow が後から完了 | concurrency で cancel |
| Agent が古い knowledge を検出 | runtime knowledge を生成、または task を停止して baseline 更新 |

---

## 17. 現在の Demo Repository への適用

現在の Repository は、本設計の基本要素をすでに実装しています。

| 設計要素 | 現在の実装 |
|---|---|
| Raw graph | `artifacts/codegraph/` |
| Generated view | `docs/agent-knowledge/generated/` |
| Curated knowledge | `docs/agent-knowledge/curated/` |
| Manifest | `docs/agent-knowledge/generated/manifest.json` |
| Generator / validator | `tools/knowledge/` |
| Freshness CI | `.github/workflows/ci.yml` |
| Branch runtime knowledge | `.agent-runtime/` |
| Custom Agent | `.github/agents/` |
| Agent Skill | `.github/skills/test-knowledge/` |
| Session hook | `.github/hooks/knowledge-freshness.json` |
| Wiki mirror | `.github/workflows/mirror-wiki.yml` |

### 17.1 次に追加すべき項目

1. Wiki page に source commit / source digest / status を表示する
2. Wiki page から source file と Issue 作成画面への link を追加する
3. `CODEOWNERS` を設定する
4. CI を default branch の required check に設定する
5. generated artifact の手動編集禁止を review rule にする
6. large graph に移行する条件を定義する
7. Wiki publish failure の通知先を定義する

---

## 18. 完了条件

本設計が成立したと判断する条件は次のとおりです。

1. Shared knowledge の正本が Repository 内に存在する
2. source change と knowledge change を Pull Request で review できる
3. source と knowledge の不一致を CI が検出できる
4. generated conflict を再生成で解決できる
5. Wiki が default branch の knowledge を表示する
6. Wiki page から source version を確認できる
7. Wiki の feedback が Issue / Pull Request に戻る
8. Agent が current branch の knowledge freshness を確認できる
9. Agent が必要な graph slice のみを取得できる
10. Agent change が branch / Pull Request / CI を経由する
11. Agent Session と Repository knowledge の役割が分離されている
12. large graph を外部 storage に移す判断基準がある

---

## 19. 最終方針

```text
Repository
= Knowledge の Source of Truth
= Git commit / PR による conflict・変更管理

Wiki
= 人向けの可視化・確認画面
= Repository からの一方向 mirror

Agent
= Repository knowledge の利用者・変更提案者
= branch / PR / CI を経由して更新

Agent Session
= 実行履歴と監査証跡
= Knowledge database ではない
```

本設計により、Knowledge の共有、更新、conflict resolution、ユーザー確認、Agent 利用を、GitHub の既存 workflow の中で一貫して管理できます。

---

## 20. 参考資料

- [Adding or editing wiki pages - GitHub Docs](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages)
- [Control the concurrency of workflows and jobs - GitHub Docs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
- [Using Copilot cloud agent on GitHub - GitHub Docs](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-on-github)
- [Managing agent sessions - GitHub Docs](https://docs.github.com/en/enterprise-cloud@latest/copilot/how-tos/copilot-on-github/use-copilot-agents/manage-and-track-agents)
- [Creating custom agents for Copilot cloud agent - GitHub Docs](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/create-custom-agents)
- [About large files on GitHub - GitHub Docs](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)
