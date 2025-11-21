# CI/CD Setup - GitHub Actions

This document explains the automated CI/CD pipeline for building and publishing Docker images.

## Overview

The project uses GitHub Actions to automatically build and push Docker images to GitHub Container Registry (GHCR) whenever code is pushed to the `main` or `master` branch.

## Workflow Features

### 🚀 Automatic Triggers
- **Push to main/master**: Automatically builds and publishes images
- **Manual trigger**: Can be triggered manually with custom version
- **Smart ignoring**: Skips builds for documentation-only changes

### 📦 Images Built
The workflow builds and publishes 5 Docker images:

1. **orchestrator-api** - FastAPI Workflow Management API
2. **orchestrator-executor** - Centralized Executor
3. **orchestrator-bridge** - HTTP-Kafka Bridge
4. **orchestrator-consumer** - Execution Consumer
5. **orchestrator-ui** - React UI

**Note:** The mock-agent image is not published as it's only needed for local testing.

### 🏷️ Tagging Strategy

Each image is tagged with:
- `latest` - Always points to the most recent build
- `v{version}` - Semantic version (e.g., `v1.2.3`)
- `{branch}-{sha}` - Branch name with commit SHA
- `{branch}` - Branch name

### 📈 Version Management

**Automatic Version Bumping:**
- Reads the latest Git tag (e.g., `v1.2.3`)
- Automatically increments the patch version (e.g., `v1.2.4`)
- Creates a new Git tag
- Creates a GitHub Release with release notes

**Manual Version:**
- Can be specified when manually triggering the workflow
- Useful for major/minor version bumps

## Setup Instructions

### 1. Enable GitHub Container Registry

GHCR is automatically enabled for your repository. No additional setup needed!

### 2. Configure Repository Settings

1. Go to your repository settings
2. Navigate to **Actions** → **General**
3. Under **Workflow permissions**, ensure:
   - ✅ Read and write permissions
   - ✅ Allow GitHub Actions to create and approve pull requests

### 3. Make Images Public (Optional)

By default, images are private. To make them public:

1. Go to your GitHub profile
2. Click **Packages**
3. Select the package (e.g., `orchestrator-api`)
4. Click **Package settings**
5. Scroll to **Danger Zone**
6. Click **Change visibility** → **Public**

Repeat for all 6 images.

## Usage

### Automatic Build (Push to main/master)

Simply push your code to the main or master branch:

```bash
git add .
git commit -m "feat: add new feature"
git push origin main
```

The workflow will:
1. ✅ Calculate the next version (auto-increment patch)
2. ✅ Build all 6 Docker images
3. ✅ Push images to GHCR with multiple tags
4. ✅ Create a Git tag
5. ✅ Create a GitHub Release
6. ✅ Update `docker-compose.prod.yml`

### Manual Build with Custom Version

1. Go to **Actions** tab in your repository
2. Select **Build and Push Docker Images**
3. Click **Run workflow**
4. Enter custom version (e.g., `2.0.0`)
5. Click **Run workflow**

### Pull Images

After the workflow completes, pull images:

```bash
# Pull latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-api:latest

# Pull specific version
docker pull ghcr.io/YOUR_USERNAME/orchestrator-api:v1.2.3

# Pull all services
docker pull ghcr.io/YOUR_USERNAME/orchestrator-api:latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-executor:latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-bridge:latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-consumer:latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-ui:latest
```

### Use in Production

The workflow automatically creates/updates `docker-compose.prod.yml` with the latest version:

```bash
# Use production images
docker-compose -f docker-compose.prod.yml up -d
```

## Workflow Details

### Jobs

#### 1. **prepare**
- Calculates the next version number
- Outputs version for other jobs

#### 2. **build-and-push**
- Builds all 6 Docker images in parallel
- Uses Docker Buildx for multi-platform builds (amd64, arm64)
- Pushes to GitHub Container Registry
- Uses layer caching for faster builds

#### 3. **create-release**
- Creates a Git tag
- Generates release notes
- Creates a GitHub Release

#### 4. **update-docker-compose**
- Updates `docker-compose.prod.yml` with new version
- Commits and pushes the change

### Build Optimization

- **Multi-platform**: Builds for both `linux/amd64` and `linux/arm64`
- **Layer caching**: Uses GitHub Actions cache for faster builds
- **Parallel builds**: All images build simultaneously
- **Fail-fast disabled**: One image failure doesn't stop others

## Environment Variables

The workflow uses these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `REGISTRY` | Container registry URL | `ghcr.io` |
| `IMAGE_PREFIX` | Image name prefix | `{owner}/orchestrator` |

## Secrets

The workflow uses these secrets (automatically provided by GitHub):

| Secret | Description |
|--------|-------------|
| `GITHUB_TOKEN` | Automatically provided by GitHub Actions |

No manual secret configuration needed!

## Monitoring

### View Workflow Runs

1. Go to **Actions** tab
2. Click on a workflow run
3. View logs for each job

### Check Published Images

1. Go to your GitHub profile
2. Click **Packages**
3. View all published images and versions

### View Releases

1. Go to **Releases** in your repository
2. See all versions with release notes

## Troubleshooting

### Build Fails

**Check logs:**
1. Go to Actions tab
2. Click on failed workflow
3. Expand failed job
4. Review error messages

**Common issues:**
- **Dockerfile not found**: Check `dockerfile` path in workflow
- **Build context error**: Verify `context` path in workflow
- **Permission denied**: Check repository workflow permissions

### Images Not Visible

**Make images public:**
1. Go to Packages
2. Select package
3. Package settings → Change visibility → Public

### Version Conflict

**If tag already exists:**
```bash
# Delete local tag
git tag -d v1.2.3

# Delete remote tag
git push origin :refs/tags/v1.2.3

# Re-run workflow
```

### Authentication Issues

**If push fails:**
1. Check repository settings → Actions → Workflow permissions
2. Ensure "Read and write permissions" is enabled
3. Re-run workflow

## Best Practices

### 1. Semantic Versioning

Follow semantic versioning:
- **Major** (v2.0.0): Breaking changes
- **Minor** (v1.2.0): New features, backward compatible
- **Patch** (v1.2.3): Bug fixes

### 2. Release Notes

The workflow auto-generates release notes. For better notes:
- Use conventional commits (feat:, fix:, chore:)
- Write clear commit messages
- Group related changes

### 3. Testing Before Release

Test locally before pushing:
```bash
# Build locally
docker-compose build

# Test services
docker-compose up -d
./scripts/test_circuit_breaker_simple.sh

# If tests pass, push
git push origin main
```

### 4. Rollback Strategy

If a release has issues:

```bash
# Revert to previous version
docker-compose -f docker-compose.prod.yml down
docker pull ghcr.io/YOUR_USERNAME/orchestrator-api:v1.2.2
docker-compose -f docker-compose.prod.yml up -d
```

### 5. Monitor First Deploy

After pushing to main:
1. Watch the Actions tab
2. Verify all jobs complete successfully
3. Check that images are published
4. Test pulling and running images

## Advanced Configuration

### Custom Image Names

Edit `.github/workflows/build-and-push-images.yml`:

```yaml
env:
  IMAGE_PREFIX: your-org/your-project
```

### Add More Images

Add to the matrix in the workflow:

```yaml
matrix:
  include:
    - service: new-service
      dockerfile: Dockerfile.new-service
      context: .
```

### Change Version Strategy

Modify the version calculation in the `prepare` job:

```yaml
# For minor version bump
MINOR=$((MINOR + 1))
PATCH=0
VERSION="$MAJOR.$MINOR.$PATCH"
```

### Skip CI for Specific Commits

Add to commit message:
```bash
git commit -m "docs: update README [skip ci]"
```

## Integration with Deployment

### Kubernetes

Use the versioned images in your Kubernetes manifests:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: workflow-api
spec:
  template:
    spec:
      containers:
      - name: api
        image: ghcr.io/YOUR_USERNAME/orchestrator-api:v1.2.3
```

### Docker Swarm

Use in stack file:

```yaml
version: '3.8'
services:
  api:
    image: ghcr.io/YOUR_USERNAME/orchestrator-api:v1.2.3
    deploy:
      replicas: 3
```

### Watchtower (Auto-updates)

Use Watchtower to automatically update containers:

```bash
docker run -d \
  --name watchtower \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower \
  --interval 300
```

## Security Considerations

### 1. Image Scanning

Consider adding vulnerability scanning:

```yaml
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ghcr.io/${{ env.IMAGE_PREFIX }}-${{ matrix.service }}:latest
```

### 2. Sign Images

Consider signing images with Cosign:

```yaml
- name: Sign image
  uses: sigstore/cosign-installer@main
- run: cosign sign ghcr.io/${{ env.IMAGE_PREFIX }}-${{ matrix.service }}:latest
```

### 3. Private Images

Keep images private for sensitive applications:
- Don't change visibility to public
- Use GitHub tokens for pulling in production

## Support

For issues with the CI/CD pipeline:
1. Check workflow logs in Actions tab
2. Review this documentation
3. Check GitHub Actions documentation
4. Open an issue in the repository

## Next Steps

After setting up CI/CD:
1. ✅ Push code to trigger first build
2. ✅ Verify images are published
3. ✅ Test pulling and running images
4. ✅ Set up production deployment
5. ✅ Configure monitoring and alerts
