from src.restconf_client import IOSXERoutingClient


def test_normalize_namespaced_routes():
    payload = {
        "Cisco-IOS-XE-rib-oper:rib": {
            "route": [
                {
                    "prefix": "10.10.10.0/24",
                    "route-source": "ospf",
                    "distance": 110,
                    "metric": 20,
                    "next-hop": {
                        "next-hop-address": "192.0.2.1",
                        "outgoing-interface": "GigabitEthernet1",
                    },
                },
                {
                    "prefix": "0.0.0.0/0",
                    "route-source": "static",
                    "next-hop-address": "192.0.2.254",
                },
            ]
        }
    }
    routes = IOSXERoutingClient.normalize_routes(payload)
    assert len(routes) == 2
    ospf = next(route for route in routes if route["prefix"] == "10.10.10.0/24")
    assert ospf["protocol"] == "ospf"
    assert ospf["next_hop"] == "192.0.2.1"
    assert ospf["interface"] == "GigabitEthernet1"

