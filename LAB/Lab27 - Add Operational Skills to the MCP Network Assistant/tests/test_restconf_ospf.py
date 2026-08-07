from __future__ import annotations

import restconf_ospf
from restconf_ospf import _collect_nodes, _first_values


SAMPLE = {
    "Cisco-IOS-XE-ospf-oper:ospf-oper-data": {
        "ospf-state": {
            "ospf-instance": [
                {
                    "process-id": 1,
                    "router-id": "192.0.2.1",
                    "ospf-area": [
                        {
                            "area-id": "0.0.0.0",
                            "ospf-interface": [
                                {
                                    "name": "GigabitEthernet1",
                                    "ospf-neighbor": [
                                        {"neighbor-id": "192.0.2.2", "state": "full"}
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ]
        }
    }
}


def test_collects_ospf_hierarchy_nodes() -> None:
    assert len(_collect_nodes(SAMPLE, {"ospf-instance"})) == 1
    assert len(_collect_nodes(SAMPLE, {"ospf-area"})) == 1
    assert len(_collect_nodes(SAMPLE, {"ospf-interface"})) == 1
    assert len(_collect_nodes(SAMPLE, {"ospf-neighbor"})) == 1


def test_extracts_neighbor_evidence() -> None:
    neighbor = _collect_nodes(SAMPLE, {"ospf-neighbor"})[0]
    assert _first_values(neighbor, {"neighbor-id", "state"}) == {
        "neighbor-id": "192.0.2.2",
        "state": "full",
    }


def test_operational_status_is_bounded_and_summarized(monkeypatch) -> None:
    class FakeClient:
        def get(self, path: str):
            assert path == restconf_ospf.OSPF_OPERATIONAL_PATH
            return SAMPLE

    monkeypatch.setattr(restconf_ospf, "IosXeRestconfClient", FakeClient)
    result = restconf_ospf.ospf_operational_status()
    assert result["process_count"] == 1
    assert result["area_count"] == 1
    assert result["interface_count"] == 1
    assert result["neighbor_count"] == 1
    assert result["neighbor_state_counts"] == {"full": 1}
