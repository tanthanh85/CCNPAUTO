"""Render Cisco IOS XE native-YANG OSPF configuration from loopback intent."""

import logging
from pathlib import Path
from xml.etree import ElementTree

from jinja2 import Template


logger = logging.getLogger(__name__)


class OSPFRenderer:
    def __init__(self, template_path="templates/ospf_native.xml.j2"):
        self.template_path = Path(template_path)

    def render(self, loopbacks, process_id=1, area=0):
        logger.info(
            "Rendering OSPF payload template=%s records=%d process_id=%s area=%s",
            self.template_path,
            len(loopbacks),
            process_id,
            area,
        )
        if not loopbacks:
            raise ValueError("At least one loopback is required for OSPF")
        if int(process_id) < 1:
            raise ValueError("OSPF process ID must be positive")
        if int(area) < 0:
            raise ValueError("OSPF area must not be negative")
        template = Template(self.template_path.read_text(encoding="utf-8"))
        payload = template.render(
            loopbacks=loopbacks,
            process_id=int(process_id),
            area=int(area),
        )
        ElementTree.fromstring(payload)
        logger.info(
            "Rendered and XML-validated OSPF payload characters=%d",
            len(payload),
        )
        logger.debug("Rendered OSPF payload=%s", payload)
        return payload
