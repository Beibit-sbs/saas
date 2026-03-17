# Template Sync Playbook

## Purpose
Use this playbook to transfer proven improvements from completed projects back to the master template.

Master template path:
- `/home/sbs/AI`

Rule:
- Do not copy project-to-project directly.
- Promote reusable changes to the master template first.

## Promotion Flow
1. Identify reusable change in project repository.
2. Extract only generic parts (no project-specific data or secrets).
3. Apply changes to master template (`/home/sbs/AI`).
4. Run validation in template:
   - template validation entrypoint
   - backend tests
   - frontend lint/build
   - docker compose smoke check
5. Update docs and checklists.
6. Create new projects only from updated template.

## Derived Project Bootstrap Flow
1. Copy the master template into a new repository.
2. Rename confirmed project identity surfaces:
   - `README.md`
   - `docs/project-status.md`
   - `PROJECT_CONTEXT.md`
   - user-facing copy that still references the template name
3. Copy `infra/.env.example` to `infra/.env`.
4. Review required startup variables:
   - `POSTGRES_DB`
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
   - `JWT_SECRET`
   - `NEXT_PUBLIC_API_BASE_URL`
5. Review scaffold modules before promising them for production use.
6. Run template validation before adding domain features.

## What Can Be Promoted
- Cross-project modules and adapters.
- Security hardening and guardrails.
- CI/CD improvements.
- Docs templates and operating playbooks.
- Reusable admin workflows.

## What Must Not Be Promoted
- Project-specific business logic.
- Real credentials or production secrets.
- One-off hacks and emergency patches.
- Data model fragments tied to a single project domain.

## Quality Gate Before Promotion
- Backward compatible by default or protected with feature flags.
- No default credentials introduced.
- Migration path exists for schema changes.
- Audit impact reviewed for admin-sensitive changes.
- README and module docs updated.
- Contracts and env/config docs are grounded in confirmed code behavior or existing env examples.
- Example-only modules remain explicitly labeled and removable.

## New Project Rule
When starting a new project:
1. Copy from master template.
2. Initialize a new repository.
3. Add `PROJECT_CONTEXT.md` with project-specific scope.
4. Keep platform core unchanged unless approved.
5. Run the template validation entrypoint before feature development.

## Suggested Commit Message Prefixes
- `template(core): ...`
- `template(security): ...`
- `template(devops): ...`
- `template(docs): ...`
