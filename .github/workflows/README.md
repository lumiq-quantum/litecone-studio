# GitHub Actions Workflows

This directory contains automated CI/CD workflows for the project.

## Available Workflows

### 🐳 Build and Push Docker Images

**File:** `build-and-push-images.yml`

**Purpose:** Automatically builds and publishes Docker images to GitHub Container Registry.

**Triggers:**
- Push to `main` or `master` branch
- Manual trigger via GitHub Actions UI

**What it does:**
1. Calculates next version (auto-increments patch version)
2. Builds 5 Docker images in parallel:
   - orchestrator-api
   - orchestrator-executor
   - orchestrator-bridge
   - orchestrator-consumer
   - orchestrator-ui
3. Pushes images to GHCR with multiple tags (latest, version, sha)
4. Creates Git tag and GitHub Release
5. Updates docker-compose.prod.yml

**Note:** Mock agent is built locally only, not published to registry.

**Images published to:**
```
ghcr.io/{owner}/orchestrator-api:latest
ghcr.io/{owner}/orchestrator-executor:latest
ghcr.io/{owner}/orchestrator-bridge:latest
ghcr.io/{owner}/orchestrator-consumer:latest
ghcr.io/{owner}/orchestrator-ui:latest
ghcr.io/{owner}/orchestrator-mock-agent:latest
```

## Setup

### First Time Setup

1. **Initialize version tags:**
   ```bash
   ./scripts/init-version.sh
   ```

2. **Configure repository permissions:**
   - Go to Settings → Actions → General
   - Enable "Read and write permissions"
   - Enable "Allow GitHub Actions to create and approve pull requests"

3. **Make images public (optional):**
   - Go to your profile → Packages
   - Select each package
   - Change visibility to Public

### Trigger Automatic Build

Simply push to main/master:
```bash
git add .
git commit -m "feat: add new feature"
git push origin main
```

### Trigger Manual Build

1. Go to Actions tab
2. Select "Build and Push Docker Images"
3. Click "Run workflow"
4. Optionally specify custom version
5. Click "Run workflow"

## Monitoring

### View Workflow Status

- **Actions Tab:** See all workflow runs and their status
- **Commit Status:** Green checkmark on commits indicates successful build
- **Packages:** View published images in your profile

### Workflow Logs

1. Go to Actions tab
2. Click on a workflow run
3. Click on a job to see detailed logs
4. Expand steps to see command output

## Version Management

### Automatic Versioning

The workflow automatically:
- Reads the latest Git tag (e.g., `v1.2.3`)
- Increments patch version (e.g., `v1.2.4`)
- Creates new tag and release

### Manual Version Bump

For major/minor version bumps:

1. **Via workflow input:**
   - Trigger manually
   - Enter version like `2.0.0`

2. **Via Git tag:**
   ```bash
   git tag -a v2.0.0 -m "Release v2.0.0"
   git push origin v2.0.0
   ```

### Version Format

Follow semantic versioning:
- **Major** (v2.0.0): Breaking changes
- **Minor** (v1.2.0): New features
- **Patch** (v1.2.3): Bug fixes

## Image Tags

Each image gets multiple tags:

| Tag | Description | Example |
|-----|-------------|---------|
| `latest` | Most recent build | `orchestrator-api:latest` |
| `{version}` | Semantic version | `orchestrator-api:1.2.3` |
| `{branch}-{sha}` | Branch + commit | `orchestrator-api:main-abc1234` |
| `{branch}` | Branch name | `orchestrator-api:main` |

## Using Published Images

### Pull Images

```bash
# Pull latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-api:latest

# Pull specific version
docker pull ghcr.io/YOUR_USERNAME/orchestrator-api:v1.2.3
```

### Use in docker-compose

The workflow automatically updates `docker-compose.prod.yml`:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Use in Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: api
        image: ghcr.io/YOUR_USERNAME/orchestrator-api:v1.2.3
```

## Troubleshooting

### Build Fails

**Check the logs:**
1. Go to Actions tab
2. Click failed workflow
3. Review error messages

**Common issues:**
- Missing dependencies in Dockerfile
- Build context path incorrect
- Insufficient permissions

### Images Not Visible

**Solution:**
1. Go to Packages in your profile
2. Select the package
3. Package settings → Change visibility → Public

### Permission Errors

**Solution:**
1. Settings → Actions → General
2. Enable "Read and write permissions"
3. Re-run workflow

### Version Conflicts

**If tag exists:**
```bash
# Delete tag
git tag -d v1.2.3
git push origin :refs/tags/v1.2.3

# Re-run workflow
```

## Best Practices

### 1. Test Before Pushing

```bash
# Build locally first
docker-compose build

# Test services
docker-compose up -d
./scripts/test_circuit_breaker_simple.sh

# If tests pass, push
git push origin main
```

### 2. Use Conventional Commits

```bash
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug"
git commit -m "chore: update dependencies"
```

### 3. Skip CI When Needed

```bash
git commit -m "docs: update README [skip ci]"
```

### 4. Monitor First Build

After setup:
1. Watch Actions tab during first build
2. Verify all jobs succeed
3. Check images are published
4. Test pulling images

### 5. Version Strategy

- **Patch**: Bug fixes, small changes
- **Minor**: New features, backward compatible
- **Major**: Breaking changes

## Advanced

### Add New Image

Edit `build-and-push-images.yml`:

```yaml
matrix:
  include:
    - service: new-service
      dockerfile: Dockerfile.new-service
      context: .
```

### Multi-Platform Builds

Already configured for:
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM)

### Build Caching

Uses GitHub Actions cache for faster builds:
- Layer caching enabled
- Reuses unchanged layers
- Significantly faster rebuilds

### Custom Registry

To use a different registry, edit:

```yaml
env:
  REGISTRY: your-registry.com
  IMAGE_PREFIX: your-org/your-project
```

## Security

### Image Scanning

Consider adding Trivy scanning:

```yaml
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-${{ matrix.service }}:latest
```

### Image Signing

Consider signing with Cosign:

```yaml
- name: Sign image
  uses: sigstore/cosign-installer@main
- run: cosign sign ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-${{ matrix.service }}:latest
```

## Documentation

For detailed information, see:
- [CI/CD Setup Guide](../../docs/deployment/CICD_SETUP.md)
- [Deployment Guide](../../docs/deployment/DEPLOYMENT_GUIDE.md)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Support

For issues:
1. Check workflow logs
2. Review this documentation
3. Check [CI/CD Setup Guide](../../docs/deployment/CICD_SETUP.md)
4. Open an issue in the repository
