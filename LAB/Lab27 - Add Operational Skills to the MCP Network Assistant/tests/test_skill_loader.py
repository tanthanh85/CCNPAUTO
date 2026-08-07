from __future__ import annotations

from skill_loader import (
    load_skills,
    render_skill_collection,
    select_skills,
    validate_skill_tools,
)


def test_ospf_skill_loads_from_markdown() -> None:
    skills = load_skills()
    assert [skill.name for skill in skills] == ["ospf_no_routes"]
    assert set(skills[0].required_tools) == {
        "get_routes_by_protocol",
        "get_ospf_operational_status",
    }
    assert skills[0].triggers == ("ospf",)


def test_skill_requirements_match_catalog() -> None:
    validate_skill_tools(
        load_skills(),
        {"get_routes_by_protocol", "get_ospf_operational_status"},
    )


def test_rendered_skill_contains_evidence_order() -> None:
    prompt = render_skill_collection(load_skills())
    assert "matched_count" in prompt
    assert "get_ospf_operational_status" in prompt


def test_general_route_question_does_not_select_ospf_skill() -> None:
    selected = select_skills(
        "How many routes are present and how are they grouped by protocol?",
        load_skills(),
    )
    assert selected == []


def test_ospf_follow_up_selects_ospf_skill() -> None:
    selected = select_skills("Why are there no OSPF routes?", load_skills())
    assert [skill.name for skill in selected] == ["ospf_no_routes"]
