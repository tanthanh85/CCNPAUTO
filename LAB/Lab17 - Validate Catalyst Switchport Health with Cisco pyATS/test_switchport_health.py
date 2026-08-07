from switchport_health_test import extract_switchport_counters


def test_extracts_iosxe_switchport_health_counters():
    parsed = {
        "interfaces": {
            "GigabitEthernet1/0/1": {
                "queues": {"total_output_drop": 7},
                "counters": {
                    "in_crc_errors": 1,
                    "out_interface_resets": 2,
                    "out_collision": 3,
                    "out_errors": 4,
                },
            },
            "Loopback0": {
                "queues": {"total_output_drop": 99},
                "counters": {"in_crc_errors": 99},
            },
        }
    }

    assert extract_switchport_counters(parsed) == {
        "GigabitEthernet1/0/1": {
            "crc_errors": 1,
            "interface_resets": 2,
            "collisions": 3,
            "output_errors": 4,
            "output_drops": 7,
        }
    }


def test_uses_out_drops_when_queue_counter_is_absent():
    # The current IOS XE ShowInterfaces parser normally places interface names
    # at the root of the parsed dictionary rather than under "interfaces".
    parsed = {
        "GigabitEthernet1": {
            "counters": {
                "in_crc_errors": "0",
                "out_interface_resets": "2",
                "out_collision": "0",
                "out_errors": "0",
                "out_drops": "5",
            }
        }
    }

    counters = extract_switchport_counters(parsed)
    assert counters["GigabitEthernet1"]["output_drops"] == 5
    assert counters["GigabitEthernet1"]["interface_resets"] == 2
