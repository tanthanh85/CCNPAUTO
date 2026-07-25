# Generated telemetry payload

Use local Cisco YANG Suite at `https://localhost:8443` or Cisco DevNet Sandbox YANG Suite at `http://10.10.20.50:8480` against the active IOS XE reservation to create and validate `telemetry_payload.json` for `Cisco-IOS-XE-mdt-cfg`.

Use one receiver profile consistently:

- Cisco DevNet Sandbox C8KV: Telegraf at `10.10.20.50`, TCP `57500`.
- Local C8KV: a workstation address reachable from the router, TCP `57000`.

Do not commit a payload until its receiver address, receiver port, subscription IDs, sensor paths, encoding, and update interval have been reviewed.
