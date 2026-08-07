"""Render normalized loopback intent with the Lab 3 Jinja2 template."""

import logging
from pathlib import Path

from jinja2 import Template


logger = logging.getLogger(__name__)


class LoopbackRenderer:
    def __init__(self, template_path="templates/loopback.j2"):
        self.template_path = Path(template_path)

    def render(self, loopbacks):
        logger.info(
            "Rendering loopback configuration template=%s records=%d",
            self.template_path,
            len(loopbacks),
        )
        template = Template(self.template_path.read_text(encoding="utf-8"))
        output = template.render(loopbacks=loopbacks)
        commands = [line.strip() for line in output.splitlines() if line.strip()]
        logger.info("Rendered %d non-empty configuration line(s)", len(commands))
        logger.debug("Rendered loopback commands=%s", commands)
        return commands
