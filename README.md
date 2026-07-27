# Copilot Agent Knowledge Demo

このリポジトリは、テスト生成を対象にした **共有可能・鮮度管理可能・GitHub Copilot から参照可能な Agent Knowledge Loop** の実行デモです。

## ドキュメント

- **[GitHub ネイティブ機能カタログ — 共有 Project Knowledge の観点](docs/github-native-knowledge-capability-catalog.ja.md)**
- **[GitHub 機能を用いた共有 Knowledge の編成・運用設計](docs/shared-project-knowledge-management-design.ja.md)**
- **[日本語の詳細 README](README.ja.md)**
- **[GitHub Agents タブ実行ガイド（日本語）](docs/agents-tab-demo.ja.md)**
- **[GitHub Wiki 運用ガイド（日本語）](docs/wiki.ja.md)**
- [English README](README.en.md)
- [English Agents walkthrough](docs/agents-tab-demo.md)
- [Architecture](docs/architecture.md)
- [GitHub Wiki](https://github.com/tkhjp/copilot-agent-knowledge-demo/wiki)

## この Repository の位置付け

本 Repository は、あるプロジェクトで共有前提となる knowledge（例: code graph）について、GitHub Wiki、Copilot Agents、Spaces、Repository files、Pull Request、Actions、Issues、Discussions、Projects、Pages、Releases、LFS、Packages、CodeQL、Models、Codespaces、Agentic Workflows、MCP などの GitHub 機能をどの目的で組み合わせるかを示す reference implementation です。

基本構成:

```text
Repository knowledge files
        = Source of Truth

Git branch / commit / Pull Request / CI / Ruleset
        = 更新・競合検出・review・承認

GitHub Wiki / Pages
        = 人向けの可視化・確認画面

Issues / Discussions / Projects
        = feedback・議論・進捗管理

GitHub Copilot Agent / Skills / Hooks / MCP
        = knowledge の利用・変更提案・外部データ接続
```

各 GitHub 機能の「できること・できないこと」は[機能カタログ](docs/github-native-knowledge-capability-catalog.ja.md)、目的別の組み合わせ方、更新、conflict 解決、Wiki 同期、Agent 導入後の workflow は[編成・運用設計](docs/shared-project-knowledge-management-design.ja.md)にまとめています。

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
deterministic code graph
        ↓
Agent Knowledge Pack
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
      > 現在 branch 用 runtime knowledge
      > committed generated knowledge
      > curated rules
      > Wiki / Issue / PR / Session 履歴
```

## 実装済み機能

| 対象 | 実装 |
|---|---|
| Raw code graph | `artifacts/codegraph/` |
| Agent 向け共有知識 | `docs/agent-knowledge/generated/` |
| 人が管理するルール | `docs/agent-knowledge/curated/` |
| Branch-aware knowledge | `.agent-runtime/` |
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
- generated / curated knowledge の参照
- test file の変更
- `make test` と `make check`
- branch または Pull Request

## Session、Knowledge、Wiki の役割

| 対象 | 役割 | Agent の権威ある情報源か |
|---|---|---:|
| 現在の source code | 現在の実装事実 | はい |
| Raw code graph | 機械的な静的関係 | はい |
| Agent Knowledge Pack | 再利用可能な共有知識 | はい |
| Branch runtime knowledge | 現在 branch 用の最新投影 | はい |
| Agent Session | prompt、command、変更理由、監査証跡 | いいえ |
| GitHub Wiki | 人向け閲覧、教育、ナビゲーション | いいえ |

正式な Agent 間 handoff は Session URL ではなく、commit、branch、Pull Request、Knowledge Pack で行います。

## Wiki

Wiki:

<https://github.com/tkhjp/copilot-agent-knowledge-demo/wiki>

Wiki は人向けの downstream mirror です。Agent は同一リポジトリ内の versioned knowledge files を優先します。

## License

MIT
