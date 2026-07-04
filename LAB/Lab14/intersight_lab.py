#!/usr/bin/env python3
import os
import re

import intersight
from dotenv import load_dotenv
from intersight.api.compute_api import ComputeApi
from tabulate import tabulate


def api_client(key_id, key_file, endpoint):
    private_key = open(key_file, encoding="utf-8").read()
    if "BEGIN RSA PRIVATE KEY" in private_key:
        algorithm = intersight.signing.ALGORITHM_RSASSA_PKCS1v15
    elif "BEGIN EC PRIVATE KEY" in private_key:
        algorithm = intersight.signing.ALGORITHM_ECDSA_MODE_DETERMINISTIC_RFC6979
    else:
        raise ValueError("Unrecognized Intersight private-key format")
    signing = intersight.signing.HttpSigningConfiguration(
        key_id=key_id, private_key_string=private_key,
        signing_scheme=intersight.signing.SCHEME_HS2019,
        signing_algorithm=algorithm, hash_algorithm=intersight.signing.HASH_SHA256,
        signed_headers=[
            intersight.signing.HEADER_REQUEST_TARGET, intersight.signing.HEADER_HOST,
            intersight.signing.HEADER_DATE, intersight.signing.HEADER_DIGEST,
        ],
    )
    return intersight.ApiClient(intersight.Configuration(host=endpoint, signing_info=signing))


load_dotenv()
key_id = os.getenv("INTERSIGHT_API_KEY_ID", "")
key_file = os.getenv("INTERSIGHT_PRIVATE_KEY_FILE", "")
if not key_id or key_id.startswith("REPLACE_WITH_") or not os.path.isfile(key_file):
    raise SystemExit("Set a valid API key ID and private-key file in .env")

with api_client(key_id, key_file, os.getenv("INTERSIGHT_ENDPOINT", "https://intersight.com")) as client:
    response = ComputeApi(client).get_compute_physical_summary_list(top=100)
    results = getattr(response, "results", []) or []
    rows = [[x.name, x.serial, x.model, x.oper_power_state, x.management_mode] for x in results]
    print(tabulate(rows, headers=["Name", "Serial", "Model", "Power", "Management Mode"]))
    print(f"Retrieved {len(rows)} physical compute summaries")
