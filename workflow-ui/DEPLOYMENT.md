# Deployment Guide

This guide covers deploying the Workflow Management UI to various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Build Process](#build-process)
- [Docker Deployment](#docker-deployment)
- [Manual Deployment](#manual-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Node.js 20.19+ or 22.12+
- Docker and Docker Compose (for containerized deployment)
- nginx (for manual deployment)

## Environment Configuration

### Environment Variables

Create environment-specific `.env` files:

**Development (.env.development)**
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_POLLING_INTERVAL=1000
VITE_APP_NAME=Workflow Manager (Dev)
```

**Staging (.env.staging)**
```env
VITE_API_URL=https://staging-api.example.com/api/v1
VITE_POLLING_INTERVAL=2000
VITE_APP_NAME=Workflow Manager (Staging)
```

**Production (.env.production)**
```env
VITE_API_URL=https://api.example.com/api/v1
VITE_POLLING_INTERVAL=3000
VITE_APP_NAME=Workflow Manager
```

## Build Process

### Using Build Script

The `build.sh` script handles environment-specific builds:

```bash
# Development build
./build.sh development

# Staging build
./build.sh staging

# Production build
./build.sh production
```

The script will:
1. Set environment variables
2. Install dependencies (if needed)
3. Run type checking
4. Run linting
5. Run tests
6. Build the application

### Manual Build

```bash
# Install dependencies
npm ci

# Run quality checks
npm run type-check
npm run lint
npm test

# Build
npm run build
```

The built files will be in the `dist/` directory.

## Docker Deployment

### Using Docker Compose

1. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Deploy**:
   ```bash
   ./deploy.sh
   ```

   Or manually:
   ```bash
   docker-compose up -d
   ```

3. **Check status**:
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

4. **Stop**:
   ```bash
   docker-compose down
   ```

### Using Docker Only

```bash
# Build image
docker build -t workflow-ui:latest .

# Run container
docker run -d \
  --name workflow-ui \
  -p 3000:80 \
  -e VITE_API_URL=http://localhost:8000/api/v1 \
  workflow-ui:latest

# Check logs
docker logs -f workflow-ui

# Stop container
docker stop workflow-ui
docker rm workflow-ui
```

## Manual Deployment

### With nginx

1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Copy files to web server**:
   ```bash
   sudo cp -r dist/* /var/www/workflow-ui/
   ```

3. **Configure nginx**:
   ```bash
   sudo cp nginx.conf /etc/nginx/sites-available/workflow-ui
   sudo ln -s /etc/nginx/sites-available/workflow-ui /etc/nginx/sites-enabled/
   ```

4. **Update nginx configuration** (`/etc/nginx/sites-available/workflow-ui`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       root /var/www/workflow-ui;
       
       # Include the rest from nginx.conf
       include /path/to/nginx.conf;
   }
   ```

5. **Test and reload nginx**:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### With Apache

1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Copy files**:
   ```bash
   sudo cp -r dist/* /var/www/html/workflow-ui/
   ```

3. **Create `.htaccess`** in `/var/www/html/workflow-ui/`:
   ```apache
   <IfModule mod_rewrite.c>
     RewriteEngine On
     RewriteBase /workflow-ui/
     RewriteRule ^index\.html$ - [L]
     RewriteCond %{REQUEST_FILENAME} !-f
     RewriteCond %{REQUEST_FILENAME} !-d
     RewriteRule . /workflow-ui/index.html [L]
   </IfModule>
   ```

4. **Enable mod_rewrite**:
   ```bash
   sudo a2enmod rewrite
   sudo systemctl restart apache2
   ```

## Cloud Deployment

### AWS S3 + CloudFront

1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Create S3 bucket**:
   ```bash
   aws s3 mb s3://workflow-ui-bucket
   ```

3. **Upload files**:
   ```bash
   aws s3 sync dist/ s3://workflow-ui-bucket --delete
   ```

4. **Configure S3 for static website hosting**:
   - Enable static website hosting
   - Set index document to `index.html`
   - Set error document to `index.html` (for SPA routing)

5. **Create CloudFront distribution**:
   - Origin: S3 bucket
   - Default root object: `index.html`
   - Error pages: 404 → /index.html (200)

### Vercel

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Deploy**:
   ```bash
   vercel
   ```

3. **Set environment variables** in Vercel dashboard

### Netlify

1. **Install Netlify CLI**:
   ```bash
   npm i -g netlify-cli
   ```

2. **Deploy**:
   ```bash
   netlify deploy --prod
   ```

3. **Configure redirects** (create `public/_redirects`):
   ```
   /*    /index.html   200
   ```

### Google Cloud Platform (GCP)

1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Create Cloud Storage bucket**:
   ```bash
   gsutil mb gs://workflow-ui-bucket
   ```

3. **Upload files**:
   ```bash
   gsutil -m rsync -r -d dist/ gs://workflow-ui-bucket
   ```

4. **Configure bucket for web hosting**:
   ```bash
   gsutil web set -m index.html -e index.html gs://workflow-ui-bucket
   ```

## Monitoring

### Health Checks

The application includes a health check endpoint at `/health`:

```bash
curl http://your-domain.com/health
# Response: healthy
```

### Docker Health Check

Docker automatically monitors container health:

```bash
docker inspect --format='{{.State.Health.Status}}' workflow-ui
```

### Logging

**Docker logs**:
```bash
docker-compose logs -f workflow-ui
```

**nginx logs**:
```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Performance Monitoring

Monitor key metrics:
- Page load time
- API response times
- Error rates
- Resource usage (CPU, memory)

Use tools like:
- Google Analytics
- Sentry for error tracking
- New Relic or Datadog for APM

## Troubleshooting

### Build Fails

**Issue**: Build fails with errors

**Solutions**:
- Check Node.js version: `node --version`
- Clear cache: `rm -rf node_modules dist .vite`
- Reinstall dependencies: `npm ci`
- Check for TypeScript errors: `npm run type-check`

### Container Won't Start

**Issue**: Docker container exits immediately

**Solutions**:
- Check logs: `docker-compose logs`
- Verify Dockerfile syntax
- Ensure nginx.conf is valid
- Check port conflicts: `lsof -i :3000`

### 404 Errors on Refresh

**Issue**: Page refreshes result in 404 errors

**Solutions**:
- Verify nginx configuration includes SPA routing
- Check `try_files` directive in nginx.conf
- For Apache, ensure `.htaccess` is configured correctly
- For cloud deployments, configure redirect rules

### API Connection Issues

**Issue**: Frontend can't connect to backend API

**Solutions**:
- Verify `VITE_API_URL` is correct
- Check CORS configuration on backend
- Ensure API is accessible from frontend host
- Check network/firewall rules
- Verify SSL certificates (for HTTPS)

### Performance Issues

**Issue**: Application is slow

**Solutions**:
- Enable gzip compression in nginx
- Configure proper caching headers
- Use CDN for static assets
- Optimize images and assets
- Check API response times

### SSL/HTTPS Issues

**Issue**: SSL certificate errors

**Solutions**:
- Verify certificate is valid and not expired
- Check certificate chain is complete
- Ensure nginx SSL configuration is correct
- Use Let's Encrypt for free certificates:
  ```bash
  sudo certbot --nginx -d your-domain.com
  ```

## Security Best Practices

1. **Use HTTPS** in production
2. **Set security headers** (already configured in nginx.conf)
3. **Keep dependencies updated**: `npm audit fix`
4. **Use environment variables** for sensitive data
5. **Implement rate limiting** on API endpoints
6. **Regular security audits**: `npm audit`
7. **Monitor for vulnerabilities**: Use Snyk or Dependabot

## Rollback Procedure

### Docker Deployment

```bash
# List images
docker images workflow-ui

# Tag current version before deploying
docker tag workflow-ui:latest workflow-ui:backup

# If deployment fails, rollback
docker-compose down
docker tag workflow-ui:backup workflow-ui:latest
docker-compose up -d
```

### Manual Deployment

```bash
# Keep backup of previous version
sudo cp -r /var/www/workflow-ui /var/www/workflow-ui.backup

# If deployment fails, restore
sudo rm -rf /var/www/workflow-ui
sudo mv /var/www/workflow-ui.backup /var/www/workflow-ui
sudo systemctl reload nginx
```

## Continuous Deployment

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Run tests
        run: npm test
        
      - name: Build
        run: npm run build
        env:
          VITE_API_URL: ${{ secrets.API_URL }}
          
      - name: Deploy to production
        run: |
          # Add your deployment commands here
```

## Support

For issues or questions:
- Check the [main README](README.md)
- Review [troubleshooting section](#troubleshooting)
- Check application logs
- Contact the development team
