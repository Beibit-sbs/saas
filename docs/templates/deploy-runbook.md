# Deploy Runbook

## Preconditions
- Server access prepared
- Docker/Compose installed
- `.env` configured on server

## Deployment
1. Pull/upload release archive
2. Extract to target directory
3. `docker compose --env-file .env up -d --build`
4. Verify health endpoints

## Rollback
1. Switch to previous release directory
2. Run compose up with previous images
3. Verify health

## Post-Deploy Checks
- App responds via Nginx
- DB connectivity works
- Audit logs are generated
