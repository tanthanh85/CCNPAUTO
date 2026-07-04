"""Render normalized loopback intent with the Lab 3 Jinja2 template."""

from pathlib import Path

from jinja2 import Template


class LoopbackRenderer:
    def __init__(self, template_path="templates/loopback.j2"):
        self.template_path = Path(template_path)

    def render(self, loopbacks):
        template = Template(self.template_path.read_text(encoding="utf-8"))
        output = template.render(loopbacks=loopbacks)
        return [line.strip() for line in output.splitlines() if line.strip()]
