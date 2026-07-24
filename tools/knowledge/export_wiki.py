from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .project import repository_root


PAGE_MAP = {
    "docs/agents-tab-demo.ja.md": "Agent-Session-Guide-JA.md",
    "docs/wiki.ja.md": "Wiki-Operation-Guide-JA.md",
    "docs/agent-knowledge/generated/system-overview.md": "Generated-System-Overview.md",
    "docs/agent-knowledge/generated/modules/payment-service.md": "Generated-Module-Payment-Service.md",
    "docs/agent-knowledge/generated/test-impact/payment-service.md": "Generated-Test-Impact-Payment-Service.md",
    "docs/agent-knowledge/curated/domain-rules.md": "Curated-Domain-Rules.md",
    "docs/agent-knowledge/curated/testing-policy.md": "Curated-Testing-Policy.md",
}


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
                "この Wiki は、リポジトリ内の Agent Knowledge Pack を人向けに閲覧するためのミラーです。",
                "Agent は Wiki ではなく、同一リポジトリの versioned knowledge files と現在の source code を優先します。",
                "",
                "## 最初に確認すること",
                "",
                "Custom Agent の定義を配置しただけでは Agent Session は作成されません。",
                "GitHub の **Agents** タブから実際の cloud agent task を開始すると、初めて **Agents > All sessions** に共有 Session が作成されます。",
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
                "## 役割分担",
                "",
                "```text",
                "Repository Knowledge Pack = Agent の共有・再利用可能な知識",
                "Agent Session            = prompt、command、変更理由、監査証跡",
                "GitHub Wiki              = 人向け閲覧、教育、ナビゲーション",
                "```",
                "",
                "## Governance",
                "",
                "Generated pages は自動化により上書きされます。Curated pages も Wiki で直接編集せず、main repository の Pull Request で管理してください。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (output / "_Sidebar.md").write_text(
        "\n".join(
            [
                "- [[Home]]",
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
