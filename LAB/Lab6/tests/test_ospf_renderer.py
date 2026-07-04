from src.ospf_renderer import OSPFRenderer


def test_render_two_loopbacks():
    loopbacks = [
        {"ipv4": "192.0.2.101"},
        {"ipv4": "192.0.2.102"},
    ]
    payload = OSPFRenderer().render(loopbacks, process_id=1, area=0)
    assert payload.count("<network>") == 2
    assert "<ip>192.0.2.101</ip>" in payload
    assert "<area>0</area>" in payload

