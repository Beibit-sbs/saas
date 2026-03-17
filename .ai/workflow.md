# Operating Workflow

## Stage Gates
1. Architect: produce architecture draft and wait for approval.
2. Developer: implement approved scope only.
3. Reviewer: check violations and test completeness.
4. Security: run security checklist and report findings.
5. DevOps: package and prepare deploy artifacts.

## Command Prefixes for Prompting AI
- `Architect:` for architecture tasks
- `Developer:` for implementation tasks
- `Reviewer:` for review tasks
- `Security:` for security checks
- `DevOps:` for infra/deploy tasks

## Fast Loop
idea -> architect -> developer -> reviewer -> security -> devops -> docker -> server deploy

## Template Hardening Order
When the task is template hardening rather than product feature delivery, apply work in this order:
1. bootstrap flow and required docs
2. maturity matrix
3. confirmed contracts
4. single validation entrypoint
5. oversized file decomposition
6. example-only extension slice

Do not invent env vars, contracts, or platform rules that are not confirmed by the repository.
