from cpu_monitor import parse_cpu_output


def test_parse_cpu_output():
    output = (
        "CPU utilization for five seconds: 7%/2%; "
        "one minute: 4%; five minutes: 3%"
    )
    assert parse_cpu_output(output) == {
        "cpu_5_seconds_pct": 7.0,
        "cpu_interrupt_5_seconds_pct": 2.0,
        "cpu_1_minute_pct": 4.0,
        "cpu_5_minutes_pct": 3.0,
    }


def test_parse_decimal_cpu_output():
    output = (
        "CPU utilization for five seconds: 1.5%/0.5%; "
        "one minute: 2.0%; five minutes: 2.5%"
    )
    result = parse_cpu_output(output)
    assert result["cpu_1_minute_pct"] == 2.0

