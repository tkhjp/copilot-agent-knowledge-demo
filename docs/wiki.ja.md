# GitHub Wiki ミラー運用ガイド

[English version](wiki.md)

このリポジトリは、Agent Knowledge Pack の人向けミラーを GitHub Wiki に公開します。

Wiki:

<https://github.com/tkhjp/copilot-agent-knowledge-demo/wiki>

## Wiki の役割

Wiki は次の用途を想定しています。

- チームメンバーによる知識閲覧
- 新規参加者のオンボーディング
- module responsibility や test-impact の確認
- curated testing policy の共有
- Agent Knowledge Loop の説明

Wiki は Agent の第一優先コンテキストではありません。

## Agent が優先して読む情報

Agent は同一リポジトリの versioned files を権威ある知識として使用します。

```text
docs/agent-knowledge/generated/
docs/agent-knowledge/curated/
artifacts/codegraph/
```

知識の優先順位:

```text
現在のソースコード
  > 現在 branch 用 runtime knowledge
  > committed generated knowledge
  > curated rules
  > Wiki / Issue / PR / Session 履歴
```

## Wiki と Agent Session の違い

| 対象 | Wiki | Agent Session |
|---|---|---|
| 主目的 | 人向け知識閲覧 | Agent 実行履歴と監査 |
| 長期共有知識 | ミラーとして保持 | 適さない |
| prompt/response | なし | あり |
| command/tool log | なし | あり |
| Agent の権威ある情報源 | いいえ | いいえ |
| 更新元 | Repository Knowledge Pack | 個別の Agent task |

Wiki が存在しても Agent Session は作成されません。Session を作成するには GitHub の Agents タブから実際の cloud agent task を開始してください。

詳細:

- [GitHub Agents タブ デモ手順](agents-tab-demo.ja.md)

## 自動公開 workflow

次の workflow が Wiki を更新します。

```text
.github/workflows/mirror-wiki.yml
```

`develop` branch で次のファイルが変更されると、自動同期されます。

```text
docs/agent-knowledge/**
tools/knowledge/export_wiki.py
```

処理:

```text
Repository Knowledge Pack
        ↓
make wiki-export
        ↓
dist/wiki/*.md
        ↓
<repository>.wiki.git
        ↓
GitHub Wiki
```

## 公開ページ

- Home
- Sidebar navigation
- Generated System Overview
- Generated Module Payment Service
- Generated Test Impact Payment Service
- Curated Domain Rules
- Curated Testing Policy

## 編集ルール

### Generated ページ

直接編集しないでください。次回の mirror workflow で上書きされます。

変更元:

```text
docs/agent-knowledge/generated/
```

### Curated ページ

Wiki 上で直接編集せず、リポジトリ側を変更して Pull Request でレビューしてください。

変更元:

```text
docs/agent-knowledge/curated/
```

## 手動再公開

GitHub の Actions 画面で次を選びます。

```text
Mirror Knowledge to Wiki
→ Run workflow
→ Branch: develop
```

## トラブルシューティング

### Wiki repository が見つからない

GitHub Wiki を enable しただけでは `.wiki.git` が作成されない場合があります。GitHub UI で最初の Wiki ページを保存してから workflow を再実行します。

### Workflow は成功したが内容が変わらない

Repository Knowledge Pack の内容が同じ場合、空 commit は作成されません。

### Wiki とコードが矛盾する

現在のコードを正としてください。Wiki は下流 mirror です。

### Agent が Wiki を読んでいない

正常な設計です。Agent は repository 内の versioned knowledge を優先します。Wiki は人向けの portal です。

## 共有する際の推奨案内

リポジトリをチームメンバーに共有するときは、次の順で案内してください。

1. [日本語 README](../README.ja.md)
2. [Agents タブ デモ手順](agents-tab-demo.ja.md)
3. GitHub Wiki
4. `docs/architecture.md`
5. `.github/agents/` と `.github/skills/`

最初の実習では `test-generator` を使って共有 Agent Session を作成します。
