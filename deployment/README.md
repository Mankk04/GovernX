# Deployment Notes

See the root `docker-compose.yml` for local/dev deployment.

For production (Section 23 Deployment Architecture):

1. Put the frontend build (`npm run build` output) and backend behind an
   Nginx reverse proxy / load balancer terminating TLS.
   
3. Run 2+ backend (FastAPI/Uvicorn) replicas behind the load balancer for
   availability.
4. Run the cloud poller as a separate scheduled background worker (Celery +
   Redis, or a simple cron invoking the scan endpoint) rather than inline
   with API requests, so polling never blocks the live dashboard.
5. Use managed PostgreSQL and Redis (or self-hosted with encrypted volumes)
   with automated backups.
6. Store secrets (DB password, JWT secret, cloud credentials) in a secrets
   manager (AWS Secrets Manager / HashiCorp Vault), never in the image or
   docker-compose file.
7. Enable a WAF and rate limiting at the edge.
