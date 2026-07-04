"""Build a Cisco IOS XE MDT configured-subscription payload."""


SUBSCRIPTIONS = [
    {
        "subscription-id": 601,
        "xpath": "/process-cpu-ios-xe-oper:cpu-usage/cpu-utilization",
    },
    {
        "subscription-id": 602,
        "xpath": "/memory-ios-xe-oper:memory-statistics/memory-statistic",
    },
    {
        "subscription-id": 603,
        "xpath": (
            "/interfaces-ios-xe-oper:interfaces/"
            "interface[name='GigabitEthernet1']/statistics"
        ),
    },
]


def build_mdt_payload(receiver_ip, receiver_port, period_cs):
    receiver_name = "LAB6_TELEGRAF"
    return {
        "Cisco-IOS-XE-mdt-cfg:mdt-config-data": {
            "mdt-named-protocol-rcvrs": {
                "mdt-named-protocol-rcvr": [
                    {
                        "name": receiver_name,
                        "protocol": "grpc-tcp",
                        "host": {"address": receiver_ip},
                        "port": receiver_port,
                    }
                ]
            },
            "mdt-subscription": [
                {
                    "subscription-id": item["subscription-id"],
                    "base": {
                        "stream": "yang-push",
                        "encoding": "encode-kvgpb",
                        "rcvr-type": "rcvr-type-protocol",
                        "period": period_cs,
                        "xpath": item["xpath"],
                    },
                    "mdt-receiver-names": {
                        "mdt-receiver-name": [{"name": receiver_name}]
                    },
                }
                for item in SUBSCRIPTIONS
            ],
        }
    }
