# Tree-sitter 構造 Code Graph の更新・同期設計

**対象:** Tree-sitter から抽出する `functions / classes / imports / calls / inheritance` を中心とした構造 Code Graph  
**生成方式:** LLM を使用しない決定的な generator を Agent Skill から呼び出す  
**想定読者:** ソフトウェア設計・CI/CD・Git 運用に習熟したエンジニア  
**位置付け:** 初期導入向けの更新・共有・同期方式  
**更新日:** 2026-07-27

---

## 1. 前提と結論

本プロジェクトの初期 Code Graph は、Understand Anything の非 LLM 部分を参考にしつつ、Tree-sitter と言語別 resolver から構造的事実だけを生成します。

```text
Tree-sitter
    ↓
構文木
    ↓
構造抽出・名前解決
    ↓
files / modules / functions / classes
imports / calls / inherits
```

初期段階では、次を Code Graph に含めません。

- LLM が生成する summary、tag、architecture layer
- business domain の意味付け
- 自然言語による責務説明
- 実行時 coverage
- test result、mutation result
- 人が記述した設計判断

生成処理の入口は Agent Skill ですが、graph generator 自体は Agent の判断に依存しない独立 command として実装します。

```text
Agent Skill
    = generator の起動、対象 commit の確認、結果の利用

generator
    = Tree-sitter を使った決定的な構造抽出
```

この前提では、Code Graph は人が編集する knowledge ではなく、source code から再生成できる派生物です。

したがって正本は次です。

```text
正本
├── source code
├── graph generator
├── Tree-sitter grammar version
├── generator configuration
└── graph schema version

派生物
└── Code Graph snapshot
```

### 1.1 推奨方式

初期段階では、次の方式を推奨します。

```text
Feature branch / Agent workspace
    └── branch-local graph を一時生成
        └── shared graph には書き込まない

Pull Request
    └── PR head の exact commit から graph を生成・検証
        └── CI artifact と graph diff summary を残す

Default branch merge 後
    └── 単一 writer の GitHub Actions が graph を再生成
        └── exact source commit に紐づく shared snapshot を公開

GitHub Wiki
    └── graph の概要、状態、source commit、利用方法だけを表示
```

重要な原則は次です。

1. Code Graph file を複数 branch で共同編集しない
2. Generated graph の競合を手動 merge しない
3. Shared graph は default branch に対して単一 writer が公開する
4. Agent は現在 branch と一致する graph だけを使用する
5. 同一入力から同一 graph digest が得られることを CI で検証する
6. 初期実装は full rebuild を基本とし、性能上必要になってから増分更新を追加する

---

## 2. Tree-sitter を使う際の技術的な境界

Tree-sitter が直接提供するのは構文木です。`function`、`class`、`import` などの構文要素は抽出できますが、言語全体の意味解析を自動的に完了するわけではありません。

特に次は、Tree-sitter 以外の resolver が必要です。

- import path の解決
- namespace / package / module の解決
- overload の解決
- dynamic dispatch の解決
- method call の receiver type 推定
- inheritance の cross-file 解決
- alias、re-export、barrel file の解決

そのため edge には、解決方法を記録します。

```json
{
  "source": "symbol:python:src/service.py:PaymentService.authorize",
  "target": "symbol:python:src/gateway.py:PaymentGateway.request",
  "type": "calls",
  "resolution": "import-resolved",
  "confidence": 1.0
}
```

推奨する `resolution` の例:

| 値 | 意味 |
|---|---|
| `exact-local` | 同一 file 内で一意に解決 |
| `import-resolved` | import / export table から解決 |
| `inheritance-resolved` | class hierarchy から解決 |
| `heuristic` | 名前や path の規則から推定 |
| `unresolved` | target を一意に決定できない |

初期段階では、無理に edge を確定させるより `unresolved` を残す方が安全です。Agent は推定 edge を事実として扱ってはいけません。

---

## 3. Graph Snapshot の識別

### 3.1 Source commit だけでは不十分

同じ source commit でも、次が変わると graph は変化します。

- generator version
- Tree-sitter runtime version
- language grammar version
- graph schema version
- 対象 file / ignore 設定
- resolver 設定

したがって、snapshot は次の入力集合で識別します。

```text
repository identity
+ source commit または source digest
+ generator version
+ grammar lock digest
+ configuration digest
+ schema version
```

### 3.2 Snapshot ID

推奨:

```text
snapshot_id = sha256(
    repository_id
    + source_commit
    + source_digest
    + generator_version
    + grammar_lock_digest
    + configuration_digest
    + schema_version
)
```

同一 `snapshot_id` に対して異なる graph digest が生成された場合は、決定性違反として CI を失敗させます。

### 3.3 Manifest

Shared graph には machine-readable manifest を必須とします。

```json
{
  "schemaVersion": 1,
  "generatorVersion": "0.1.0",
  "treeSitterVersion": "0.25.x",
  "grammars": {
    "python": "sha256:...",
    "typescript": "sha256:..."
  },
  "configurationDigest": "sha256:...",
  "sourceCommit": "abcdef1234567890",
  "sourceDigest": "sha256:...",
  "snapshotId": "sha256:...",
  "generationMode": "full",
  "generatedAt": "2026-07-27T00:00:00Z",
  "files": {
    "src/service.py": {
      "contentDigest": "sha256:...",
      "structureDigest": "sha256:..."
    }
  },
  "graph": {
    "nodeCount": 1200,
    "edgeCount": 3600,
    "nodeDigest": "sha256:...",
    "edgeDigest": "sha256:..."
  },
  "status": "READY"
}
```

`generatedAt` は監査情報であり、graph identity の計算には含めません。

---

## 4. Graph の状態モデル

| 状態 | 条件 | 利用可否 |
|---|---|---:|
| `ABSENT` | 対象 source に対応する snapshot がない | 不可。生成する |
| `GENERATING` | staging area で生成中 | 不可 |
| `READY` | schema、hash、参照整合性の検証済み | 利用可 |
| `STALE` | graph の source identity が現在 source と不一致 | 原則不可。参考利用時は明示 |
| `BROKEN` | parse error policy 違反、重複 ID、dangling edge、digest 不一致 | 不可 |
| `FAILED` | 生成処理が失敗 | 不可。直前の READY snapshot を保持 |

Agent は `READY` かつ現在の source identity と一致する snapshot のみを通常利用します。

例外として、read-only の調査で直近 ancestor snapshot を使う場合は、回答に `STALE` と差分 commit を明記します。test generation や code change では、この fallback を使用しません。

---

## 5. 出力形式と決定性

### 5.1 推奨ディレクトリ

```text
artifacts/codegraph/
├── manifest.json
├── nodes.jsonl.gz
├── edges.jsonl.gz
└── file-index.json
```

1つの巨大な JSON でも実装できますが、次の理由から node / edge を JSON Lines に分ける方が扱いやすくなります。

- stream processing が可能
- node と edge を個別に hash 化できる
- 大規模化時に分割しやすい
- query tool が全体を memory に展開せず読める

### 5.2 Stable ID

line number を ID に含めません。行追加だけで全 ID が変化するためです。

推奨例:

```text
file:<repository-relative-path>

symbol:<language>:<repository-relative-path>:<kind>:<qualified-name>:<signature>
```

例:

```text
symbol:python:src/payment/service.py:method:PaymentService.authorize:(Order,str)->Payment
```

Edge の一意性:

```text
edge_id = sha256(
    edge_type
    + source_symbol_id
    + target_symbol_id
    + callsite_file
    + callsite_start_byte
)
```

### 5.3 Canonicalization

同一入力から同一出力を得るため、次を固定します。

- UTF-8
- LF 改行
- JSON key の順序
- node は `id` で sort
- edge は `type + source + target + location` で sort
- tag や collection の順序
- gzip の timestamp を固定
- 絶対 path を保存しない
- OS 固有 path separator を `/` に統一
- `generatedAt` を graph digest から除外

### 5.4 Validation

公開前に最低限、次を検証します。

- schema validation
- node ID の一意性
- edge ID の一意性
- dangling edge がない
- source / target node が存在する
- file path が Repository 外を参照していない
- unsupported language の扱いが明示されている
- parse error 数が policy 内
- node / edge digest が manifest と一致
- 同一 snapshot ID が既に存在する場合、graph digest が一致

---

## 6. 更新方式

更新は、Tree-sitter 自体の増分 parse と、Repository 全体の graph 増分更新を分けて考えます。

### 6.1 Tree-sitter の増分 parse

Tree-sitter は、同一 document の以前の syntax tree を保持し、編集位置を `Tree.edit` で反映した後、その tree を次回 parse に渡すことで変更部分を効率的に再解析できます。

この方式は次に適しています。

- IDE plugin
- long-running daemon
- 同一 process が以前の syntax tree を保持する環境

一方、GitHub Actions や一時的な Agent workspace は通常、以前の syntax tree を memory 上に保持していません。そのため、CI の更新設計では Tree-sitter の parse-level incremental だけに依存しません。

### 6.2 Repository 単位の増分更新

Repository の graph 更新では、Git diff と per-file fingerprint を使用します。

```text
base source identity
        ↓
git diff --name-status
        ↓
A / M / D / R を分類
        ↓
変更 file を再 parse
        ↓
影響範囲を再 link
        ↓
全体 validation
```

### 6.3 初期段階の推奨: Full Rebuild

初期実装では、default branch の shared graph は full rebuild を基本とします。

理由:

- LLM cost がない
- incremental merge logic の不具合を避けられる
- rename / delete / cross-file resolution を安全に反映できる
- 同一入力の決定性を検証しやすい
- graph generator 自体の正しさを先に確立できる

増分更新は、full rebuild の実測時間が許容範囲を超えてから導入します。

### 6.4 増分更新を導入する場合の処理

#### Step 1: Changed file の取得

```text
A: 追加
M: 変更
D: 削除
R: rename
```

#### Step 2: 構造 fingerprint の比較

各 file に次を保存します。

```text
content digest
exported symbol digest
import set digest
class / function signature digest
inheritance declaration digest
callsite digest
```

変更内容を次に分類します。

| 分類 | 例 | graph 更新 |
|---|---|---|
| `NO_CHANGE` | content hash も同じ | 不要 |
| `NON_STRUCTURAL` | comment、format のみ | 原則不要 |
| `LOCAL_STRUCTURAL` | function 内 call の追加 | 対象 file を更新 |
| `PUBLIC_STRUCTURAL` | export、signature、class name の変更 | 対象 file + reverse dependency を更新 |
| `GLOBAL_INVALIDATION` | grammar、schema、resolver、ignore 設定の変更 | full rebuild |

#### Step 3: 影響範囲の計算

```text
Affected Files
    = changed files
    + reverse importers of changed exports
    + subclasses of changed base classes
    + files containing calls to renamed / removed symbols
```

初期の安全な実装としては、changed file だけを再 parse した後、全 file の compact symbol table を使って global link phase を再実行する方法を推奨します。

```text
parse cost
    = changed files のみ

link cost
    = Repository 全体の compact index
```

これにより、古い cross-file edge が残るリスクを下げられます。

#### Step 4: 古い情報の除去

各 node は `ownerFile` を持ちます。

変更または削除 file について:

1. `ownerFile` が一致する旧 node を削除
2. 削除 node を参照する edge を削除
3. 新しい node を追加
4. import / call / inheritance edge を再解決

#### Step 5: Full Rebuild への切替条件

次の場合は incremental update を中止し、full rebuild します。

- generator version が変化
- Tree-sitter grammar version が変化
- graph schema version が変化
- resolver / ignore 設定が変化
- rename / move が module boundary をまたぐ
- parse error が増加
- affected files が閾値を超える
- dangling edge が解消できない
- incremental result と periodic full rebuild の digest が不一致

---

## 7. 「更新」と「同期」を分ける

本設計では、次の3つを別の処理として扱います。

| 処理 | 意味 |
|---|---|
| 更新 | source change から graph を再生成する |
| 公開 | 検証済み graph snapshot を shared storage に登録する |
| 同期 | 利用者・Agent・Wiki が正しい snapshot を取得・反映する |

この区別がないと、Agent が graph を生成しただけで shared graph を更新したと誤認したり、古い publish job が最新 graph を上書きしたりします。

---

## 8. Branch / Agent Workspace の同期

### 8.1 Branch-local Graph

Feature branch と Agent workspace では、現在の source state に対する graph を local に生成します。

```text
.agent-runtime/codegraph/<source-digest>/
```

または:

```text
.worktrees/<worktree-id>/.codegraph/
```

規則:

- Git 管理外にする
- workspace ごとに出力先を分離する
- 同一 directory を複数 Agent が共有しない
- lock file を workspace 単位に置く
- shared latest pointer を更新しない
- exact commit snapshot が既に存在する場合は再利用してよい

### 8.2 Agent Skill の責務

Agent Skill は次の interface を持たせます。

```text
ensure_graph
    現在の source identity を計算
    exact snapshot の有無を確認
    なければ branch-local graph を生成

query_graph
    symbol / edge type / direction / depth / limit を指定して取得

validate_graph
    manifest、schema、digest、参照整合性を確認

publish_graph
    shared publication 用
    Agent からは直接呼ばせず、中央 CI のみ許可
```

Agent は raw graph 全量を prompt に読み込まず、query tool で必要範囲だけを取得します。

### 8.3 Agent が記録する追跡情報

```markdown
## Code Graph provenance

- Source commit: `abcdef1`
- Source digest: `sha256:...`
- Snapshot ID: `sha256:...`
- Generator version: `0.1.0`
- Grammar digest: `sha256:...`
- Graph source: `shared-exact` / `branch-local-generated`
- Query:
  - symbol: `PaymentService.authorize`
  - edge types: `calls, imports`
  - depth: `2`
```

---

## 9. Pull Request の更新・同期

PR では、graph file を feature branch で共同編集する方式を避けます。

### 9.1 推奨 PR Workflow

```text
PR head commit
    ↓
exact SHA を checkout
    ↓
Code Graph を staging directory に full generate
    ↓
schema / digest / referential integrity を検証
    ↓
base graph との差分 summary を生成
    ↓
Actions Artifact と PR summary に保存
    ↓
required check
```

PR で確認する内容:

- graph 生成に成功したか
- parse error が増えていないか
- node / edge の増減
- public symbol の追加・削除
- import / inheritance の大きな変化
- graph schema が壊れていないか

Raw graph は Actions Artifact に置けますが、Artifact は保存期間を持つ一時成果物です。永続的な shared store としては扱いません。

### 9.2 PR branch に graph を commit しない理由

- 2つの PR が同時に graph を更新すると大きな conflict が発生する
- source diff より generated diff が大きくなりやすい
- merge 順により graph の再生成が必要になる
- reviewer が generated JSON を手作業で評価しにくい

代わりに、PR では graph の検証結果と要約差分を review し、shared graph は merge 後に中央 workflow が公開します。

---

## 10. Default Branch の Shared Graph 公開

### 10.1 Single Writer

Shared graph の更新者は、default branch 用 GitHub Actions workflow 1つに限定します。

```text
Human / Agent
    → shared graph に直接 write しない

GitHub Actions publisher
    → shared graph の唯一の writer
```

### 10.2 Publish Workflow

```text
1. default branch の source commit C を exact checkout
2. staging directory に graph を生成
3. manifest と graph を検証
4. snapshot ID / graph digest を計算
5. immutable snapshot として保存
6. default branch HEAD がまだ C か確認
7. C のままなら latest pointer を C の snapshot に更新
8. C より先に進んでいれば snapshot は保持するが latest は更新しない
```

### 10.3 なぜ head check が必要か

GitHub Actions の `concurrency` と `cancel-in-progress` は古い run を減らせますが、workflow の完了順序そのものは保証されません。

例:

```text
commit C1 → workflow W1 開始
commit C2 → workflow W2 開始

W2 完了
W1 が遅れて完了
```

W1 が無条件に `latest` を更新すると、C2 の graph が C1 に巻き戻ります。

そのため publish 前に必ず確認します。

```bash
git fetch origin develop
CURRENT_HEAD="$(git rev-parse origin/develop)"

if [ "$CURRENT_HEAD" != "$SOURCE_SHA" ]; then
  echo "A newer commit exists; keep snapshot but do not move latest pointer."
  exit 0
fi
```

### 10.4 冪等性

同じ `snapshot_id` が既に存在する場合:

| 条件 | 動作 |
|---|---|
| graph digest が同じ | no-op |
| graph digest が異なる | 決定性違反として失敗 |

### 10.5 Publication の原子性

Shared location へ直接書きながら生成しません。

```text
staging/
    ↓ generate
    ↓ validate
    ↓ digest
    ↓ publish atomically
shared/READY snapshot
```

生成に失敗した場合、直前の READY snapshot と latest pointer を変更しません。

---

## 11. Shared Graph の保存方式

### 11.1 初期推奨: Repository 内に latest snapshot を保存

Graph が小規模・中規模であれば、次を default branch に保存できます。

```text
artifacts/codegraph/
├── manifest.json
├── nodes.jsonl.gz
├── edges.jsonl.gz
└── file-index.json
```

ただし更新は中央 publisher のみが行います。

Source merge commit を `C`、graph publication commit を `G` とすると:

```text
C: source / test change
G: graph snapshot for source commit C
```

`manifest.sourceCommit` は `C` を指します。

Graph directory 自体は generator の source input から除外し、graph-only commit `G` によって graph が再び stale になる循環を防ぎます。

Graph publish workflow は source path の変更だけを trigger にし、graph-only commit では再起動しないようにします。

### 11.2 PR 用: Actions Artifact

用途:

- PR head graph
- graph diff report
- debug output
- validation log

制約:

- retention period がある
- permanent pointer には向かない
- Repository context から直接参照しにくい

### 11.3 大規模化後: Object Storage / GraphDB

次の場合は complete graph を外部化します。

- Repository history が肥大化
- graph update frequency が高い
- cross-repository query が必要
- traversal / aggregate query が必要
- Agent が低 latency で subgraph を取得する必要がある

Repository には次を残します。

```text
manifest
source commit / digest
snapshot ID
schema version
generator / grammar version
external URI
query client / Agent Skill
```

---

## 12. 利用者側の同期規則

Consumer は branch name ではなく、source identity で graph を選択します。

```text
Input:
    repository
    source commit または source digest
    generator / schema version

Lookup:
    exact READY snapshot
```

### 12.1 Agent / Tool の選択順

```text
1. current source identity と一致する shared READY snapshot
2. current workspace で生成した branch-local READY snapshot
3. exact snapshot が生成できない場合は処理を停止
```

Default branch の `latest` graph を feature branch に黙って流用しません。

### 12.2 Nearest Ancestor の利用

次の read-only 用途に限り、nearest ancestor snapshot を参考利用できます。

- architecture overview
- change impact の初期候補
- user navigation

その場合は必ず次を表示します。

```text
Graph status: STALE
Graph source commit: C1
Current source commit: C2
Changed files since graph: ...
```

Test generation、code modification、CI gate では利用しません。

---

## 13. 競合と Race Condition

| 状況 | 問題 | 対応 |
|---|---|---|
| 2つの PR が同じ file を変更 | branch graph が異なる | 各 branch-local graph を独立生成。merge 後に shared graph を再生成 |
| 2つの Agent が同時実行 | 同一 local file の上書き | workspace / worktree ごとに出力先を分離 |
| 古い publish job が後で完了 | latest pointer の巻戻り | concurrency + publish 前の HEAD check |
| Generator version が変更 | 同じ source でも graph が変化 | snapshot ID に generator / grammar version を含め full rebuild |
| File rename / delete | orphan node / edge | old ownerFile の node / edge を削除して再 link |
| Generated graph が Git conflict | 手動解決で不整合 | target branch を取り込み graph を再生成 |
| Publish 中に失敗 | partial graph が見える | staging 生成、検証後に原子的 publish |
| 同じ input で異なる digest | generator が非決定的 | CI fail。shared latest を更新しない |

### 13.1 複数 Agent の標準フロー

```text
Agent A worktree
    └── local graph A
    └── PR A

Agent B worktree
    └── local graph B
    └── PR B

PR A merge
    └── central publisher → shared graph C1

PR B rebase latest develop
    └── local graph B2 を再生成
    └── validation
    └── merge
    └── central publisher → shared graph C2
```

---

## 14. Wiki との同期

Wiki には raw graph 全量を同期しません。

公開対象:

- current source commit
- graph snapshot ID
- generator / grammar version
- node / edge count
- parse coverage / error count
- 主要 module / dependency の概要
- graph query tool / dashboard の利用方法
- feedback Issue への link

### 14.1 Wiki page metadata

```markdown
> **Graph 状態:** READY
> **Source commit:** `abcdef1`
> **Snapshot ID:** `sha256:...`
> **Generator version:** `0.1.0`
> **Grammar digest:** `sha256:...`
> **Graph digest:** `sha256:...`
> **更新方法:** Wiki を直接編集せず、source / generator の Pull Request を作成してください。
```

### 14.2 Publish 条件

Wiki publish は shared graph が `READY` になった後に実行します。

```text
source merge
    ↓
shared graph publish READY
    ↓
Wiki summary publish
```

Graph publish が失敗した場合は、前回 Wiki page を保持し、最新 source に対して graph が未更新であることを status page または workflow failure で通知します。

Wiki は結果整合です。Repository / manifest が正本であり、Wiki の反映遅延は正本の破損を意味しません。

---

## 15. CI Gate

### 15.1 PR Required Check

- generator command が完了
- supported source file の parse coverage が基準以上
- 新規 parse error がない、または policy 内
- schema validation 成功
- duplicate node / edge ID がない
- dangling edge がない
- manifest と graph digest が一致
- graph query smoke test 成功
- graph diff summary が生成される

### 15.2 Default Branch Publish Check

- exact source SHA を使用
- full rebuild 成功
- snapshot ID と input identity が一致
- existing same snapshot の digest と一致
- publication 後に read-back validation 成功
- current default HEAD を確認後 latest pointer 更新

### 15.3 Periodic Determinism Check

定期的に同一 commit を2回 full rebuild し、logical graph digest を比較します。

```text
same input identity
    → same nodes digest
    → same edges digest
```

差分が出た場合は、次を疑います。

- unordered collection
- OS / path 差異
- grammar version の未固定
- timestamp 混入
- hash seed / iteration order
- resolver の環境依存

---

## 16. GitHub Actions 実装例

### 16.1 PR Graph Check

```yaml
name: Code Graph Check

on:
  pull_request:
    paths:
      - "src/**"
      - "tests/**"
      - "tools/codegraph/**"
      - ".github/skills/codegraph/**"

permissions:
  contents: read

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          fetch-depth: 0

      - name: Capture exact PR source SHA
        run: echo "SOURCE_SHA=${{ github.event.pull_request.head.sha }}" >> "$GITHUB_ENV"

      - name: Generate exact PR graph
        run: |
          ./tools/codegraph/generate \
            --source-commit "${SOURCE_SHA}" \
            --mode full \
            --output .agent-runtime/pr-graph

      - name: Validate graph
        run: |
          ./tools/codegraph/validate \
            --graph .agent-runtime/pr-graph

      - name: Create graph diff summary
        run: |
          ./tools/codegraph/diff \
            --base-ref "origin/${{ github.base_ref }}" \
            --current .agent-runtime/pr-graph \
            --output graph-diff.md

      - uses: actions/upload-artifact@v4
        with:
          name: codegraph-${{ github.event.pull_request.head.sha }}
          path: |
            .agent-runtime/pr-graph/
            graph-diff.md
```

### 16.2 Default Branch Publisher

```yaml
name: Publish Shared Code Graph

on:
  push:
    branches: [develop]
    paths:
      - "src/**"
      - "tests/**"
      - "tools/codegraph/**"
      - ".github/skills/codegraph/**"

permissions:
  contents: write

concurrency:
  group: shared-codegraph-publisher
  cancel-in-progress: true

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ github.sha }}
          fetch-depth: 0

      - name: Generate into staging
        run: |
          ./tools/codegraph/generate \
            --source-commit "${GITHUB_SHA}" \
            --mode full \
            --output .agent-runtime/staging-codegraph

      - name: Validate staging graph
        run: |
          ./tools/codegraph/validate \
            --graph .agent-runtime/staging-codegraph

      - name: Verify this is still current HEAD
        id: current
        env:
          SOURCE_SHA: ${{ github.sha }}
        run: |
          git fetch origin develop
          CURRENT_HEAD="$(git rev-parse origin/develop)"
          if [ "$CURRENT_HEAD" = "$SOURCE_SHA" ]; then
            echo "publish=true" >> "$GITHUB_OUTPUT"
          else
            echo "publish=false" >> "$GITHUB_OUTPUT"
            echo "Newer commit exists. Keep the snapshot result, but do not update the shared latest graph."
          fi

      - name: Publish repository snapshot
        if: steps.current.outputs.publish == 'true'
        run: |
          rm -rf artifacts/codegraph
          cp -R .agent-runtime/staging-codegraph artifacts/codegraph
          git config user.name "github-actions[bot]"
          git config user.email \
            "41898282+github-actions[bot]@users.noreply.github.com"
          git add artifacts/codegraph
          git diff --cached --quiet && exit 0
          git commit -m "chore(codegraph): publish for ${GITHUB_SHA}"
          git push
```

この例では output flag により、古い run を失敗扱いにせず publish step だけを停止します。さらに、head check 後に default branch が更新された場合も、通常の `git push` が non-fast-forward で失敗するため、古い graph commit が新しい source commit を上書きしません。

---

## 17. 段階導入

### Phase 1: Correctness First

- full rebuild のみ
- stable ID
- canonical output
- manifest
- branch-local graph
- PR CI validation
- default branch single writer
- Wiki status / summary

### Phase 2: File-level Incremental Update

- per-file fingerprint
- Git diff classification
- changed file re-parse
- global link phase
- full rebuild fallback
- incremental vs full digest comparison

### Phase 3: Scale-out

- immutable external snapshot
- GraphDB / object storage
- exact commit lookup
- MCP query
- retention / garbage collection
- cross-repository graph

初期段階では Phase 1 を完成させ、graph generation time と artifact size の実測後に Phase 2 / 3 を判断します。

---

## 18. 受入条件

初期版は次を満たせば成立とします。

1. 同一 source identity から同一 graph digest を生成できる
2. Graph が対象 source commit と generator / grammar version を記録する
3. Feature branch / Agent workspace が shared graph を直接更新しない
4. PR head で graph generation / validation を実行できる
5. Default branch merge 後、単一 writer が shared graph を公開する
6. 古い workflow が最新 graph を巻き戻さない
7. Generated graph の conflict を手動 merge せず再生成できる
8. Agent が current branch と一致する graph snapshot だけを使用する
9. Wiki が graph の source commit と状態を表示する
10. Publish failure 時に直前の READY graph を保持する
11. Graph が大規模化した場合の外部化条件が定義されている

---

## 19. 最終判断

この Code Graph は LLM 生成 knowledge ではなく、Tree-sitter と resolver から生成する構造的な派生物です。

したがって更新・同期の中心は、内容の共同編集ではなく、次の4点になります。

```text
1. 入力 identity を固定する
2. 決定的に再生成する
3. exact commit に紐づく snapshot として公開する
4. shared publication を単一 writer に限定する
```

初期推奨構成:

```text
Branch / Agent
    = local graph

Pull Request
    = exact SHA で生成・検証、artifact と差分を保存

Default branch
    = central workflow が full rebuild して shared graph を公開

Wiki
    = graph の概要・状態・利用導線を表示
```

この方式であれば、複数の開発者や Agent が同時に作業しても、Code Graph 自体を merge する必要はありません。

---

## 20. 参考資料

- [Tree-sitter: Introduction](https://tree-sitter.github.io/tree-sitter/)
- [Tree-sitter: Advanced Parsing / Editing](https://tree-sitter.github.io/tree-sitter/using-parsers/3-advanced-parsing.html)
- [GitHub Actions: Workflow concurrency](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency)
- [GitHub Actions: Artifact retention](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#configuring-the-retention-period-for-github-actions-artifacts-and-logs-in-your-repository)
