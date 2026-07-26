from unittest.mock import Mock

from loopback_recovery import (
    LoopbackRecovery,
    RouterSettings,
    is_loopback1_shutdown,
)


def settings():
    return RouterSettings(
        host="192.168.200.1",
        port=22,
        username="apphost",
        password="secret",
        device_type="cisco_ios",
        timeout=10,
    )


def test_detect_only_loopback1_shutdown():
    assert is_loopback1_shutdown(
        "%LINK-5-CHANGED: Interface Loopback1, "
        "changed state to administratively down"
    )
    assert not is_loopback1_shutdown(
        "%LINK-3-UPDOWN: Interface Loopback1, changed state to up"
    )
    assert not is_loopback1_shutdown(
        "%LINK-5-CHANGED: Interface Loopback2, "
        "changed state to administratively down"
    )


def test_netmiko_sends_no_shutdown_and_disconnects():
    connection = Mock()
    connection.send_config_set.return_value = "configuration accepted"
    connection.send_command.return_value = (
        "Loopback1 is up, line protocol is up"
    )
    factory = Mock(return_value=connection)
    recovery = LoopbackRecovery(settings(), connection_factory=factory)

    assert recovery.enable_loopback1() is True
    factory.assert_called_once_with(
        host="192.168.200.1",
        port=22,
        username="apphost",
        password="secret",
        device_type="cisco_ios",
        timeout=10,
    )
    connection.send_config_set.assert_called_once_with(
        ["interface Loopback1", "no shutdown"]
    )
    connection.disconnect.assert_called_once()


def test_verification_detects_interface_still_down():
    connection = Mock()
    connection.send_config_set.return_value = "configuration accepted"
    connection.send_command.return_value = (
        "Loopback1 is administratively down, line protocol is down"
    )
    recovery = LoopbackRecovery(
        settings(),
        connection_factory=Mock(return_value=connection),
    )

    assert recovery.enable_loopback1() is False
