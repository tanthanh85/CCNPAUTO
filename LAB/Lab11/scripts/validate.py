#!/usr/bin/env python3
import logging

from src.common import configure_logging, load_vlans

configure_logging("validation.log")
vlans = load_vlans()
logging.info("Validated %s VLAN records", len(vlans))
