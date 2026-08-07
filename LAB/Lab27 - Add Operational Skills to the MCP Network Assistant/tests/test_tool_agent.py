from __future__ import annotations

import pytest

from tool_agent import ToolAgentError, _arguments


def test_arguments_accept_dictionary() -> None:
    assert _arguments({"protocol": "ospf"}) == {"protocol": "ospf"}


def test_arguments_parse_json_object() -> None:
    assert _arguments('{"prefix":"0.0.0.0/0"}') == {"prefix": "0.0.0.0/0"}


def test_arguments_reject_non_object() -> None:
    with pytest.raises(ToolAgentError):
        _arguments('["get_all_routes"]')
