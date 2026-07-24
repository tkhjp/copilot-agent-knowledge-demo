from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Branch:
    line: int
    condition: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Node:
    id: str
    kind: str
    name: str
    qualified_name: str
    path: str
    line: int
    end_line: int
    parent: str | None = None
    doc: str = ""
    branches: tuple[Branch, ...] = field(default_factory=tuple)
    raises: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["branches"] = [branch.to_dict() for branch in self.branches]
        data["raises"] = list(self.raises)
        return data


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    kind: str
    path: str
    line: int
    resolution: str = "exact"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Graph:
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]

    def node_map(self) -> dict[str, Node]:
        return {node.id: node for node in self.nodes}
