# TLS Certificate Lifecycle Runbook

## Overview

This runbook covers obtaining, deploying, rotating, and monitoring TLS certificates
for the production Nginx edge (`infra/nginx/nginx.prod.conf`).

The production compose overlay (`infra/docker-compose.prod.yml`) mounts
`infra/nginx/certs/` as `/etc/nginx/certs:ro` inside the Nginx container.

Nginx expects:
- `/etc/nginx/certs/edge.crt` — full-chain PEM certificate
- `/etc/nginx/certs/edge.key` — private key (PEM, no passphrase)

---

## Certificate Sources

Choose one of the following based on environment:

### Option A: Let's Encrypt (ACME) — recommended for internet-facing hosts

```bash
# Install certbot if not present
sudo dnf install -y certbot

# Obtain certificate (HTTP-01 challenge — stop nginx first)
sudo certbot certonly --standalone \
  --preferred-challenges http \
  -d your.domain.example.com

# Copy to infra certs dir
sudo cp /etc/letsencrypt/live/your.domain.example.com/fullchain.pem \
        /home/sbs/AI/infra/nginx/certs/edge.crt
sudo cp /etc/letsencrypt/live/your.domain.example.com/privkey.pem \
        /home/sbs/AI/infra/nginx/certs/edge.key
sudo chown $(id -u):$(id -g) /home/sbs/AI/infra/nginx/certs/edge.*
chmod 600 /home/sbs/AI/infra/nginx/certs/edge.key
chmod 644 /home/sbs/AI/infra/nginx/certs/edge.crt
```

### Option B: Internal CA / Self-signed (dev/staging without public DNS)

```bash
# Generate 2-year self-signed cert
openssl req -x509 -nodes -days 730 -newkey rsa:4096 \
  -keyout /home/sbs/AI/infra/nginx/certs/edge.key \
  -out /home/sbs/AI/infra/nginx/certs/edge.crt \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
chmod 600 /home/sbs/AI/infra/nginx/certs/edge.key
```

### Option C: Institutional certificate (manual PEM delivery)

Place the full-chain PEM and key files at the paths above.
Verify chain: `openssl verify -CAfile chain.pem edge.crt`

---

## Deploying a New Certificate

```bash
# 1. Place the new files in infra/nginx/certs/
#    (edge.crt = full-chain, edge.key = private key)

# 2. Verify the certificate/key pair matches
openssl x509 -noout -modulus -in infra/nginx/certs/edge.crt | md5sum
openssl rsa  -noout -modulus -in infra/nginx/certs/edge.key | md5sum
# Both md5 hashes must match.

# 3. Test nginx config
docker compose --env-file infra/.env -f infra/docker-compose.prod.yml \
  exec nginx nginx -t

# 4. Reload nginx (zero-downtime)
docker compose --env-file infra/.env -f infra/docker-compose.prod.yml \
  exec nginx nginx -s reload
```

---

## Certificate Rotation Schedule

| Certificate Source | Validity | Rotation Trigger |
|---|---|---|
| Let's Encrypt | 90 days | Automate via cron/systemd at 60 days |
| Institutional CA | Varies (typically 1-2 years) | 30 days before expiry |
| Self-signed (dev) | 730 days | On demand |

### Automated Let's Encrypt renewal (cron)

```cron
# /etc/cron.d/certbot-ai-platform
0 3 * * * root certbot renew --quiet --deploy-hook "
  cp /etc/letsencrypt/live/your.domain/fullchain.pem /home/sbs/AI/infra/nginx/certs/edge.crt &&
  cp /etc/letsencrypt/live/your.domain/privkey.pem  /home/sbs/AI/infra/nginx/certs/edge.key &&
  docker compose --env-file /home/sbs/AI/infra/.env -f /home/sbs/AI/infra/docker-compose.prod.yml exec nginx nginx -s reload
"
```

---

## Checking Expiry

```bash
# From host
openssl x509 -noout -dates -in infra/nginx/certs/edge.crt

# From live endpoint (replace hostname)
echo | openssl s_client -connect your.domain.example.com:443 2>/dev/null \
  | openssl x509 -noout -dates
```

Prometheus alert `TLSCertExpiringSoon` should fire at ≤30 days.

---

## Files Not Committed to Git

`infra/nginx/certs/` is in `.gitignore`.
Never commit private keys or certificates to the repository.

---

## Rollback

If a new certificate breaks TLS:

```bash
# Restore previous cert from backup
cp /secure/backup/edge.crt.prev infra/nginx/certs/edge.crt
cp /secure/backup/edge.key.prev infra/nginx/certs/edge.key
docker compose ... exec nginx nginx -s reload
```

Keep a copy of the previous certificate/key until the new cert is confirmed healthy.
