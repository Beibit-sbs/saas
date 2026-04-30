#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="${ROOT_DIR}/infra"
ARTIFACTS_DIR="${ROOT_DIR}/artifacts/audits/pass-fail-warning-coverage"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${ARTIFACTS_DIR}/${STAMP}"
SUMMARY_TSV="${RUN_DIR}/summary.tsv"
SUMMARY_MD="${RUN_DIR}/summary.md"
MASTER_LOG="${RUN_DIR}/run.log"
PROFILE="standard"
DRY_RUN="false"
STOP_ON_FAIL="false"
RESUME_FROM=""
REACHED_RESUME="true"
COMPOSE_READY="false"
SELECTED_BATCHES=()

BACKEND_SHARD_SIZE="${BACKEND_SHARD_SIZE:-25}"
BACKEND_TESTS_REBUILD="${BACKEND_TESTS_REBUILD:-false}"
FRONTEND_TESTS_REBUILD="${FRONTEND_TESTS_REBUILD:-false}"
STRICT_WARNINGS="${STRICT_WARNINGS:-false}"

mkdir -p "${RUN_DIR}"

if [[ -z "${JWT_SECRET:-}" && -f "${INFRA_DIR}/.env" ]]; then
	source <(grep '^JWT_SECRET=' "${INFRA_DIR}/.env" || true)
fi
JWT_SECRET="${JWT_SECRET:-coverage-suite-secret-not-for-prod-1234567890}"

log() {
	printf '%s\n' "$*" | tee -a "${MASTER_LOG}"
}

usage() {
	cat <<EOF
Usage: bash scripts/pass_fail_warning_coverage.sh [options]

Options:
  --profile fast|standard|full   Coverage depth profile. Default: standard
  --batch NAME                   Run only the named batch. Repeatable.
  --resume-from NAME             Skip batches until NAME is reached.
  --stop-on-fail                 Stop after the first FAIL.
  --dry-run                      Print the planned batches without executing them.
  --help                         Show this help.

Environment:
  BACKEND_SHARD_SIZE             Files per backend pytest shard. Default: 25
  BACKEND_TESTS_REBUILD          Rebuild backend-tests image before sharded pytest. Default: false
  FRONTEND_TESTS_REBUILD         Rebuild frontend-tests image before frontend tests. Default: false
  STRICT_WARNINGS                Exit non-zero when warnings are present. Default: false

Artifacts:
  ${ARTIFACTS_DIR}/<timestamp>/summary.md
  ${ARTIFACTS_DIR}/<timestamp>/summary.tsv
  ${ARTIFACTS_DIR}/<timestamp>/*.log
EOF
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		--profile)
			PROFILE="${2:-}"
			shift 2
			;;
		--batch)
			SELECTED_BATCHES+=("${2:-}")
			shift 2
			;;
		--resume-from)
			RESUME_FROM="${2:-}"
			REACHED_RESUME="false"
			shift 2
			;;
		--stop-on-fail)
			STOP_ON_FAIL="true"
			shift
			;;
		--dry-run)
			DRY_RUN="true"
			shift
			;;
		--help)
			usage
			exit 0
			;;
		*)
			echo "Unknown option: $1" >&2
			usage >&2
			exit 2
			;;
	esac
done

case "${PROFILE}" in
	fast|standard|full) ;;
	*)
		echo "Invalid profile: ${PROFILE}" >&2
		usage >&2
		exit 2
		;;
esac

printf 'batch\tstatus\texit_code\tlog\tdetail\n' >"${SUMMARY_TSV}"

compose_cmd() {
	docker compose --project-directory "${INFRA_DIR}" --env-file "${INFRA_DIR}/.env" "$@"
}
export -f compose_cmd
export INFRA_DIR

has_selected_batches() {
	[[ ${#SELECTED_BATCHES[@]} -gt 0 ]]
}

is_selected_batch() {
	local name="$1"
	local selected
	if ! has_selected_batches; then
		return 0
	fi
	for selected in "${SELECTED_BATCHES[@]}"; do
		if [[ "${selected}" == "${name}" ]]; then
			return 0
		fi
	done
	return 1
}

record_result() {
	local name="$1"
	local status="$2"
	local exit_code="$3"
	local log_file="$4"
	local detail="$5"
	printf '%s\t%s\t%s\t%s\t%s\n' "${name}" "${status}" "${exit_code}" "${log_file}" "${detail//$'\n'/ }" >>"${SUMMARY_TSV}"
	log "[${status}] ${name}: ${detail}"
}

detect_warning_status() {
	local log_file="$1"
	if grep -Eiq '(^|[^A-Za-z])(\[WARN\]|WARNING:|warnings summary|PytestDeprecationWarning|DeprecationWarning)([^A-Za-z]|$)' "${log_file}"; then
		return 0
	fi
	if grep -Eiq '([1-9][0-9]* (skipped|deselected|xfailed))' "${log_file}"; then
		return 0
	fi
	return 1
}

run_batch() {
	local name="$1"
	local command="$2"
	local batch_log="${RUN_DIR}/${name}.log"
	local exit_code=0
	local status="PASS"
	local detail="ok"

	if [[ "${REACHED_RESUME}" != "true" ]]; then
		if [[ "${name}" == "${RESUME_FROM}" ]]; then
			REACHED_RESUME="true"
		else
			record_result "${name}" "SKIPPED" "0" "${batch_log}" "skipped before --resume-from ${RESUME_FROM}"
			return 0
		fi
	fi

	if ! is_selected_batch "${name}"; then
		record_result "${name}" "SKIPPED" "0" "${batch_log}" "not selected"
		return 0
	fi

	if [[ "${DRY_RUN}" == "true" ]]; then
		record_result "${name}" "PLANNED" "0" "${batch_log}" "${command}"
		return 0
	fi

	log "[run] ${name}"
	printf 'COMMAND: %s\n\n' "${command}" >"${batch_log}"
	bash -c "${command}" >>"${batch_log}" 2>&1 || exit_code=$?

	if [[ ${exit_code} -ne 0 ]]; then
		status="FAIL"
		detail="exit=${exit_code}"
	else
		if detect_warning_status "${batch_log}"; then
			status="WARNING"
			detail="exit=0 with warning patterns"
		fi
	fi

	record_result "${name}" "${status}" "${exit_code}" "${batch_log}" "${detail}"

	if [[ "${name}" == "compose-bootstrap" && ${exit_code} -eq 0 ]]; then
		COMPOSE_READY="true"
	fi

	if [[ "${status}" == "FAIL" && "${STOP_ON_FAIL}" == "true" ]]; then
		return 99
	fi
	return 0
}

run_or_skip_compose_batch() {
	local name="$1"
	local command="$2"
	local batch_log="${RUN_DIR}/${name}.log"
	if [[ "${DRY_RUN}" == "true" ]]; then
		run_batch "${name}" "${command}"
		return 0
	fi
	if [[ "${COMPOSE_READY}" != "true" ]]; then
		record_result "${name}" "SKIPPED" "0" "${batch_log}" "compose-bootstrap did not pass"
		return 0
	fi
	run_batch "${name}" "${command}"
}

run_backend_shards() {
	local -a files=()
	local shard_index=1
	local start=0
	local total=0
	local batch_name=""
	local command=""
	local shard_count=0

	mapfile -t files < <(find "${ROOT_DIR}/backend/tests" -type f \( -name 'test_*.py' -o -name '*_test.py' \) | sort)
	total=${#files[@]}
	if [[ ${total} -eq 0 ]]; then
		record_result "backend-pytest-shards" "WARNING" "0" "${RUN_DIR}/backend-pytest-shards.log" "no backend test files found"
		return 0
	fi

	shard_count=$(((total + BACKEND_SHARD_SIZE - 1) / BACKEND_SHARD_SIZE))
	if [[ "${DRY_RUN}" == "true" ]]; then
		if [[ "${BACKEND_TESTS_REBUILD}" == "true" ]]; then
			run_or_skip_compose_batch "backend-tests-build" "compose_cmd build backend-tests"
		fi
		while [[ ${shard_index} -le ${shard_count} ]]; do
			printf -v batch_name 'backend-pytest-shard-%02d' "${shard_index}"
			run_or_skip_compose_batch "${batch_name}" "dynamic backend pytest shard ${shard_index}/${shard_count}"
			shard_index=$((shard_index + 1))
		done
		record_result "backend-pytest-shards" "PLANNED" "0" "${RUN_DIR}/backend-pytest-shards.log" "${total} files across ${shard_count} shards"
		return 0
	fi

	if [[ "${COMPOSE_READY}" != "true" ]]; then
		record_result "backend-pytest-shards" "SKIPPED" "0" "${RUN_DIR}/backend-pytest-shards.log" "compose-bootstrap did not pass"
		return 0
	fi

	if [[ "${BACKEND_TESTS_REBUILD}" == "true" ]]; then
		run_or_skip_compose_batch "backend-tests-build" "compose_cmd build backend-tests"
	fi

	while [[ ${start} -lt ${total} ]]; do
		local -a shard_files=()
		local end=$((start + BACKEND_SHARD_SIZE))
		if [[ ${end} -gt ${total} ]]; then
			end=${total}
		fi
		shard_files=("${files[@]:start:end-start}")
		printf -v batch_name 'backend-pytest-shard-%02d' "${shard_index}"
		printf -v command 'compose_cmd run --rm --no-deps -e JWT_SECRET=%q -e DATABASE_URL= -e REDIS_URL= backend-tests pytest -q -o addopts= --no-cov --disable-warnings' "${JWT_SECRET}"
		for file in "${shard_files[@]}"; do
			printf -v command '%s %q' "${command}" "${file#${ROOT_DIR}/backend/}"
		done
		run_or_skip_compose_batch "${batch_name}" "cd ${ROOT_DIR}/backend && ${command}" || return $?
		start=${end}
		shard_index=$((shard_index + 1))
		if [[ "${STOP_ON_FAIL}" == "true" ]]; then
			batch_log="${RUN_DIR}/${batch_name}.log"
			if grep -q $'\tFAIL\t' "${SUMMARY_TSV}"; then
				return 99
			fi
		fi
	done

	record_result "backend-pytest-shards" "PASS" "0" "${RUN_DIR}/backend-pytest-shards.log" "${total} files across $((shard_index - 1)) shards"
}

write_summary() {
	local pass_count fail_count warning_count skipped_count planned_count
	pass_count=$(awk -F '\t' 'NR > 1 && $2 == "PASS" {c++} END {print c+0}' "${SUMMARY_TSV}")
	fail_count=$(awk -F '\t' 'NR > 1 && $2 == "FAIL" {c++} END {print c+0}' "${SUMMARY_TSV}")
	warning_count=$(awk -F '\t' 'NR > 1 && $2 == "WARNING" {c++} END {print c+0}' "${SUMMARY_TSV}")
	skipped_count=$(awk -F '\t' 'NR > 1 && $2 == "SKIPPED" {c++} END {print c+0}' "${SUMMARY_TSV}")
	planned_count=$(awk -F '\t' 'NR > 1 && $2 == "PLANNED" {c++} END {print c+0}' "${SUMMARY_TSV}")

	{
		echo "# PASS / FAIL / WARNING Coverage Summary"
		echo
		echo "- Timestamp UTC: ${STAMP}"
		echo "- Profile: ${PROFILE}"
		echo "- Pass: ${pass_count}"
		echo "- Fail: ${fail_count}"
		echo "- Warning: ${warning_count}"
		echo "- Skipped: ${skipped_count}"
		echo "- Planned: ${planned_count}"
		echo
		echo "| Batch | Status | Exit | Log | Detail |"
		echo "|-------|--------|------|-----|--------|"
		awk -F '\t' 'NR > 1 {printf("| %s | %s | %s | %s | %s |\n", $1, $2, $3, $4, $5)}' "${SUMMARY_TSV}"
	} >"${SUMMARY_MD}"

	log "[summary] pass=${pass_count} fail=${fail_count} warning=${warning_count} skipped=${skipped_count} planned=${planned_count}"
	log "[summary] markdown=${SUMMARY_MD}"

	if [[ ${fail_count} -gt 0 ]]; then
		return 1
	fi
	if [[ "${STRICT_WARNINGS}" == "true" && ${warning_count} -gt 0 ]]; then
		return 2
	fi
	return 0
}

run_profile() {
	run_batch "preflight" "bash ${ROOT_DIR}/scripts/preflight_checks.sh" || return $?
	run_batch "permission-parity" "bash ${ROOT_DIR}/scripts/check_permission_parity.sh" || return $?
	run_batch "compose-bootstrap" "compose_cmd up -d db redis backend frontend nginx" || return $?
	run_or_skip_compose_batch "backend-lint" "compose_cmd exec -T backend ruff check ." || return $?
	run_backend_shards || return $?
	run_or_skip_compose_batch "frontend-lint" "compose_cmd run --rm -T frontend-tests npm run lint" || return $?

	if [[ "${PROFILE}" == "standard" || "${PROFILE}" == "full" ]]; then
		if [[ "${FRONTEND_TESTS_REBUILD}" == "true" ]]; then
			run_or_skip_compose_batch "frontend-tests-build" "compose_cmd build frontend-tests" || return $?
		fi
		run_or_skip_compose_batch "frontend-tests" "compose_cmd run --rm -T frontend-tests npm run test:frontend" || return $?
		run_batch "domain-layer-gate" "bash ${ROOT_DIR}/scripts/domain_layer_gate.sh" || return $?
		run_batch "data-layer-gate" "bash ${ROOT_DIR}/scripts/data_layer_gate.sh" || return $?
		run_batch "smoke-gate" "bash ${ROOT_DIR}/scripts/platform_smoke_check.sh" || return $?
	fi

	if [[ "${PROFILE}" == "full" ]]; then
		run_batch "safe-gate" "bash ${ROOT_DIR}/scripts/university_pilot_safe_gate.sh" || return $?
		run_batch "release-gate" "bash ${ROOT_DIR}/scripts/release_gate.sh" || return $?
	fi

	return 0
}

log "[coverage] profile=${PROFILE} dry_run=${DRY_RUN} shard_size=${BACKEND_SHARD_SIZE} run_dir=${RUN_DIR}"
run_profile
run_exit=$?
write_summary
summary_exit=$?

if [[ ${run_exit} -eq 99 ]]; then
	exit ${summary_exit}
fi

if [[ ${summary_exit} -ne 0 ]]; then
	exit ${summary_exit}
fi

exit ${run_exit}