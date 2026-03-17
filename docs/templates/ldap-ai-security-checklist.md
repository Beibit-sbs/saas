# LDAP and AI Keys Security Checklist

## LDAP/AD
- [ ] Service account is least-privileged
- [ ] LDAP bind credentials are in env/secret manager only
- [ ] LDAP over TLS/LDAPS is configured for production
- [ ] Group-to-role mapping is documented

## AI Provider Keys
- [ ] API keys are not stored in code or git
- [ ] Separate keys are used per environment
- [ ] Key rotation process exists
- [ ] Provider usage and quota monitoring is enabled

## Runtime Controls
- [ ] Rate limiting is enabled on AI endpoints
- [ ] Sensitive prompts/responses are redacted in logs
- [ ] Access to provider management endpoints is admin-only
