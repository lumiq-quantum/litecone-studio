# Environment Variables Reference

Complete reference for all environment variables used by the Workflow Management API.

## Quick Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ Yes | - | PostgreSQL connection string |
| `KAFKA_BROKERS` | ✅ Yes | - | Kafka broker addresses |
| `API_HOST` | No | `0.0.0.0` | Host to bind to |
| `API_PORT` | No | `8000` | Port to listen on |
| `API_WORKERS` | No | `1` | Number of worker processes |
| `JWT_SECRET` | No | `dev-secret-key` | JWT signing secret |
| `LOG_LEVEL` | No | `INFO` | Logging level |

## Detailed Reference

### Application Settings

#### `API_TITLE`
- **Type:** String
- **Required:** No
- **Default:** `Workflow Management API`
- **Description:** API title displayed in documentation
- **Example:** `My Workflow API`

#### `API_VERSION`
- **Type:** String
- **Required:** No
- **Default:** `1.0.0`
- **Description:** API version displayed in documentation
- **Example:** `2.0.0`

#### `API_DESCRIPTION`
- **Type:** String
- **Required:** No
- **Default:** `REST API for managing workflow orchestration`
- **Description:** API description displayed in documentation
- **Example:** `Production Workflow Management System`

#### `API_PREFIX`
- **Type:** String
- **Required:** No
- **Default:** `/api/v1`
- **Description:** URL prefix for all API routes
- **Example:** `/api/v2`, `/v1`
- **Note:** Must start with `/`

#### `API_HOST`
- **Type:** String
- **Required:** No
- **Default:** `0.0.0.0`
- **Description:** Host address to bind the server to
- **Example:** `127.0.0.1` (localhost only), `0.0.0.0` (all interfaces)
- **Production:** Use `0.0.0.0` to accept connections from all interfaces

#### `API_PORT`
- **Type:** Integer
- **Required:** No
- **Default:** `8000`
- **Description:** Port number to listen on
- **Example:** `8080`, `3000`
- **Range:** 1-65535

#### `API_RELOAD`
- **Type:** Boolean
- **Required:** No
- **Default:** `false`
- **Description:** Enable auto-reload on code changes (development only)
- **Example:** `true`, `false`
- **Production:** Must be `false`

#### `API_WORKERS`
- **Type:** Integer
- **Required:** No
- **Default:** `1`
- **Description:** Number of worker processes
- **Example:** `4`, `8`
- **Recommendation:** `(2 x CPU cores) + 1`
- **Production:** Set to 4 or higher based on CPU cores

---

### Database Configuration

#### `DATABASE_URL`
- **Type:** String (URL)
- **Required:** ✅ Yes
- **Default:** None
- **Description:** PostgreSQL connection string
- **Format:** `postgresql://[user]:[password]@[host]:[port]/[database]`
- **Example:** `postgresql://workflow_user:password@localhost:5432/workflow_db`
- **SSL Example:** `postgresql://user:pass@host:5432/db?sslmode=require`
- **Note:** Must be a valid PostgreSQL connection URL

#### `DATABASE_POOL_SIZE`
- **Type:** Integer
- **Required:** No
- **Default:** `10`
- **Description:** Number of connections to maintain in the pool
- **Example:** `20`, `30`
- **Recommendation:** `workers * 2`
- **Range:** 5-100

#### `DATABASE_MAX_OVERFLOW`
- **Type:** Integer
- **Required:** No
- **Default:** `20`
- **Description:** Maximum number of connections that can be created beyond pool_size
- **Example:** `40`, `60`
- **Recommendation:** `pool_size * 2`
- **Range:** 10-200

#### `DATABASE_ECHO`
- **Type:** Boolean
- **Required:** No
- **Default:** `false`
- **Description:** Log all SQL queries (for debugging)
- **Example:** `true`, `false`
- **Production:** Must be `false` (performance impact)
- **Development:** Can be `true` for debugging

---

### Kafka Configuration

#### `KAFKA_BROKERS`
- **Type:** String (comma-separated)
- **Required:** ✅ Yes
- **Default:** None
- **Description:** Kafka broker addresses
- **Format:** `host:port[,host:port,...]`
- **Example:** `localhost:9092`
- **Multiple:** `kafka-1:9092,kafka-2:9092,kafka-3:9092`
- **Note:** Must be reachable from the API container

#### `KAFKA_EXECUTION_TOPIC`
- **Type:** String
- **Required:** No
- **Default:** `workflow.execution.requests`
- **Description:** Kafka topic for workflow execution requests
- **Example:** `prod.workflow.execution`, `dev.workflow.execution`
- **Note:** Topic must exist or auto-creation must be enabled

#### `KAFKA_CANCELLATION_TOPIC`
- **Type:** String
- **Required:** No
- **Default:** `workflow.cancellation.requests`
- **Description:** Kafka topic for workflow cancellation requests
- **Example:** `prod.workflow.cancellation`, `dev.workflow.cancellation`
- **Note:** Topic must exist or auto-creation must be enabled

---

### Authentication Settings

#### `JWT_SECRET`
- **Type:** String
- **Required:** No (but recommended for production)
- **Default:** `dev-secret-key-change-in-production`
- **Description:** Secret key for signing JWT tokens
- **Example:** `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6`
- **Minimum Length:** 32 characters
- **Production:** ⚠️ Must be changed to a strong random value
- **Generate:** `openssl rand -hex 32` or `python -c "import secrets; print(secrets.token_hex(32))"`

#### `JWT_ALGORITHM`
- **Type:** String
- **Required:** No
- **Default:** `HS256`
- **Description:** Algorithm used for JWT signing
- **Example:** `HS256`, `HS512`
- **Allowed:** `HS256`, `HS384`, `HS512`
- **Production:** Use `HS256` (recommended)

#### `JWT_EXPIRATION_MINUTES`
- **Type:** Integer
- **Required:** No
- **Default:** `60`
- **Description:** JWT token expiration time in minutes
- **Example:** `30` (30 minutes), `1440` (24 hours)
- **Range:** 5-10080 (1 week)
- **Production:** 60-120 minutes recommended

#### `API_KEY_HEADER`
- **Type:** String
- **Required:** No
- **Default:** `X-API-Key`
- **Description:** HTTP header name for API key authentication
- **Example:** `X-API-Key`, `X-Custom-API-Key`
- **Note:** Must be a valid HTTP header name

---

### CORS Settings

#### `CORS_ORIGINS`
- **Type:** String (comma-separated)
- **Required:** No
- **Default:** `http://localhost:3000`
- **Description:** Allowed CORS origins
- **Format:** `origin[,origin,...]`
- **Example:** `https://app.example.com,https://admin.example.com`
- **Development:** `http://localhost:3000,http://localhost:8080`
- **Production:** ⚠️ Never use `*` - specify exact domains
- **Note:** Must include protocol (http/https)

#### `CORS_ALLOW_CREDENTIALS`
- **Type:** Boolean
- **Required:** No
- **Default:** `true`
- **Description:** Allow credentials (cookies, authorization headers) in CORS requests
- **Example:** `true`, `false`
- **Production:** `true` if using authentication

#### `CORS_ALLOW_METHODS`
- **Type:** String (comma-separated)
- **Required:** No
- **Default:** `*`
- **Description:** Allowed HTTP methods for CORS
- **Example:** `GET,POST,PUT,DELETE,PATCH`
- **Production:** Specify exact methods instead of `*`

#### `CORS_ALLOW_HEADERS`
- **Type:** String (comma-separated)
- **Required:** No
- **Default:** `*`
- **Description:** Allowed HTTP headers for CORS
- **Example:** `Content-Type,Authorization,X-API-Key`
- **Production:** Specify exact headers instead of `*`

---

### Logging Configuration

#### `LOG_LEVEL`
- **Type:** String
- **Required:** No
- **Default:** `INFO`
- **Description:** Minimum logging level
- **Allowed:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Development:** `DEBUG` or `INFO`
- **Production:** `INFO` or `WARNING`
- **Note:** Case-insensitive

#### `LOG_FORMAT`
- **Type:** String
- **Required:** No
- **Default:** `json`
- **Description:** Log output format
- **Allowed:** `json`, `text`
- **Development:** `text` (more readable)
- **Production:** `json` (easier to parse)

---

### Pagination Settings

#### `DEFAULT_PAGE_SIZE`
- **Type:** Integer
- **Required:** No
- **Default:** `20`
- **Description:** Default number of items per page
- **Example:** `10`, `50`
- **Range:** 1-1000
- **Recommendation:** 20-50

#### `MAX_PAGE_SIZE`
- **Type:** Integer
- **Required:** No
- **Default:** `100`
- **Description:** Maximum allowed items per page
- **Example:** `50`, `200`
- **Range:** 1-1000
- **Note:** Must be >= DEFAULT_PAGE_SIZE

---

### Feature Flags

#### `ENABLE_METRICS`
- **Type:** Boolean
- **Required:** No
- **Default:** `true`
- **Description:** Enable Prometheus metrics endpoint
- **Example:** `true`, `false`
- **Production:** `true` (recommended for monitoring)

#### `ENABLE_AUDIT_LOGGING`
- **Type:** Boolean
- **Required:** No
- **Default:** `true`
- **Description:** Enable audit logging for all actions
- **Example:** `true`, `false`
- **Production:** `true` (recommended for compliance)

---

## Environment File Examples

### Development (.env.api)

```bash
# Application
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
API_WORKERS=1

# Database
DATABASE_URL=postgresql://workflow_user:workflow_pass@localhost:5432/workflow_db
DATABASE_ECHO=true

# Kafka
KAFKA_BROKERS=localhost:9092

# Authentication
JWT_SECRET=dev-secret-key-change-in-production

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=text
```

### Production (.env.api.production)

```bash
# Application
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
API_WORKERS=8

# Database
DATABASE_URL=postgresql://prod_user:STRONG_PASSWORD@db-host:5432/workflow_prod?sslmode=require
DATABASE_POOL_SIZE=30
DATABASE_MAX_OVERFLOW=60
DATABASE_ECHO=false

# Kafka
KAFKA_BROKERS=kafka-1:9092,kafka-2:9092,kafka-3:9092
KAFKA_EXECUTION_TOPIC=prod.workflow.execution.requests
KAFKA_CANCELLATION_TOPIC=prod.workflow.cancellation.requests

# Authentication (CHANGE THESE!)
JWT_SECRET=GENERATE_STRONG_RANDOM_SECRET_MIN_32_CHARS
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# CORS (restrict to your domains)
CORS_ORIGINS=https://app.example.com,https://admin.example.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,PATCH
CORS_ALLOW_HEADERS=Content-Type,Authorization,X-API-Key

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Features
ENABLE_METRICS=true
ENABLE_AUDIT_LOGGING=true
```

---

## Validation

### Required Variables Check

Before starting the API, ensure these required variables are set:

```bash
# Check required variables
echo "DATABASE_URL: ${DATABASE_URL:?'DATABASE_URL is required'}"
echo "KAFKA_BROKERS: ${KAFKA_BROKERS:?'KAFKA_BROKERS is required'}"
```

### Production Checklist

- [ ] `DATABASE_URL` uses strong password
- [ ] `DATABASE_URL` uses SSL (`?sslmode=require`)
- [ ] `JWT_SECRET` is changed from default
- [ ] `JWT_SECRET` is at least 32 characters
- [ ] `CORS_ORIGINS` specifies exact domains (not `*`)
- [ ] `API_RELOAD` is set to `false`
- [ ] `API_WORKERS` is set to 4 or higher
- [ ] `LOG_LEVEL` is `INFO` or `WARNING`
- [ ] `LOG_FORMAT` is `json`
- [ ] `DATABASE_ECHO` is `false`

---

## Security Notes

1. **Never commit `.env` files to version control**
   - Add to `.gitignore`
   - Use `.env.example` as template

2. **Use strong secrets in production**
   - Generate with `openssl rand -hex 32`
   - Minimum 32 characters
   - Use different secrets per environment

3. **Restrict CORS origins**
   - Never use `*` in production
   - Specify exact domains with protocol

4. **Use SSL for database connections**
   - Add `?sslmode=require` to DATABASE_URL
   - Use certificate verification in production

5. **Rotate secrets regularly**
   - Change JWT_SECRET periodically
   - Update API keys regularly
   - Use secret management tools (Vault, AWS Secrets Manager)

---

## Troubleshooting

### Variable Not Being Read

1. Check file name: `.env.api` (not `.env.api.txt`)
2. Check file location: Same directory as `docker-compose.yml`
3. Check syntax: `KEY=value` (no spaces around `=`)
4. Restart containers: `docker-compose restart api`

### Invalid Value Error

1. Check data type (string, integer, boolean)
2. Check allowed values (e.g., LOG_LEVEL must be DEBUG/INFO/WARNING/ERROR/CRITICAL)
3. Check format (e.g., DATABASE_URL must be valid PostgreSQL URL)

### Variable Not Taking Effect

1. Environment variables in `docker-compose.yml` override `.env` file
2. Check `docker-compose exec api env` to see actual values
3. Restart container after changing variables

---

## Additional Resources

- [Deployment Guide](./DEPLOYMENT.md)
- [API Documentation](./API_DOCUMENTATION.md)
- [Database Setup](./DATABASE_SETUP.md)
