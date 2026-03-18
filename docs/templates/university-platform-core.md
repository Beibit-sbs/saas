# University Platform Core Template

Use this template when the derived project targets higher education.
For other verticals, treat it as an example profile and adapt capability requirements to domain scope.

## 1. Admin Dashboard
- User and role management
- Integration settings (LDAP/AD, AI providers)
- System flags and maintenance controls

## 2. Authentication and Identity
- Local auth enabled
- LDAP/AD auth enabled (or planned with timeline)
- Session/JWT policy defined

## 3. RBAC
- Role matrix documented
- Endpoint-level permissions mapped
- Admin-only actions isolated

## 4. Audit and Compliance
- Admin actions logged with actor, action, target, timestamp, source IP
- Sensitive actions marked and searchable
- Log retention policy defined

## 5. AI Provider Gateway
- Provider adapter contract documented
- Supported providers listed
- Key management policy defined

## 6. Backup and Restore
- Backup schedule documented
- Restore test procedure documented
- Recovery objectives (RPO/RTO) documented
