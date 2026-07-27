from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .project import repository_root


PAGE_MAP = {
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
                "この Wiki は、Repository 内の共有 Knowledge を人向けに閲覧・確認するための downstream mirror です。",
                "Knowledge の Source of Truth は同一 Repository 内の versioned files です。",
                "",
                "## 管理・利用設計",
                "",
                "- [[Shared Project Knowledge Management Design JA]]",
                "",
                "この設計書では、Repository files、GitHub Wiki、Copilot Spaces、Copilot Agent / Session、必要に応じた GitHub Pages または external GraphDB + MCP の組み合わせを説明します。",
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
                "Repository Knowledge Pack = Source of Truth / Agent が参照する知識",
                "Git commit / Pull Request = 更新・競合検出・review・承認",
                "GitHub Actions           = 生成・検証・Wiki 同期",
                "GitHub Wiki              = 人向け可視化・確認画面",
                "Copilot Spaces           = Copilot 問答用 curated context",
                "Agent Session            = prompt、command、変更理由、監査証跡",
                "```",
                "",
                "## Governance",
                "",
                "Managed Wiki pages は自動化により上書きされます。修正は Wiki を直接編集せず、main Repository の Issue または Pull Request で行ってください。",
                "Workflow 管理外の manual Wiki page は保持されますが、Agent の正式な knowledge source にはしません。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (output / "_Sidebar.md").write_text(
        "\n".join(
            [
                "- [[Home]]",
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
