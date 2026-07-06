#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 PLAYBOOK LOG_FILE" >&2
  exit 2
fi

: "${AUTOMATION_IMAGE:?AUTOMATION_IMAGE is required}"
mkdir -p artifacts

known_hosts_copy="$(mktemp /tmp/ccnpauto-known-hosts.XXXXXX)"
trap 'rm -f "$known_hosts_copy"' EXIT
cp /home/gitlab-runner/.ssh/known_hosts "$known_hosts_copy"
chmod 644 "$known_hosts_copy"

env_args=()
for name in NETBOX_URL NETBOX_TOKEN NETBOX_DEVICE NETBOX_TAG VAULT_ADDR VAULT_TOKEN \
  VAULT_MOUNT VAULT_IOSXE_PATH IOSXE_HOST IOSXE_SSH_PORT IOSXE_NETCONF_PORT \
  SANDBOX_MODE ALLOW_CONFIG_CHANGES OSPF_PROCESS_ID OSPF_AREA ANSIBLE_AUDIT_LOG \
  CI_PIPELINE_ID CI_JOB_NAME; do
  if [[ -n "${!name:-}" ]]; then
    env_args+=(--env "$name")
  fi
done

docker run --rm --network host \
  --user "$(id -u):$(id -g)" \
  --volume "$CI_PROJECT_DIR:/workspace" \
  --volume "$known_hosts_copy:/etc/ssh/ssh_known_hosts:ro" \
  --workdir /workspace \
  "${env_args[@]}" \
  "$AUTOMATION_IMAGE" "$1" 2>&1 | tee "$2"
