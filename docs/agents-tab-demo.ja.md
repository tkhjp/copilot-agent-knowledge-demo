# GitHub Agents タブ デモ手順

[English version](agents-tab-demo.md)

この手順書では、次の要素を組み合わせて実際の GitHub Copilot cloud agent Session を作成します。

- リポジトリ内の Custom Agent
- Agent Skill
- `sessionStart` freshness hook
- code graph
- Agent Knowledge Pack
- GitHub Agents タブで共有される Session

## 重要: ファイルを置いただけでは Session は作成されない

このリポジトリには次の Agent 定義があります。

```text
.github/agents/
├── test-generator.agent.md
├── knowledge-curator.agent.md
└── test-evaluator.agent.md
```

これらは Agent の定義です。定義を default branch に配置しただけでは Session は開始されません。

```text
Custom Agent 定義を commit
        ↓
Agents の picker で選択可能になる
        ↓
まだ Session はない
        ↓
ユーザーが Agents タブから task を開始
        ↓
Copilot cloud agent Session が作成される
```

GitHub Actions の workflow run、通常の Pull Request、API 経由の commit は Agent Session ではありません。

## 前提条件

- GitHub Copilot cloud agent がアカウントで利用可能であること
- このリポジトリへのアクセス権があること
- GitHub Actions が有効であること
- `.github/agents/` の Custom Agent が Agent picker に表示されること
- default branch が `develop` であること

Copilot cloud agent の環境は次で準備されます。

```text
.github/workflows/copilot-setup-steps.yml
```

Session 開始後、次の hook が active knowledge context を準備します。

```text
.github/hooks/knowledge-freshness.json
```

## Demo 1: 最初の共有 Agent Session を作成する

### 操作

1. GitHub で `tkhjp/copilot-agent-knowledge-demo` を開きます。
2. **Agents** タブを開きます。
3. **New task** または同等の新規タスク操作を選びます。
4. Repository にこのリポジトリを選択します。
5. Base branch に `develop` を選択します。
6. Custom agent に `test-generator` を選択します。
7. 次の prompt を送信します。

```text
PaymentService.authorize で、同じ idempotency key に対して既存の Payment が
保存済みの場合の不足している unit test を追加してください。

編集前に以下を実行してください。

1. test-knowledge skill を使用する。
2. .agent-runtime/active-context.md の active knowledge mode を報告する。
3. PAYMENT_GRAPH_PROBE_7F31 を検索する。
4. PaymentService.authorize を depth 1 で graph query する。
5. 関連する generated module、test-impact、domain rules、testing policy を読む。
6. すべての知識を現在の実装と照合する。

変更対象は test のみにしてください。

以下を証明してください。

- 元の Payment object がそのまま返る。
- PaymentGateway.request_authorization は呼ばれない。
- PaymentRepository.save は再度呼ばれない。

make test と make check を実行してください。
Pull Request を作成し、summary に以下を記載してください。

- current Git HEAD
- active knowledge mode
- 使用した knowledge files
- 実行した graph query
- validation results
```

### Session が作成されたことを確認する

タスク送信後、**Agents > All sessions** に Session が表示されます。

Session 内で次を確認してください。

1. `sessionStart` hook が実行された。
2. 次の command が実行された。

   ```bash
   python3 -m tools.knowledge.prepare_context --hook
   ```

3. `.agent-runtime/active-context.md` が作成された。
4. `test-knowledge` skill が利用された。
5. `PaymentService.authorize` の graph query が実行された。
6. generated knowledge と curated knowledge が読まれた。
7. `tests/test_payment_service.py` のみが変更された。
8. `make test` と `make check` が成功した。
9. Session から branch または Pull Request が作成された。

### 期待するテスト内容

追加されるテストは、既存 idempotency key の場合に次を検証します。

- 保存済みの `Payment` object と同一 object が返る。
- gateway の authorization method が呼ばれない。
- repository の `save` が再実行されない。

## Demo 2: ブランチごとの知識鮮度を確認する

1. `PaymentService.authorize` の処理を変更する branch を作成します。
2. `make knowledge` は実行しないでください。
3. その branch を base に `test-generator` Session を開始します。
4. 次の prompt を送信します。

```text
変更された PaymentService.authorize の behavior を分析し、必要な最小テストを
提案してください。ファイルは変更しないでください。

committed knowledge と runtime knowledge のどちらが active かを報告し、
committed/current source digest と runtime knowledge file を一覧にしてください。
```

期待結果:

```text
committed source digest != current source digest
    -> .agent-runtime/ に現在 branch 用 knowledge を生成
    -> runtime knowledge を committed baseline より優先
```

runtime knowledge が生成されても、現在の source code が最優先です。

## Demo 3: 共有 Knowledge Pack を更新する

ソース変更が受け入れられた後、`knowledge-curator` Agent を選択し、次を送信します。

```text
この branch の deterministic code graph と Agent Knowledge Pack を再生成して
検証してください。production behavior と curated policy は変更しないでください。

変更された knowledge artifact を説明し、make check を実行して Pull Request を
作成してください。
```

または GitHub Actions の **Refresh Agent Knowledge** workflow を手動実行します。

## Demo 4: テスト品質を評価する

`test-evaluator` Agent を選択し、次を送信します。

```text
現在 branch の PaymentService.authorize のテストを評価してください。
ファイルは変更しないでください。

knowledge freshness を確認し、target を depth 1 で query し、make test と
make check を実行してください。behavior gap、弱い assertion、nondeterminism、
使用した knowledge provenance を報告してください。
```

## チーム内で共有されるもの

Copilot cloud agent の Session は **Agents > All sessions** に表示され、リポジトリのアクセス権を持つメンバーが確認できます。

Session では次をレビューします。

- user prompt
- Agent response
- 実行 command
- tool usage
- 読み取ったファイル
- 変更ファイル
- validation result
- branch / Pull Request

ただし Session は長期知識の保存先ではありません。

正式な handoff artifact は次です。

```text
source commit / branch
+ artifacts/codegraph/
+ docs/agent-knowledge/
+ Pull Request
+ CI validation results
```

## GitHub Actions と Agent Session の違い

| 対象 | GitHub Actions | Copilot Agent Session |
|---|---:|---:|
| CI 実行 | はい | 必要に応じて実行 |
| 定期・イベント起動 | はい | 通常は task 起動 |
| Agent prompt/response | いいえ | はい |
| Agent のファイル探索履歴 | いいえ | はい |
| Agent による branch/PR 作成 | 通常は専用 script | はい |
| Agents > All sessions に表示 | いいえ | はい |

このため、CI や Wiki mirror workflow が成功していても、Agent task を開始していなければ Session 一覧は空です。

## Session が表示されない場合

### 1. Agent task をまだ開始していない

最も多い原因です。Custom Agent 定義を commit しただけでは Session は作られません。

### 2. GitHub Actions の画面を見ている

Actions の workflow run は Agents Session ではありません。GitHub の **Agents** タブを開いてください。

### 3. ローカルの VS Code / CLI Session を使った

ローカル Session は cloud Session と共有方法が異なる場合があります。共有操作を行っていなければ、他のメンバーの **All sessions** に表示されません。

### 4. Custom Agent が picker に出ない

確認項目:

- Agent file が `.github/agents/*.agent.md` にあるか
- default branch に merge 済みか
- frontmatter が有効か
- Copilot cloud agent が利用可能か

### 5. Repository または branch が違う

Session 作成時に次を確認してください。

```text
Repository: tkhjp/copilot-agent-knowledge-demo
Base branch: develop
Agent: test-generator
```

## Session のレビュー基準

このデモでは、単にテストが追加されたことだけでなく、次を確認します。

- 知識鮮度を確認したか
- 現在 source を最優先したか
- graph 全体ではなく小さい slice を query したか
- generated knowledge と curated policy を区別したか
- Session summary に provenance があるか
- test と knowledge validation が成功したか

## 関連資料

- [日本語 README](../README.ja.md)
- [英語 README](../README.md)
- [Architecture](architecture.md)
- [Wiki 運用ガイド（日本語）](wiki.ja.md)
- [Prompt examples](../examples/prompts.md)
