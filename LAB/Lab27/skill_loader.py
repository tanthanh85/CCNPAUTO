from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent
SKILLS_DIR = ROOT / "skills"
VALID_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


class SkillError(RuntimeError):
    """Raised when a local skill document is malformed or unsafe to load."""


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    triggers: tuple[str, ...]
    required_tools: tuple[str, ...]
    instructions: str
    source: Path

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "triggers": list(self.triggers),
            "required_tools": list(self.required_tools),
            "source": str(self.source.relative_to(ROOT)),
        }

    def as_prompt(self) -> str:
        return (
            f"## Skill: {self.name}\n"
            f"Purpose: {self.description}\n"
            f"Required tools: {', '.join(self.required_tools)}\n\n"
            f"{self.instructions.strip()}"
        )


def _split_front_matter(text: str, source: Path) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        raise SkillError(f"{source.name} must begin with YAML front matter")
    marker = text.find("\n---\n", 4)
    if marker == -1:
        raise SkillError(f"{source.name} has no closing front-matter marker")
    metadata = yaml.safe_load(text[4:marker]) or {}
    if not isinstance(metadata, dict):
        raise SkillError(f"{source.name} front matter must be a mapping")
    return metadata, text[marker + 5 :].strip()


def load_skills(directory: Path = SKILLS_DIR) -> list[Skill]:
    """Load validated, enabled Markdown skills from the local collection."""
    skills: list[Skill] = []
    names: set[str] = set()
    for source in sorted(directory.glob("*.md")):
        if source.name.lower() == "readme.md":
            continue
        metadata, instructions = _split_front_matter(
            source.read_text(encoding="utf-8"), source
        )
        if metadata.get("enabled", True) is False:
            continue
        name = str(metadata.get("name", "")).strip()
        description = str(metadata.get("description", "")).strip()
        triggers = metadata.get("triggers", [])
        required = metadata.get("required_tools", [])
        if not VALID_NAME.fullmatch(name):
            raise SkillError(f"{source.name} has an invalid skill name")
        if name in names:
            raise SkillError(f"Duplicate skill name: {name}")
        if not description or not instructions:
            raise SkillError(f"{source.name} needs a description and instructions")
        if not isinstance(triggers, list) or not all(
            isinstance(item, str) and item.strip() for item in triggers
        ):
            raise SkillError(f"{source.name} triggers must be a list of phrases")
        if not isinstance(required, list) or not all(
            isinstance(item, str) and VALID_NAME.fullmatch(item) for item in required
        ):
            raise SkillError(f"{source.name} required_tools must be a list of tool names")
        skills.append(
            Skill(
                name=name,
                description=description,
                triggers=tuple(item.strip().lower() for item in triggers),
                required_tools=tuple(required),
                instructions=instructions,
                source=source,
            )
        )
        names.add(name)
    logger.info("Loaded skill collection names=%s", [skill.name for skill in skills])
    return skills


def validate_skill_tools(skills: list[Skill], available_tools: set[str]) -> None:
    for skill in skills:
        missing = set(skill.required_tools).difference(available_tools)
        if missing:
            raise SkillError(
                f"Skill {skill.name} requires unavailable tools: {sorted(missing)}"
            )


def render_skill_collection(skills: list[Skill]) -> str:
    if not skills:
        return "No local operational skills are loaded."
    return "\n\n".join(skill.as_prompt() for skill in skills)


def select_skills(question: str, skills: list[Skill]) -> list[Skill]:
    """Select skills whose declared trigger appears in the learner's question."""
    normalized = question.casefold()
    selected = [
        skill
        for skill in skills
        if any(trigger.casefold() in normalized for trigger in skill.triggers)
    ]
    logger.info(
        "Selected skills question_characters=%d names=%s",
        len(question),
        [skill.name for skill in selected],
    )
    return selected
