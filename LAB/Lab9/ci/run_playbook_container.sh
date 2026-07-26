#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 PLAYBOOK LOG_FILE" >&2
  exit 2
fi

: "${AUTOMATION_IMAGE:?AUTOMATION_IMAGE is required}"
mkdir -p artifacts

known_hosts_copy="$(mktemp /tmp/ccnpauto-known-hosts.XXXXXX)"
runtime_home="$(mktemp -d /tmp/ccnpauto-ansible-home.XXXXXX)"

cleanup() {
  rm -f "$known_hosts_copy"
  rm -rf "$runtime_home"
}
trap cleanup EXIT

known_hosts_source="${HOME}/.ssh/known_hosts"
if [[ -r "$known_hosts_source" ]]; then
  cp "$known_hosts_source" "$known_hosts_copy"
else
  : > "$known_hosts_copy"
fi
chmod 644 "$known_hosts_copy"

mkdir -p \
  "$runtime_home/.ansible/tmp" \
  "$runtime_home/.cache" \
  "$runtime_home/.config"
chmod -R 700 "$runtime_home"

env_args=()
for name in NETBOX_URL NETBOX_TOKEN NETBOX_DEVICE NETBOX_TAG VAULT_ADDR VAULT_TOKEN \
  VAULT_MOUNT VAULT_IOSXE_PATH IOSXE_HOST IOSXE_SSH_PORT IOSXE_NETCONF_PORT \
  OSPF_PROCESS_ID OSPF_AREA ANSIBLE_AUDIT_LOG ENABLE_FILE_LOGGING \
  ENABLE_CONSOLE_LOGGING LOG_LEVEL LOG_CONSOLE_LEVEL LOG_DIR \
  CI_PIPELINE_ID CI_JOB_NAME; do
  if [[ -n "${!name:-}" ]]; then
    env_args+=(--env "$name")
  fi
done

docker run --rm --network host \
  --user "$(id -u):$(id -g)" \
  --volume "$CI_PROJECT_DIR:/workspace" \
  --volume "$runtime_home:/home/runtime" \
  --volume "$known_hosts_copy:/etc/ssh/ssh_known_hosts:ro" \
  --workdir /workspace \
  --env HOME=/home/runtime \
  --env ANSIBLE_LOCAL_TEMP=/home/runtime/.ansible/tmp \
  --env XDG_CACHE_HOME=/home/runtime/.cache \
  --env XDG_CONFIG_HOME=/home/runtime/.config \
  "${env_args[@]}" \
  "$AUTOMATION_IMAGE" "$1" 2>&1 | tee "$2"
