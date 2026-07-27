# GitHub Wiki ミラー運用ガイド

[English version](wiki.md)

このリポジトリでは、共有プロジェクト知識の正本を Repository 内の版管理対象ファイルに置き、GitHub Wiki を人向けの閲覧・確認・feedback 画面として利用します。

Wiki:

<https://github.com/tkhjp/copilot-agent-knowledge-demo/wiki>

共有知識全体の保存、更新、競合解決、Spaces、Agent 利用については、次を参照してください。

- [共有プロジェクト知識の管理・利用アーキテクチャ](shared-project-knowledge-management-design.ja.md)

---

## 1. Wiki の役割

Wiki は次の用途を想定しています。

- チームメンバーによる knowledge の閲覧
- 新規参加者の onboarding
- system overview の確認
- module responsibility、dependency、test impact の確認
- domain rule / testing policy の共有
- source commit、source digest、generator version、status の確認
- Repository file、Issue、Pull Request への navigation
- Agent が作成した変更内容を人が理解するための補助画面

Wiki は Agent の第一優先 context ではなく、knowledge の正本でもありません。

```text
Repository 内知識パック
    = 正本

GitHub Wiki
    = 人向けの派生表示
```

---

## 2. GitHub 機能との役割分担

| 機能 | Wiki 運用における役割 |
|---|---|
| Repository files | Wiki に表示する内容の正本 |
| Git branch / commit | 版と変更履歴 |
| Pull Request / review | 内容変更の確認・承認 |
| CODEOWNERS / Rulesets | owner review と merge rule の強制 |
| GitHub Actions | Wiki page の生成・同期 |
| GitHub Wiki | 人向け閲覧・確認・navigation |
| Issues | 誤り、stale、更新要求の受付 |
| Discussions | 方針相談、Q&A、複数案の議論 |
| Projects | feedback / update backlog の進捗管理 |
| Copilot Agent | Repository knowledge を読み、変更案を作成 |
| Agent Session | Agent の prompt、command、変更理由、検証履歴 |
| GitHub Pages | Wiki より高度な検索・可視化が必要な場合の拡張先 |

---

## 3. Agent が優先して読む情報

Agent は同一 Repository の版管理対象ファイルを正本として使用します。

```text
docs/agent-knowledge/generated/
docs/agent-knowledge/curated/
artifacts/codegraph/
```

Knowledge の優先順位:

```text
現在 branch の source code
  > 現在 branch 用の一時知識
  > commit 済みの自動生成知識
  > 人が管理するルール
  > Space / Wiki / Issue / PR / Session 履歴
```

Wiki page と現在の source code が矛盾する場合、現在の source code を正とします。

---

## 4. Wiki と Agent Session の違い

| 対象 | Wiki | Agent Session |
|---|---|---|
| 主目的 | 人向け knowledge 閲覧・確認 | Agent 実行履歴と監査 |
| 長期共有 knowledge | Repository の mirror として保持 | 適さない |
| prompt / response | なし | あり |
| command / tool log | なし | あり |
| Agent の正本 | いいえ | いいえ |
| 更新元 | Repository 内知識パック | 個別の Agent task |
| 正式な引継ぎ | いいえ | いいえ |

正式な Agent 間の引継ぎは次です。

```text
commit
+ branch
+ Pull Request
+ Repository knowledge files
+ manifest
```

Wiki が存在しても Agent Session は作成されません。Session を作成するには GitHub の Agents タブから実際の cloud agent task を開始してください。

詳細:

- [GitHub Agents タブ デモ手順](agents-tab-demo.ja.md)

---

## 5. 自動管理 page と手動 page

Wiki page を2種類に分けます。

### 5.1 自動管理 page

Repository から GitHub Actions により生成・同期される page です。

例:

- Home
- Sidebar
- 共有 Knowledge の管理設計
- Agent Session Guide
- Wiki Operation Guide
- Generated System Overview
- Generated Module Knowledge
- Generated Test Impact
- Curated Domain Rules
- Curated Testing Policy

規則:

- Wiki 上で直接編集しない
- source Repository の file を変更する
- Pull Request と review を経由する
- merge 後に workflow が再公開する

### 5.2 手動 page

利用者が Wiki 上で作成する、workflow 管理外の page です。

想定用途:

- meeting note
- 一時的な検討メモ
- onboarding note
- 人向け FAQ

規則:

- mirror workflow は削除・上書きしない
- Agent の正式な knowledge source にはしない
- project rule や確定 knowledge になった内容は Repository file に移し、Pull Request で管理する

Workflow は `wiki/.managed-pages` に自動管理 page の一覧を記録し、前回の自動管理 page のみを置換します。

---

## 6. 自動公開 workflow

次の workflow が Wiki を更新します。

```text
.github/workflows/mirror-wiki.yml
```

`develop` branch で次の file が変更されると、自動同期されます。

```text
docs/agent-knowledge/**
docs/shared-project-knowledge-management-design.ja.md
docs/agents-tab-demo.ja.md
docs/wiki.ja.md
tools/knowledge/export_wiki.py
.github/ISSUE_TEMPLATE/knowledge-feedback.yml
```

手動実行も可能です。

```text
Actions
→ Mirror Knowledge to Wiki
→ Run workflow
→ Branch: develop
```

---

## 7. Wiki 同期処理

```text
1. develop を checkout
2. make wiki-export
3. dist/wiki/*.md を生成
4. <repository>.wiki.git を clone
5. 前回の .managed-pages を読み取る
6. 自動管理 page のみ削除・置換
7. 手動 page を保持
8. 新しい .managed-pages を保存
9. Wiki commit を作成
10. Wiki master branch に push
```

```text
Repository 内知識パック
        ↓
make wiki-export
        ↓
dist/wiki/*.md
        ↓
自動管理 page を更新
        ↓
<repository>.wiki.git
        ↓
GitHub Wiki
```

同時実行は次で制御します。

```yaml
concurrency:
  group: mirror-agent-knowledge-wiki
  cancel-in-progress: true
```

古い source commit の publish が、新しい page を後から上書きすることを防ぎます。

---

## 8. Wiki page に表示する metadata

自動管理 page の先頭には、次の情報を表示することを推奨します。

```markdown
> **管理方式:** Repository から自動同期される page
> **Source repository:** `owner/repository`
> **Published from commit:** `abcdef1`
> **Source digest:** `sha256:...`
> **Generator version:** `1.1.0`
> **Status:** CURRENT
> **Source file:** `docs/agent-knowledge/generated/...`
> **修正方法:** Wiki を直接編集せず、Issue または Pull Request を作成してください。
```

これにより利用者は、見ている page がどの source version に対応するかを確認できます。

---

## 9. Feedback の流れ

Wiki content の同期は一方向ですが、利用者の feedback は Repository に戻します。

```text
Repository knowledge
        ↓ publish
Wiki page
        ↓ user review
Issue / Discussion / Pull Request
        ↓
Repository change
        ↓ merge
Wiki republish
```

### 9.1 誤り・更新要求

Issue Form を使用します。

```text
.github/ISSUE_TEMPLATE/knowledge-feedback.yml
```

Issue には次を記録します。

- 対象 Wiki page
- 対応する Repository file
- source commit / digest
- feedback category
- 現在の記載・挙動
- 期待する内容・挙動
- Agent / user への影響

### 9.2 方針相談・Q&A

結論が未確定の場合は GitHub Discussions を使用します。

```text
未確定の議論
    → Discussion

実行すべき修正が明確
    → Issue

具体的な変更差分
    → Pull Request
```

### 9.3 進捗管理

複数の knowledge update request を管理する場合は GitHub Projects を使用します。

Project には status、owner、priority、target date を置き、knowledge 本体は Repository に残します。

---

## 10. 公開 page

- Home
- Sidebar navigation
- 共有プロジェクト知識の管理・利用アーキテクチャ
- Agent Session Guide
- Wiki Operation Guide
- Generated System Overview
- Generated Module Payment Service
- Generated Test Impact Payment Service
- Curated Domain Rules
- Curated Testing Policy

---

## 11. 編集ルール

### 自動生成 page

直接編集しないでください。次回の mirror workflow で上書きされます。

変更元:

```text
docs/agent-knowledge/generated/
tools/knowledge/
source code / tests
```

自動生成 knowledge が誤っている場合、source code または generator の Issue として扱います。

### 人手管理 page

Wiki 上で直接編集せず、Repository 側を変更して Pull Request で review してください。

変更元:

```text
docs/agent-knowledge/curated/
```

Policy change には domain owner / test owner の review を推奨します。

### 手動 page

Workflow 管理外であることを明示してください。確定 knowledge になった場合は Repository の版管理対象 file に移します。

---

## 12. トラブルシューティング

### Wiki Repository が見つからない

GitHub Wiki を enable しただけでは `.wiki.git` が作成されない場合があります。GitHub UI で最初の Wiki page を保存してから workflow を再実行します。

### Workflow は成功したが内容が変わらない

Repository knowledge と出力した Wiki content が同じ場合、空 commit は作成されません。

### 手動 page が消えた

現在の workflow は `.managed-pages` に記録した自動管理 page のみを削除します。古い workflow が手動 page を削除した場合は Wiki history から復元してください。

### Wiki と code が矛盾する

現在の source code と Repository knowledge を正としてください。Wiki は派生表示です。

### Agent が Wiki を読んでいない

正常な設計です。Agent は Repository 内の版管理対象 knowledge を優先します。Wiki は人向けの portal です。

---

## 13. チームへの案内順序

1. [共有プロジェクト知識の管理・利用アーキテクチャ](shared-project-knowledge-management-design.ja.md)
2. [日本語 README](../README.ja.md)
3. [Agents タブ デモ手順](agents-tab-demo.ja.md)
4. GitHub Wiki
5. `docs/architecture.md`
6. `.github/agents/` と `.github/skills/`

最初の実習では `test-generator` を使い、共有 Agent Session を作成します。
