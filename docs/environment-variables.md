# Environment Variables

Configuration reference for the Python API Base project.

## Required Variables

### APP_NAME
- **Description:** Application display name
- **Default:** `My API`
- **Example:** `APP_NAME="Production API"`

### APP_ENV
- **Description:** Environment identifier
- **Values:** `development`, `staging`, `production`
- **Default:** `development`

### DATABASE__URL
- **Description:** PostgreSQL connection string (async)
- **Format:** `postgresql+asyncpg://user:password@host:port/database`
- **Required:** Yes
- **Example:** `DATABASE__URL=postgresql+asyncpg://postgres:postgres@localhost:5432/mydb`

### SECURITY__SECRET_KEY
- **Description:** Secret key for JWT signing (min 32 chars)
- **Required:** Yes
- **Security:** Never commit to version control
- **Generate:** `python -c "import secrets; print(secrets.token_urlsafe(64))"`

### REDIS__URL
- **Description:** Redis connection URL
- **Format:** `redis://[:password]@host:port/db`
- **Default:** `redis://localhost:6379/0`

## Optional Variables

### Database

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE__POOL_SIZE` | Connection pool size | `5` |
| `DATABASE__MAX_OVERFLOW` | Max overflow connections | `10` |
| `DATABASE__ECHO` | Echo SQL statements | `false` |

### Security

| Variable | Description | Default |
|----------|-------------|---------|
| `SECURITY__CORS_ORIGINS` | Allowed CORS origins (JSON array) | `["*"]` |
| `SECURITY__RATE_LIMIT` | Rate limit config | `100/minute` |
| `SECURITY__ALGORITHM` | JWT algorithm | `HS256` |
| `SECURITY__ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `30` |

### Observability

| Variable | Description | Default |
|----------|-------------|---------|
| `OBSERVABILITY__LOG_LEVEL` | Log level | `INFO` |
| `OBSERVABILITY__LOG_FORMAT` | Log format (`json`/`console`) | `json` |
| `OBSERVABILITY__PROMETHEUS_ENABLED` | Enable Prometheus metrics | `true` |
| `OBSERVABILITY__KAFKA_ENABLED` | Enable Kafka producer | `false` |

### Redis

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS__ENABLED` | Enable Redis for token storage | `false` |
| `REDIS__TOKEN_TTL` | Token TTL in seconds | `604800` |

## Security Best Practices

1. Never commit `.env` files with real credentials
2. Use `SECURITY__SECRET_KEY` with minimum 64 characters
3. Set `SECURITY__CORS_ORIGINS` to specific domains in production
4. Disable `DATABASE__ECHO` in production
5. Use `OBSERVABILITY__LOG_FORMAT=json` in production

## Example .env

```bash
# Application
APP_NAME="My API"
APP_ENV=production

# Database
DATABASE__URL=postgresql+asyncpg://user:pass@db:5432/api

# Security (generate with: python -c "import secrets; print(secrets.token_urlsafe(64))")
SECURITY__SECRET_KEY="your-64-char-secret-key-here"
SECURITY__CORS_ORIGINS=["https://app.example.com"]

# Redis
REDIS__URL=redis://redis:6379/0
REDIS__ENABLED=true

# Observability
OBSERVABILITY__LOG_LEVEL=INFO
OBSERVABILITY__LOG_FORMAT=json
```
