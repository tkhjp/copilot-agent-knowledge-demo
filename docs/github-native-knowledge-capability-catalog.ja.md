# GitHub ネイティブ機能カタログ — 共有 Project Knowledge の観点

**対象:** code graph、test knowledge、architecture metadata、domain rule などの共有・更新・確認・Agent 利用  
**更新日:** 2026-07-27  
**位置付け:** [共有 Knowledge 編成設計](shared-project-knowledge-management-design.ja.md)の機能別リファレンス

> 本資料は GitHub の全製品機能を一般目的で列挙するものではありません。共有 Project Knowledge の保存、可視化、変更管理、自動化、Agent 利用、監査に関係する GitHub ネイティブ機能を網羅的に整理します。

---

## 1. 機能全体マップ

| 分類 | GitHub 機能 | 本設計での主用途 |
|---|---|---|
| 人向け閲覧 | Wiki | 簡易 knowledge portal、確認、navigation |
| Agent 実行 | Copilot cloud agent / Agents tab / Session | 調査、変更、検証、実行履歴 |
| Context 集約 | Copilot Spaces | テーマ単位の curated context |
| 定期 Agent 実行 | Copilot Automations | schedule / Issue / PR event による Agent task |
| AI Workflow | GitHub Agentic Workflows | 自然言語で定義する repository automation |
| AI Review | Copilot code review | Pull Request の補助 review |
| Prompt 評価 | GitHub Models | prompt / model 比較、evaluation、`.prompt.yml` |
| 正本・履歴 | Repository files / Git | Source of Truth、version、branch、commit |
| 検索 | Repository indexing / Code Search | source と text knowledge の retrieval |
| 変更管理 | Pull Request / Review | diff、discussion、approval、merge |
| Ownership | CODEOWNERS | path owner と review request |
| Governance | Rulesets / Branch protection | required PR、approval、CI、push 制御 |
| 自動化 | GitHub Actions | generation、validation、publish、sync |
| 一時成果物 | Actions Artifacts | CI snapshot、report、debug output |
| 高速化 | Actions Cache | dependency / build cache |
| Credential | Secrets / Variables / Environments | external DB / MCP / publish credential |
| Feedback | Issues / Issue Forms | 誤り、stale、更新 request、task |
| 議論 | Discussions | proposal、Q&A、未確定事項 |
| 進捗 | Projects | backlog、owner、priority、roadmap |
| Rich portal | GitHub Pages | search、custom UI、graph visualization |
| Snapshot | Releases / Release Assets | immutable knowledge / graph bundle |
| Large file | Git LFS | branch / tag に紐づく large snapshot |
| Distribution | GitHub Packages / Container Registry | schema、tool、graph bundle の配布 |
| Static analysis | CodeQL database / Code Scanning | code relationship query、security analysis |
| Dependency | Dependency Graph | package dependency / SBOM |
| Dev environment | Codespaces / devcontainer | 再現可能な generator / Agent 実行環境 |
| Agent policy | Custom instructions / AGENTS.md | always-on policy、command、優先順位 |
| Reusable prompt | Prompt Files | task 起動 prompt の標準化 |
| Agent role | Custom Agents | role、tools、instructions の定義 |
| Procedure | Agent Skills | graph query、freshness、validation 手順 |
| Lifecycle | Copilot Hooks | sessionStart などの準備・強制 |
| Learned facts | Copilot Memory | 補助的 repository facts cache |
| External bridge | MCP | GraphDB / test DB / internal API 接続 |
| Integration | GitHub API / Webhooks / GitHub Apps | cross-repository automation、service identity |
| Organization governance | `.github` / `.github-private` | 共通 Agent、template、policy |
| Organization metadata | Custom properties | repository の分類、ruleset target |
| Audit | Organization audit log | actor、action、time の管理者監査 |

---

## 2. GitHub Wiki

### できること

- Markdown / Mermaid / image による閲覧 UI
- sidebar / footer / internal link
- Git history を持つ page 管理
- Repository 単位の onboarding portal
- code graph の要約や diagram の表示
- source file、Issue、Pull Request への導線

### できないこと・適さないこと

- 本体 Repository と同じ Pull Request による変更管理
- large raw graph の全量保存と query
- Agent が必ず利用する primary context
- Repository content との安全な双方向同期

### 推奨役割

```text
Repository knowledge → Wiki への一方向 publish
Wiki feedback → Issue / Discussion / Pull Request
```

---

## 3. Copilot cloud agent / Agents tab / Agent Session

### できること

- Repository を調査
- source / test / knowledge を branch 上で変更
- command、test、lint、generator を実行
- Pull Request を作成
- Agents tab で Session を確認・steer
- prompt、tool、command、file change、validation を共有

### できないこと・適さないこと

- Session を長期 knowledge database として使うこと
- human approval を置き換えること
- generated conflict の正当性を自動決定すること

### 推奨役割

```text
Agent = knowledge の利用者・変更提案者
Session = provenance
PR / commit = 正式な handoff
```

---

## 4. Copilot Spaces

### できること

- Repository、GitHub file、Issue、Pull Request、free text などを一つの context に集約
- 特定 domain / task の Q&A context をチーム共有
- GitHub 上の source content の更新に追随

### 制約

- Source of Truth ではない
- deterministic generation / conflict resolution の中心には向かない
- IDE 利用には GitHub MCP Server が必要
- raw code graph の query database ではない

### 推奨役割

```text
Repository knowledge = 正本
Space = curated context view
```

---

## 5. Copilot Automations

Copilot cloud agent を schedule または repository event で自動起動します。

### Trigger 例

- hourly / daily / weekly
- Issue created
- Pull Request opened
- Pull Request synchronized

### 利用例

- stale knowledge Issue の triage
- PR ごとの knowledge consistency 調査
- 定期的な documentation gap の確認
- knowledge refresh proposal の作成

### 制約

- 現時点では private / internal Repository 向け
- 実行ごとに cloud agent Session、Actions minutes、AI usage が発生
- untrusted input と write permission の設計が必要
- deterministic generator の代わりにはしない

### 推奨役割

固定 trigger で Agent に判断させたい task に利用します。

---

## 6. GitHub Agentic Workflows

自然言語 instructions を Markdown で定義し、AI coding agent を GitHub Actions 上で実行する automation です。

### 構成

```text
.github/workflows/<name>.md
.github/workflows/<name>.lock.yml
```

Frontmatter で trigger、permission、safe output、engine を制御し、Markdown body に Agent instructions を記載します。

### 利用例

- knowledge feedback Issue の分類
- CI failure の分析
- documentation と code の同期 proposal
- test coverage 改善 proposal
- daily / weekly knowledge status report

### 制約

- public preview
- deterministic build / graph generation は通常の Actions の方が適する
- AI output は人の review を前提にする
- engine credential、permission、safe output の設計が必要

### 推奨役割

```text
固定手順・同じ入力なら同じ出力
    → 通常の GitHub Actions

context を読み、判断し、proposal を作る
    → Agentic Workflow
```

---

## 7. Copilot Code Review

### できること

- Pull Request の差分を review
- suggestion を提示
- automatic review / re-review
- custom instructions、Agent Skills、MCP context の利用
- review comment から `Fix with Copilot`

### 制約

- Copilot review は `Comment` であり、required approval として数えない
- merge を block する正式 reviewer の代わりにはならない
- knowledge change の domain correctness は owner review が必要

### 推奨役割

- generated output の異常差分チェック
- Wiki exporter / workflow の review
- knowledge policy violation の補助検出
- 人の CODEOWNER review 前の first pass

---

## 8. GitHub Models

### できること

- model / prompt の比較
- structured evaluator による output evaluation
- prompt configuration を `.prompt.yml` として Repository に保存
- CLI / CI で evaluation
- Models REST API / SDK による利用

### 利用例

- test generation prompt の regression test
- knowledge summarization prompt の比較
- groundedness / relevance の evaluation
- model change による品質差の記録

### 制約

- Repository / Organization 向け機能の一部は public preview
- Project knowledge の保存先ではない
- code graph / test DB の代替ではない

### 推奨役割

Agent / LLM workflow 自体の prompt と model quality を管理します。

---

## 9. Repository files / Git / Repository Index / Code Search

### できること

- branch、commit、tag、history、blame
- source と knowledge の同一 PR 管理
- Markdown / JSON / JSONL / schema / tool の保存
- Copilot semantic index による relevant context retrieval
- Code Search による human search

### 制約

- record-level transaction / graph traversal database ではない
- large binary / frequent rewrite は Repository を肥大化させる
- raw graph を全量 context に入れると noise が増える

### 推奨役割

Small / medium knowledge の Source of Truth とします。

---

## 10. README / docs / Pages

### README / docs

- Repository entry point
- architecture / operation / governance の versioned source
- Agent と人の共通説明
- Wiki page の source

### GitHub Pages

- custom navigation
- full-text search
- interactive graph visualization
- documentation framework
- API reference

### 選択

```text
簡易 Markdown portal
    → Wiki

高度な検索・UI・visualization
    → Pages
```

どちらも Source of Truth は Repository files とします。

---

## 11. Pull Request / Review / CODEOWNERS / Rulesets

### Pull Request / Review

- diff
- inline comment
- approval / request changes
- status check
- merge history

### CODEOWNERS

Path 単位の owner を定義します。

```text
/docs/agent-knowledge/curated/ @org/domain-experts
/tools/knowledge/              @org/platform-team
/.github/agents/               @org/ai-governance
```

### Rulesets / Branch protection

- Pull Request 必須
- approval 必須
- CODEOWNER approval
- required status checks
- force push 禁止
- linear history
- file path / extension / size restriction
- automatic Copilot review

### 推奨役割

Git が conflict を検出し、PR / reviewer / ruleset が解決・承認 process を enforce します。

---

## 12. GitHub Actions / Artifacts / Cache

### GitHub Actions

- graph generation
- manifest generation
- freshness check
- deterministic verification
- schema validation
- Wiki publish
- external GraphDB publish
- notification

### Artifacts

- PR review 用 graph snapshot
- CI debugging report
- temporary evaluation output

Artifacts は retention 期限があるため Source of Truth にはしません。

### Cache

Dependency / build acceleration 用です。eviction されるため knowledge store にはしません。

---

## 13. Secrets / Variables / Environments

### Secrets

External GraphDB、MCP server、package registry、cloud storage の credential を Repository / Environment / Organization scope で保存します。

### Variables

Endpoint、snapshot namespace、schema version など、secret ではない configuration を保存します。

### Environments

`knowledge-staging`、`knowledge-production` などを定義し、次を設定できます。

- required approval
- allowed branch
- deployment protection
- environment secrets / variables

### 推奨役割

External knowledge store への publish を environment approval で gate します。

---

## 14. Issues / Issue Forms / Discussions / Projects

### Issues / Issue Forms

- stale report
- incorrect knowledge
- generator bug
- update request
- Agent task

### Discussions

- architecture proposal
- Q&A
- 未確定方針
- 複数案比較

### Projects

- status
- owner
- priority
- roadmap
- cross-repository backlog

### 使い分け

```text
議論中
    → Discussion

実行 task
    → Issue

具体的変更
    → Pull Request

複数 task の進捗
    → Project
```

---

## 15. Releases / LFS / Packages

### Releases / Release Assets

- tag に対応する immutable graph snapshot
- knowledge bundle
- audit snapshot

### Git LFS

- large file を branch / tag と対応づける
- working tree から local query する

### Packages / Container Registry

- graph bundle、schema、query tool を versioned package として複数 Repository に配布
- OCI image に query tool と snapshot を同梱

### 選択

| 要件 | 推奨 |
|---|---|
| immutable download | Release Asset |
| branch / tag と large file を対応 | Git LFS |
| reusable versioned bundle | Package / OCI |
| interactive graph query | External GraphDB |

---

## 16. CodeQL Database / Code Scanning / Dependency Graph

### CodeQL Database

- supported language の codebase database
- CodeQL query による static analysis
- relation / dataflow / security query

### Code Scanning

- SARIF finding を Pull Request / Security tab に表示
- code issue の workflow 化

### Dependency Graph

- package manifest / lockfile から dependency を表示
- direct / transitive dependency
- vulnerability / SBOM

### 制約

Dependency Graph は method call / inheritance / test impact の汎用 graph ではありません。

CodeQL は code analysis に強い一方、独自 domain knowledge / test result の汎用 store ではありません。

---

## 17. Codespaces / devcontainer

### できること

- Repository 固有の開発・generator 環境を再現
- browser / VS Code から同じ toolchain を利用
- branch / PR ごとの隔離環境
- `/workspaces` 内で作業を保持
- graph generator / query tool / Agent の local validation

### 制約

- Codespace filesystem は共有 knowledge database ではない
- team 共有は commit / push / external store が必要
- environment lifecycle をまたぐ正式な knowledge は Repository に保存する

### 推奨役割

Human が Agent と同じ generator / query command を再現する標準環境とします。

---

## 18. Custom Instructions / Prompt Files / Custom Agents / Skills / Hooks / Memory

### Custom Instructions / AGENTS.md

- knowledge priority
- build / test command
- generated file の編集禁止
- Wiki は正本ではないという policy

### Prompt Files

- test generation prompt
- knowledge refresh prompt
- Wiki feedback triage prompt

### Custom Agents

- Test Generator
- Knowledge Curator
- Test Evaluator
- Wiki Feedback Triage

### Agent Skills

- prepare context
- query graph
- validate manifest
- export Wiki

### Hooks

- `sessionStart` freshness check
- runtime knowledge generation
- prohibited path enforcement
- `agentStop` validation

### Copilot Memory

- frequently reused repository facts
- build command
- architecture convention

Memory は public preview の補助機能であり、versioned Source of Truth にはしません。

---

## 19. MCP / GitHub API / Webhooks / GitHub Apps

### MCP

Agent から external GraphDB、test DB、document system、internal API に接続します。

### GitHub API

Repository file、Issue、PR、Action、Release、Package の automation を実装します。

### Webhooks

push、PR、Issue、workflow event を external system に通知します。

### GitHub App

Organization / multi-repository 用の service identity、fine-grained permission、installation token を提供します。

### 選択

```text
Single Repository 内の workflow
    → GITHUB_TOKEN

Cross-repository / long-running service
    → GitHub App

Agent から external DB query
    → MCP

GitHub event を external system に通知
    → Webhook
```

---

## 20. Organization `.github` / `.github-private` / Custom Properties / Audit Log

### `.github` / `.github-private`

- organization custom agents
- common templates
- policy documents
- reusable workflows

Project-specific facts は各 Repository に残します。

### Custom Properties

Organization Repository に metadata を付与します。

例:

```text
knowledge_mode = repository-contained / external-graph
knowledge_owner = team-name
knowledge_maturity = pilot / production
wiki_enabled = true / false
agent_enabled = true / false
```

Custom property を ruleset target や repository filter に利用できます。

### Organization Audit Log

Organization 管理者が actor、action、repository、time を確認・検索・export できます。

Knowledge governance では次を監査します。

- permission change
- GitHub App change
- repository setting change
- Agent / Copilot action
- ruleset / Actions policy change

---

## 21. 目的別の標準編成

### 21.1 小規模 Repository の標準

```text
Repository files
+ Pull Request / CODEOWNERS / Ruleset
+ Actions CI
+ Wiki
+ Issue Form
+ Custom Agent / Skill / Hook
```

### 21.2 人向け閲覧を重視

```text
Repository Source of Truth
+ Wiki
+ Issue / Discussion feedback
```

UI 要件が増えたら Pages を追加します。

### 21.3 Agent 利用を重視

```text
Repository index
+ instructions
+ custom agents
+ skills
+ hooks
+ graph query tool
+ Agent Session provenance
```

### 21.4 定期・event-driven Agent task

```text
Private / internal Repository
+ Copilot Automations
```

または:

```text
GitHub Agentic Workflows
+ Actions trigger
+ safe outputs
```

### 21.5 AI prompt 品質評価

```text
GitHub Models
+ .prompt.yml
+ evaluation dataset
+ CI evaluation
```

### 21.6 大規模 graph

```text
Repository manifest / compact views
+ Release / Package / LFS for snapshot
+ External GraphDB for query
+ MCP for Agent access
+ GitHub App / Actions for publish
```

### 21.7 Organization scale

```text
Organization instructions / agents
+ .github-private
+ Custom Properties
+ Organization rulesets
+ Audit Log
+ Project-specific Repository Knowledge Packs
```

---

## 22. この Demo に対する採用判断

| 機能 | 現在 | 次の判断 |
|---|---|---|
| Repository Knowledge Pack | 採用済み | 継続 |
| Wiki | 採用済み | managed/manual page 分離を継続 |
| Agent / Session | Agent 定義済み | 実 Session を作成して利用確認 |
| Spaces | 未採用 | curated cross-document context が必要なら PoC |
| Copilot Automations | 対象外 | 現在 public Repository のため利用しない |
| Agentic Workflows | 未採用 | knowledge feedback triage で PoC 候補 |
| Copilot Code Review | optional | knowledge PR の first-pass review |
| GitHub Models | 未採用 | test generation prompt 評価で PoC 候補 |
| Issues / Issue Form | 採用 | Wiki feedback 入口 |
| Discussions | optional | 方針議論が増えたら enable |
| Projects | optional | update backlog が増えたら enable |
| Pages | 未採用 | graph visualization 要件が出たら採用 |
| Codespaces | 未採用 | standard demo environment が必要なら採用 |
| External GraphDB / MCP | 未採用 | graph size / query requirement で判断 |
| Custom Properties / Audit Log | Organization 移行時 | governance scale-out で採用 |

---

## 23. 公式仕様参照

- [Documenting your project with wikis](https://docs.github.com/en/communities/documenting-your-project-with-wikis)
- [Using Copilot cloud agent on GitHub](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-on-github)
- [Managing and tracking agents](https://docs.github.com/en/copilot/how-tos/copilot-on-github/use-copilot-agents/manage-and-track-agents)
- [About Copilot Spaces](https://docs.github.com/en/copilot/concepts/context/spaces)
- [About Copilot automations](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-automations)
- [About GitHub Agentic Workflows](https://docs.github.com/en/copilot/concepts/agents/about-github-agentic-workflows)
- [Using Copilot code review](https://docs.github.com/en/copilot/how-tos/copilot-on-github/use-copilot-agents/copilot-code-review)
- [About GitHub Models](https://docs.github.com/en/github-models/about-github-models)
- [Repository indexing for Copilot](https://docs.github.com/en/copilot/concepts/context/repository-indexing)
- [Managing rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets)
- [About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- [About Issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/learning-about-issues/about-issues)
- [GitHub Discussions](https://docs.github.com/en/discussions)
- [About Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)
- [GitHub Codespaces features](https://docs.github.com/en/codespaces/about-codespaces/codespaces-features)
- [CodeQL CLI](https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-cli)
- [Dependency graph](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-graph)
- [Managing custom properties](https://docs.github.com/en/organizations/managing-organization-settings/managing-custom-properties-for-repositories-in-your-organization)
- [Reviewing the organization audit log](https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-security-settings-for-your-organization/reviewing-the-audit-log-for-your-organization)
