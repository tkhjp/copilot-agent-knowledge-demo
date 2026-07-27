# 現フェーズの調査スコープ整理

**更新日:** 2026-07-27  
**ステータス:** 顧客フィードバック反映版

## Executive Summary

現フェーズで求められているのは、完成されたナレッジ蓄積・管理機能ではありません。

主な検討対象は、code graph や test data を保存し、複数の利用者・実行環境・Agent から共有利用できる**データ基盤の土台部分**です。

まず各候補を単体で確認し、それぞれの「できること・できないこと」を明確にします。その後、graph data と test data を Agent が参照する最小の組み合わせ例を提示します。

共有場所におけるナレッジの自動更新、長期蓄積、鮮度管理、Wiki 連携、Session 活用などは、後続フェーズの検討対象とします。

```text
今回の主対象

code graph / test data
        ↓
共有可能な保存基盤
        ↓
複数環境から読み書き・参照
        ↓
最小の Agent 利用例
```

---

## 1. 顧客フィードバックの要旨

### 1.1 現時点で欲しいもの

現時点で優先されているのは、完成されたナレッジ蓄積機能ではなく、次のような共有データ基盤です。

- graphDB や testDB のデータを保存できる
- 複数の環境から共有利用できる
- mount または接続によって利用できる
- Session 終了後もデータが保持される
- Agent や開発ツールが必要なデータを参照できる

ナレッジを共有場所でどのように更新し、どのように長期蓄積するかは、現時点の主課題ではありません。

### 1.2 調査結果の見せ方

複数の技術を最初から組み合わせると、各構成要素の能力と制約が見えにくくなります。

そのため、次の順序で確認します。

1. 各候補を単体で確認する
2. 各候補の「できること・できないこと」を整理する
3. graph data と test data の保存・参照を個別に実証する
4. 最後に、Agent が両方を利用する最小サンプルを示す

---

## 2. 現フェーズで答えるべき問い

本調査では、主に次の問いに答えます。

1. code graph と test data をどこに保存するか
2. ローカル環境、CI、VS Code、GitHub Copilot Agent からどのようにアクセスするか
3. mount 型と connection/API 型のどちらが適しているか
4. 複数利用者・複数 Agent による読み取りや書き込みが可能か
5. データは Session や実行環境をまたいで保持されるか
6. 権限、監査、バックアップ、運用責任をどのように扱うか
7. 各候補の制約と適用範囲は何か

---

## 3. 用語整理

顧客フィードバック中の「マウント可能な共有DB」は、技術的には次の2種類に分けて評価します。

### 3.1 Mount 型共有ストレージ

ファイルシステムとして利用環境に mount し、ファイルとして読み書きします。

例として想定するデータ:

- `nodes.jsonl`
- `edges.jsonl`
- graph snapshot
- test case definition
- test result
- coverage result
- metadata

主な確認点:

- 複数環境から同時に参照できるか
- lock や同時書き込みをどう扱うか
- Agent 実行環境に mount できるか
- ファイル数やサイズが増えた場合の性能

### 3.2 Connection / API 型データベース

DB protocol、SQL、Graph query language、SDK、REST API などを通じて接続します。

主な確認点:

- Agent 実行環境から network connection が可能か
- authentication と authorization をどう扱うか
- query 単位で必要なデータだけ取得できるか
- schema、index、concurrent update を管理できるか

Mount 型と Connection 型は排他的ではありません。用途に応じて、raw artifact は共有ストレージ、検索用データは DB に置く構成も候補になります。

---

## 4. 現フェーズのスコープ

### 4.1 In Scope

| 対象 | 確認内容 |
|---|---|
| 共有データ基盤候補 | 保存方式、アクセス方式、永続性、権限、運用負荷 |
| Graph data | node、edge、symbol、dependency、test impact の保存と検索 |
| Test data | test case、test result、coverage、評価 metadata の保存と検索 |
| 単体 PoC | 各保存方式を単独で読み書きできることの確認 |
| 複数環境共有 | ある環境で書き込み、別環境で読み取れることの確認 |
| Agent 利用 | Agent が必要な graph/test data を限定的に取得できることの確認 |
| 制約整理 | できること、できないこと、前提条件、セキュリティ制約 |
| 最小組み合わせ例 | graph data と test data を読み、テスト生成または評価に利用する例 |

### 4.2 Out of Scope

以下は有用ですが、現フェーズの主対象にはしません。

- 完成されたナレッジ管理システム
- ナレッジの自動抽出・自動要約
- 長期的な更新・蓄積ポリシー
- branch-aware な知識鮮度管理の完成形
- Wiki の自動同期を中心とした運用
- Agent Session を利用した監査・共有の完成形
- Copilot Memory の活用設計
- 自動 PR 作成を含む運用フロー全体
- 組織全体の knowledge governance
- 本番運用向け HA、DR、容量設計の詳細

これらは、共有データ基盤の成立を確認した後のフェーズで扱います。

---

## 5. 調査・デモの進め方

### Step 1: 候補を単体で評価する

各候補について、同じ観点で比較します。

```text
候補A
- 保存できるデータ
- アクセス方法
- 読み取り・書き込み
- 永続性
- 権限
- Agent からの利用方法
- できること
- できないこと

候補B
- 同じ観点で評価
```

最初から大きな統合アーキテクチャにはしません。

### Step 2: Graph data の単体 PoC

```text
source code
    ↓
code graph generator
    ↓
shared storage / graph database
    ↓
another environment reads a graph slice
```

確認事項:

- node / edge を保存できる
- 指定 symbol の近傍を取得できる
- 別環境から同じデータを参照できる
- Session 終了後も保持される

### Step 3: Test data の単体 PoC

```text
test execution / evaluation
    ↓
test data writer
    ↓
shared test data store
    ↓
another environment queries the result
```

確認事項:

- test case、実行結果、coverage、評価値を保存できる
- repository、commit、branch、test ID で検索できる
- 別環境から同じデータを参照できる
- 更新履歴または最新状態を識別できる

### Step 4: 最小の組み合わせサンプル

```text
Agent
├── target symbol の graph data を取得
├── 関連する test data を取得
└── テスト生成またはテスト評価に利用
```

このサンプルでは、完全な knowledge lifecycle は実装しません。

目的は、共有データ基盤を組み合わせることで、Agent がどのような利用をできるかを具体的に見せることです。

---

## 6. 候補比較の評価軸

| 評価軸 | 確認内容 |
|---|---|
| 保存対象 | graph、test case、test result、coverage、metadata |
| データ粒度 | ファイル、record、node/edge、test execution 単位 |
| アクセス方式 | mount、SQL、Graph query、SDK、REST API |
| 利用環境 | local、VS Code、CI、GitHub-hosted Agent、self-hosted Agent |
| 読み取り | 全件、部分取得、symbol 単位、repository/commit 単位 |
| 書き込み | 単一 writer、複数 writer、transaction、lock |
| 永続性 | Session 終了後の保持、version、snapshot、backup |
| 鮮度識別 | source commit、generated time、schema version の保持 |
| 権限管理 | user、team、repository、organization、service identity |
| 監査 | 誰が、いつ、何を更新したか |
| 性能 | データ量、検索速度、更新頻度、同時利用数 |
| 運用負荷 | server 管理、schema 管理、backup、障害対応 |
| Agent 適合性 | 必要な小さい data slice を取得できるか |
| 制約 | network、mount 可否、secret 管理、vendor lock-in |

---

## 7. 現在の Repository の位置付け

`copilot-agent-knowledge-demo` は、共有データ基盤そのものを比較するための完成版ではありません。

現在の実装は、複数の要素を組み合わせた場合の**将来利用イメージを示す統合参考デモ**として扱います。

```text
現在の Repository

code graph
+ Agent Knowledge Pack
+ Custom Agent
+ Skill / Hook
+ Agent Session
+ Wiki mirror

= 組み合わせた場合の利用イメージ
```

現フェーズでは、次のように再整理します。

| Repository 内の要素 | 現フェーズでの扱い |
|---|---|
| code graph generator | 単体 PoC の入力として利用 |
| graph artifact | 共有保存対象のサンプルとして利用 |
| test code / result | test data のサンプルとして利用 |
| Custom Agent / Skill | 最小組み合わせ例で利用 |
| Agent Session | 参考的な実行履歴として利用 |
| Wiki mirror | 後続の knowledge sharing 例として扱う |
| freshness / knowledge lifecycle | 後続フェーズの検討対象 |

この Repository は最終アーキテクチャの決定案ではなく、構成要素を組み合わせた際の挙動を確認する reference implementation です。

---

## 8. 想定成果物

### 8.1 候補比較表

各候補について、次を一覧化します。

- 概要
- 保存対象
- アクセス方式
- 利用可能な環境
- 読み取り・書き込み能力
- 永続性
- 権限
- 運用負荷
- できること
- できないこと
- 適用判断

### 8.2 Graph data 単体デモ

- graph を共有場所に保存
- 別環境から target symbol の graph slice を取得
- 保存前後のデータ同一性を確認

### 8.3 Test data 単体デモ

- test metadata と result を共有場所に保存
- repository / commit / test ID で検索
- 別環境から取得

### 8.4 最小統合デモ

- Agent が graph data と test data を取得
- 取得した情報をテスト生成または評価に利用
- 使用したデータと制約を明示

### 8.5 判断メモ

- 推奨候補
- 採用条件
- 未解決事項
- 後続フェーズへの持ち越し事項

---

## 9. 現フェーズの完了条件

次を満たした時点で、現フェーズの検証は完了とします。

1. graph data と test data の保存候補が比較されている
2. 各候補の「できること・できないこと」が明文化されている
3. ある環境で書き込んだデータを別環境から読み取れる
4. データが Session 終了後も保持される
5. 権限を持たない利用者または環境からのアクセスを制限できる
6. Agent が全データではなく、必要な data slice を取得できる
7. graph data と test data を組み合わせた最小利用例がある
8. 完成された knowledge management は後続課題として分離されている

---

## 10. 後続フェーズの検討項目

共有データ基盤の成立後に、次を検討します。

- ナレッジの更新責任と承認フロー
- 自動更新と手動更新の境界
- source commit と knowledge version の対応
- branch / PR 単位の鮮度管理
- historical snapshot と latest view
- Wiki、Copilot、Agent Session への提供方法
- retention、backup、削除ポリシー
- organization-wide governance
- quality evaluation と feedback loop

---

## 11. 一文での説明

> 現時点では完成されたナレッジ蓄積機能を作るのではなく、graphDB や testDB のデータを保存し、複数の環境から共有利用できるデータ基盤を確認します。まず各構成要素を単体で評価して「できること・できないこと」を明確にし、その後、Agent が graph data と test data を利用する最小サンプルを提示します。ナレッジの自動更新・長期蓄積・運用設計は後続フェーズで検討します。
