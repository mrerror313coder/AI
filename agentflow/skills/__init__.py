"""Skill package: discovery and registry for AgentFlow skills."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, Type

from skills.base import BaseSkill

# Built-in sample skills (also discoverable via package scan).
from skills.code_reviewer import CodeReviewerSkill
from skills.markdown_generator import MarkdownGeneratorSkill

_BUILTIN: list[Type[BaseSkill]] = [
    CodeReviewerSkill,
    MarkdownGeneratorSkill,
]


def _discover_skill_classes() -> list[Type[BaseSkill]]:
    """Import sibling modules and collect concrete BaseSkill subclasses."""
    found: dict[str, Type[BaseSkill]] = {}
    package = importlib.import_module("skills")
    for module_info in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        if module_info.name.rsplit(".", 1)[-1] in {"base", "__init__"}:
            continue
        module = importlib.import_module(module_info.name)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseSkill)
                and attr is not BaseSkill
                and getattr(attr, "name", None)
            ):
                found[attr.name] = attr
    # Ensure builtins are present even if discovery is run from odd cwd.
    for cls in _BUILTIN:
        found.setdefault(cls.name, cls)
    return list(found.values())


def load_skills() -> Dict[str, BaseSkill]:
    """Instantiate all discovered skills keyed by ``skill.name``."""
    registry: Dict[str, BaseSkill] = {}
    for cls in _discover_skill_classes():
        instance = cls()
        registry[instance.name] = instance
    return registry


__all__ = [
    "BaseSkill",
    "CodeReviewerSkill",
    "MarkdownGeneratorSkill",
    "load_skills",
]
