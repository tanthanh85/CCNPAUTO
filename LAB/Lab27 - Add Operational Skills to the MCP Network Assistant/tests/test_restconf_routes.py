from __future__ import annotations

from restconf_routes import DEFAULT_ROUTE_ENDPOINTS, _find_routes, _normalize


def test_iosxe_ietf_operational_route_endpoint_is_first() -> None:
    assert DEFAULT_ROUTE_ENDPOINTS[0].endswith(
        "/routing-instance=default/ribs/rib=ipv4-default/routes/route"
    )


def test_normalize_ietf_route_record() -> None:
    payload = {
        "ietf-routing:route": [
            {
                "destination-prefix": "0.0.0.0/0",
                "source-protocol": "ietf-routing:static",
                "route-preference": 1,
                "next-hop": {"next-hop-address": "198.51.100.1"},
            }
        ]
    }
    routes = _find_routes(payload)
    assert len(routes) == 1
    assert _normalize(routes[0]) == {
        "prefix": "0.0.0.0/0",
        "protocol": "static",
        "next_hops": ["198.51.100.1"],
        "metric": 1,
        "active": "unknown",
    }


def test_normalize_native_fib_fallback_record() -> None:
    payload = {
        "Cisco-IOS-XE-fib-oper:fib-entries": [
            {
                "ip-addr": "192.0.2.0/24",
                "fib-nexthop-entries": [
                    {"nh-addr": "198.51.100.2/32", "ifname": "GigabitEthernet1"}
                ],
            }
        ]
    }
    routes = _find_routes(payload)
    assert len(routes) == 1
    normalized = _normalize(routes[0])
    assert normalized["prefix"] == "192.0.2.0/24"
    assert normalized["next_hops"] == ["198.51.100.2/32"]
