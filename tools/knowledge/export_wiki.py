from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .project import repository_root


PAGE_MAP = {
    "docs/tree-sitter-code-graph-update-sync-design.ja.md": "Tree-Sitter-Code-Graph-Update-Sync-Design-JA.md",
    "docs/shared-project-knowledge-management-design.ja.md": "Shared-Project-Knowledge-Management-Design-JA.md",
    "docs/agents-tab-demo.ja.md": "Agent-Session-Guide-JA.md",
    "docs/wiki.ja.md": "Wiki-Operation-Guide-JA.md",
    "docs/agent-knowledge/generated/system-overview.md": "Generated-System-Overview.md",
    "docs/agent-knowledge/generated/modules/payment-service.md": "Generated-Module-Payment-Service.md",
    "docs/agent-knowledge/generated/test-impact/payment-service.md": "Generated-Test-Impact-Payment-Service.md",
    "docs/agent-knowledge/curated/domain-rules.md": "Curated-Domain-Rules.md",
    "docs/agent-knowledge/curated/testing-policy.md": "Curated-Testing-Policy.md",
}


ISSUE_URL = (
    "https://github.com/tkhjp/copilot-agent-knowledge-demo/issues/new"
    "?template=knowledge-feedback.yml"
)


def export(root: Path, output: Path) -> None:
    shutil.rmtree(output, ignore_errors=True)
    output.mkdir(parents=True, exist_ok=True)
    for source_name, destination_name in PAGE_MAP.items():
        source = root / source_name
        if not source.exists():
            raise FileNotFoundError(source)
        shutil.copyfile(source, output / destination_name)

    (output / "Home.md").write_text(
        "\n".join(
            [
                "# Copilot Agent Knowledge Demo",
                "",
                "この Wiki は、Repository 内の共有情報を人向けに閲覧・確認するための派生表示です。",
                "Tree-sitter Code Graph の正しさは source code、generator、grammar、config を基準に判断し、graph snapshot はそれらから再生成します。",
                "",
                "## Code Graph の更新・同期",
                "",
                "- [[Tree Sitter Code Graph Update Sync Design JA]]",
                "",
                "Tree-sitter から生成する構造 Code Graph について、branch-local 生成、Pull Request 検証、default branch の単一 writer、競合回避、Wiki 同期、Agent 利用を説明します。",
                "",
                "## 共有 Knowledge の管理・利用設計",
                "",
                "- [[Shared Project Knowledge Management Design JA]]",
                "",
                "Repository files、GitHub Wiki、Copilot Spaces、Copilot Agent / Session、必要に応じた GitHub Pages または external GraphDB + MCP の組み合わせを説明します。",
                "",
                "## 利用ガイド",
                "",
                "- [[Agent Session Guide JA]]",
                "- [[Wiki Operation Guide JA]]",
                "",
                "## Knowledge pages",
                "",
                "- [[Generated System Overview]]",
                "- [[Generated Module Payment Service]]",
                "- [[Generated Test Impact Payment Service]]",
                "- [[Curated Domain Rules]]",
                "- [[Curated Testing Policy]]",
                "",
                "## Feedback",
                "",
                f"- [Knowledge の誤り・更新要求を Issue として登録する]({ISSUE_URL})",
                "- 具体的な修正は source Repository の Pull Request で行ってください。",
                "",
                "## 役割分担",
                "",
                "```text",
                "Source + generator + grammar = Code Graph の生成基準",
                "Repository graph snapshot    = 特定 source state の共有派生物",
                "Git commit / Pull Request     = 更新・競合検出・review・承認",
                "GitHub Actions               = 生成・検証・shared graph / Wiki 同期",
                "GitHub Wiki                  = 人向け可視化・確認画面",
                "Copilot Spaces              = Copilot 問答用の選別済みコンテキスト",
                "Agent Session               = prompt、command、変更理由、監査証跡",
                "```",
                "",
                "## Governance",
                "",
                "自動管理 Wiki page は workflow により上書きされます。修正は Wiki を直接編集せず、main Repository の Issue または Pull Request で行ってください。",
                "Workflow 管理外の手動 Wiki page は保持されますが、Agent の正式な情報源にはしません。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (output / "_Sidebar.md").write_text(
        "\n".join(
            [
                "- [[Home]]",
                "- [[Tree Sitter Code Graph Update Sync Design JA]]",
                "- [[Shared Project Knowledge Management Design JA]]",
                "- [[Agent Session Guide JA]]",
                "- [[Wiki Operation Guide JA]]",
                "- [[Generated System Overview]]",
                "- [[Generated Module Payment Service]]",
                "- [[Generated Test Impact Payment Service]]",
                "- [[Curated Domain Rules]]",
                "- [[Curated Testing Policy]]",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a flat GitHub Wiki mirror.")
    parser.add_argument("--output", type=Path, default=Path("dist/wiki"))
    args = parser.parse_args()
    root = repository_root()
    output = args.output if args.output.is_absolute() else root / args.output
    export(root, output)
    print(f"wiki export written to {output.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
