#!/usr/bin/env python3
import os

from dotenv import load_dotenv
from tabulate import tabulate
from ucsmsdk import ucsmethodfactory as mf
from ucsmsdk.ucshandle import UcsHandle


load_dotenv()
required = ["UCSM_HOST", "UCSM_USERNAME", "UCSM_PASSWORD"]
if any(not os.getenv(x) or os.getenv(x).startswith("REPLACE_WITH_") for x in required):
    raise SystemExit("Complete UCS Manager settings in .env")

handle = UcsHandle(
    ip=os.environ["UCSM_HOST"], username=os.environ["UCSM_USERNAME"],
    password=os.environ["UCSM_PASSWORD"], secure=os.getenv("UCSM_SECURE", "false").lower() == "true",
)
try:
    handle.login()
    blades = handle.query_classid("computeBlade")
    racks = handle.query_classid("computeRackUnit")
    rows = [[x.dn, x.serial, x.model, x.oper_state, x.assigned_to_dn] for x in [*blades, *racks]]
    print(tabulate(rows, headers=["DN", "Serial", "Model", "State", "Assigned Profile"]))

    templates = [x for x in handle.query_classid("lsServer") if x.type in ("initial-template", "updating-template")]
    print("\nService Profile Templates")
    print(tabulate([[x.dn, x.name, x.type] for x in templates], headers=["DN", "Name", "Type"]))

    if os.getenv("ALLOW_UCS_CHANGES", "false").lower() != "true":
        print("Read-only run complete. Enable ALLOW_UCS_CHANGES only in a reserved emulator.")
    else:
        template_dn = os.environ["UCSM_TEMPLATE_DN"]
        profile_name = os.getenv("UCSM_PROFILE_NAME", "LAB17-AU-SERVER-01")
        if handle.query_dn(f"{os.getenv('UCSM_TARGET_ORG', 'org-root')}/ls-{profile_name}"):
            raise RuntimeError(f"Service profile {profile_name} already exists")
        request = mf.ls_instantiate_template(
            cookie=handle.cookie, dn=template_dn, in_error_on_existing="true",
            in_server_name=profile_name, in_target_org=os.getenv("UCSM_TARGET_ORG", "org-root"),
            in_hierarchical="false",
        )
        created = handle.process_xml_element(request)
        print("Created:", [item.dn for item in created])
finally:
    handle.logout()
