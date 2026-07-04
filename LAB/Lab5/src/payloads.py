"""Build XML and JSON payloads from one loopback dataset."""

from xml.etree import ElementTree as ET


IF_NS = "urn:ietf:params:xml:ns:yang:ietf-interfaces"
IP_NS = "urn:ietf:params:xml:ns:yang:ietf-ip"
IANA_NS = "urn:ietf:params:xml:ns:yang:iana-if-type"
NC_NS = "urn:ietf:params:xml:ns:netconf:base:1.0"

ET.register_namespace("", IF_NS)
ET.register_namespace("ietf-ip", IP_NS)
ET.register_namespace("ianaift", IANA_NS)
ET.register_namespace("nc", NC_NS)


def build_netconf_interfaces(loopbacks, operation="merge"):
    config = ET.Element(f"{{{NC_NS}}}config")
    interfaces = ET.SubElement(
        config,
        f"{{{IF_NS}}}interfaces",
        {"xmlns:ianaift": IANA_NS},
    )

    for loopback in loopbacks:
        interface = ET.SubElement(
            interfaces,
            f"{{{IF_NS}}}interface",
            {f"{{{NC_NS}}}operation": operation},
        )
        ET.SubElement(interface, f"{{{IF_NS}}}name").text = loopback["name"]
        ET.SubElement(interface, f"{{{IF_NS}}}description").text = loopback["description"]
        ET.SubElement(interface, f"{{{IF_NS}}}type").text = "ianaift:softwareLoopback"
        ET.SubElement(interface, f"{{{IF_NS}}}enabled").text = "true"

        ipv4 = ET.SubElement(interface, f"{{{IP_NS}}}ipv4")
        address = ET.SubElement(ipv4, f"{{{IP_NS}}}address")
        ET.SubElement(address, f"{{{IP_NS}}}ip").text = loopback["address"]
        ET.SubElement(address, f"{{{IP_NS}}}prefix-length").text = str(
            loopback["prefix_length"]
        )

    return ET.tostring(config, encoding="unicode")


def build_ospf_router_payload(loopbacks, process_id):
    return {
        "Cisco-IOS-XE-native:router": {
            "Cisco-IOS-XE-ospf:router-ospf": {
                "ospf": {
                    "process-id": [
                        {
                            "id": process_id,
                            "network": [
                                {
                                    "ip": loopback["address"],
                                    "wildcard": "0.0.0.0",
                                    "area": 0,
                                }
                                for loopback in loopbacks
                            ],
                        }
                    ]
                }
            }
        }
    }
