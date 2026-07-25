from filter_plugins.drift_filters import build_drift_report


INTENT = [{"name": "Loopback101", "ipv4": "192.0.2.101", "enabled": True}]


def test_compliant_state():
    interfaces = "interface Loopback101\n description NETBOX_MANAGED\n ip address 192.0.2.101 255.255.255.255\n"
    ospf = "router ospf 1\n network 192.0.2.101 0.0.0.0 area 0\n"
    assert build_drift_report(INTENT, interfaces, ospf)["compliant"] is True


def test_missing_and_unmanaged_state():
    interfaces = "interface Loopback999\n ip address 198.51.100.9 255.255.255.255\n"
    report = build_drift_report(INTENT, interfaces, "router ospf 1\n")
    assert report["missing_interfaces"] == ["Loopback101"]
    assert report["unmanaged_loopbacks"] == ["Loopback999"]
    assert report["compliant"] is False
