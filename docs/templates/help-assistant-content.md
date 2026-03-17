# Help Assistant Content Template

Use this file to define guidance content for in-app help.

## 1. Pages covered
- /admin
- /admin/roles
- /admin/integrations
- /records/new
- /records/edit

## 2. Field-level hints
- field: role_name
  hint: Use clear business role names, e.g. registrar, dean, methodist.
- field: ldap_bind_dn
  hint: Use a dedicated read-only bind account.
- field: openai_api_key
  hint: Store in env/secret manager only; never in source code.

## 3. Common Q&A
- Q: What should I write here?
  A: Follow module requirements and required field validation.
- Q: Why is save blocked?
  A: Check required fields, role permission, and input format.

## 4. Escalation
- If user still cannot proceed:
  1. Show related documentation link.
  2. Show admin support contact.
  3. Log unresolved help request for review.
