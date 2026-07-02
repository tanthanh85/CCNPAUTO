#!/usr/bin/env bash
set -u

PASS=0
FAIL=0

check_command() {
  local name="$1"
  local command_name="$2"
  if command -v "$command_name" >/dev/null 2>&1; then
    printf '[PASS] %-22s %s\n' "$name" "$(command -v "$command_name")"
    PASS=$((PASS + 1))
  else
    printf '[FAIL] %-22s command not found: %s\n' "$name" "$command_name"
    FAIL=$((FAIL + 1))
  fi
}

check_python_module() {
  local module="$1"
  if python -c "import ${module}" >/dev/null 2>&1; then
    printf '[PASS] Python module          %s\n' "$module"
    PASS=$((PASS + 1))
  else
    printf '[FAIL] Python module          %s\n' "$module"
    FAIL=$((FAIL + 1))
  fi
}

printf '\nLab 1 workstation validation\n'
printf '%s\n' '----------------------------------------'

check_command "Python" python
check_command "pip" pip
check_command "Git" git
check_command "Ansible" ansible
check_command "Terraform" terraform
check_command "Vault" vault
check_command "Docker" docker
check_command "Docker Compose" docker
check_command "kubectl" kubectl
check_command "Minikube" minikube
check_command "pyATS" pyats
check_command "VS Code" code
check_command "GitLab Runner" gitlab-runner

for module in requests netmiko scrapli ncclient xmltodict yaml json pyats genie; do
  check_python_module "$module"
done

if docker compose version >/dev/null 2>&1; then
  printf '[PASS] %-22s available\n' "Compose plugin"
  PASS=$((PASS + 1))
else
  printf '[FAIL] %-22s unavailable\n' "Compose plugin"
  FAIL=$((FAIL + 1))
fi

printf '%s\n' '----------------------------------------'
printf 'Passed: %d  Failed: %d\n' "$PASS" "$FAIL"

if (( FAIL > 0 )); then
  exit 1
fi
