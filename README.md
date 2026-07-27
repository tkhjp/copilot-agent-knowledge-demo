# Copilot Agent Knowledge Demo

このリポジトリは、テスト生成を題材として、**Repository に紐づく共有プロジェクト知識を版管理・レビュー・可視化し、GitHub Copilot Agent から利用するための参考実装**を提供します。

主な対象は code graph、test-impact metadata、testing policy、domain rule です。単なる Agent デモではなく、知識の正本、派生表示、変更管理、Agent 実行を分離した構成を検証します。

## ドキュメント

- **[共有プロジェクト知識の管理・利用アーキテクチャ（日本語）](docs/shared-project-knowledge-management-design.ja.md)**
- **[日本語の詳細 README](README.ja.md)**
- **[GitHub Agents タブ実行ガイド（日本語）](docs/agents-tab-demo.ja.md)**
- **[GitHub Wiki 運用ガイド（日本語）](docs/wiki.ja.md)**
- [English README](README.en.md)
- [English Agents walkthrough](docs/agents-tab-demo.md)
- [Architecture](docs/architecture.md)
- [GitHub Wiki](https://github.com/tkhjp/copilot-agent-knowledge-demo/wiki)

## この Repository の位置付け

本 Repository は、GitHub の各機能を次の責務に分けて組み合わせます。

```text
Repository 内知識パック
        = 知識の正本 / 正式な記録元

Git branch / commit / Pull Request / CI
        = 更新管理 / 検証 / 競合検出

GitHub Wiki
        = 人向けの派生表示

Copilot Spaces
        = Copilot 利用向けに選別したコンテキスト

Copilot Agent
        = 実行・変更提案の担い手

Agent Session
        = 実行履歴・追跡情報
```

必要に応じて、GitHub Pages を高度な表示画面として、external GraphDB + MCP を大規模 graph query の仕組みとして追加します。

保存場所、必須要件・追加要件、情報種別ごとの保存方針、整合性モデル、競合解決、Wiki 公開、Agent 利用時の流れは、[共有プロジェクト知識の管理・利用アーキテクチャ](docs/shared-project-knowledge-management-design.ja.md)にまとめています。

## 最初に理解すべき点

`.github/agents/*.agent.md` を配置しただけでは、GitHub の **Agents > All sessions** に Session は作成されません。

```text
Custom Agent 定義を default branch に配置
        ↓
Agent picker で選択可能になる
        ↓
まだ Session はない
        ↓
Agents タブから実際の cloud agent task を開始
        ↓
共有 Agent Session が作成される
```

GitHub Actions の workflow run、通常の Pull Request、API 経由の commit は Agent Session ではありません。

最初の Session を作る手順は、[GitHub Agents タブ実行ガイド](docs/agents-tab-demo.ja.md)を参照してください。

## デモの構成

```text
現在の source code
        ↓
再生成可能な code graph
        ↓
Agent 向け知識パック
        ↓
Agent Skill + sessionStart freshness hook
        ↓
Custom Agent
        ↓
Tests / Pull Request / shared Agent Session
        ↓
GitHub Wiki mirror
```

知識の優先順位:

```text
現在の working tree のソースコード
      > 現在 branch 用の一時知識
      > commit 済みの自動生成知識
      > 人が管理するルール
      > Space / Wiki / Issue / PR / Session 履歴
```

## 実装済み機能

| 対象 | 実装 |
|---|---|
| Raw code graph | `artifacts/codegraph/` |
| Agent 向け共有知識 | `docs/agent-knowledge/generated/` |
| 人が管理するルール | `docs/agent-knowledge/curated/` |
| Branch 用の一時知識 | `.agent-runtime/` |
| Custom Agents | `.github/agents/` |
| Agent Skill | `.github/skills/test-knowledge/` |
| Session hook | `.github/hooks/knowledge-freshness.json` |
| CI / knowledge refresh | `.github/workflows/` |
| 人向け knowledge portal | GitHub Wiki |

## ローカル確認

必要環境:

- Python 3.11 以上
- GNU Make
- Git

```bash
make demo
```

または:

```bash
make check
make context
make query SYMBOL=PaymentService.authorize
```

## 最初の共有 Agent Session

GitHub の **Agents** タブで次を選択します。

```text
Repository: tkhjp/copilot-agent-knowledge-demo
Base branch: develop
Custom Agent: test-generator
```

使用する prompt は [日本語手順書](docs/agents-tab-demo.ja.md#demo-1-最初の共有-agent-session-を作成する) に記載しています。

Session 作成後は次を確認します。

- `sessionStart` freshness hook
- active knowledge mode
- `test-knowledge` skill
- `PaymentService.authorize` の graph query
- 自動生成知識と人手管理知識の参照
- test file の変更
- `make test` と `make check`
- branch または Pull Request

## Session、Knowledge、Wiki の役割

| 対象 | 役割 | Agent の正本か |
|---|---|---:|
| 現在の source code | 現在の実装事実 | はい |
| Raw code graph | 機械的な静的関係 | はい |
| Agent 向け知識パック | 再利用可能な共有知識 | はい |
| Branch 用の一時知識 | 現在 branch 用の最新投影 | はい |
| Copilot Spaces | Copilot 用の選別済みコンテキスト | いいえ |
| Agent Session | prompt、command、変更理由、監査証跡 | いいえ |
| GitHub Wiki | 人向け閲覧、教育、ナビゲーション | いいえ |

正式な Agent 間の引継ぎは Session URL ではなく、commit、branch、Pull Request、Repository 内知識パックで行います。

## Wiki

Wiki:

<https://github.com/tkhjp/copilot-agent-knowledge-demo/wiki>

Wiki は人向けの下流 mirror です。Agent は同一 Repository 内の版管理対象知識を優先します。

## License

MIT
