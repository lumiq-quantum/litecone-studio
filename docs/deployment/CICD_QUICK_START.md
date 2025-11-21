# CI/CD Quick Start Guide

Get your automated Docker image builds up and running in 5 minutes!

## 🚀 Quick Setup (3 Steps)

### Step 1: Initialize Version Tag

```bash
./scripts/init-version.sh
```

This creates your first version tag (e.g., `v0.1.0`).

### Step 2: Configure GitHub Repository

1. Go to your repository **Settings**
2. Navigate to **Actions** → **General**
3. Under **Workflow permissions**:
   - ✅ Select "Read and write permissions"
   - ✅ Check "Allow GitHub Actions to create and approve pull requests"
4. Click **Save**

### Step 3: Push to Main Branch

```bash
git add .
git commit -m "feat: enable CI/CD pipeline"
git push origin main
```

**That's it!** 🎉 The workflow will automatically:
- Build all 5 Docker images
- Push to GitHub Container Registry
- Create a new version tag (v0.1.1)
- Create a GitHub Release

## 📦 What Gets Built

| Image | Purpose |
|-------|---------|
| `orchestrator-api` | REST API service |
| `orchestrator-executor` | Workflow executor |
| `orchestrator-bridge` | HTTP-Kafka bridge |
| `orchestrator-consumer` | Execution consumer |
| `orchestrator-ui` | React web interface |

**Note:** Mock agent is built locally only, not published to registry.

## 🏷️ Image Tags

Each image gets tagged with:
- `latest` - Always the newest version
- `v1.2.3` - Specific version number
- `main-abc1234` - Branch + commit SHA

## 📍 Where to Find Images

After the workflow completes:

```bash
# View in GitHub
https://github.com/YOUR_USERNAME?tab=packages

# Pull images
docker pull ghcr.io/YOUR_USERNAME/orchestrator-api:latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-executor:latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-bridge:latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-consumer:latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-ui:latest
```

## 🔄 How It Works

### Automatic Builds (Every Push)

```
Push to main → Build images → Tag version → Create release
```

**Version bumping:**
- Current: `v1.2.3`
- Next: `v1.2.4` (auto-increments patch)

### Manual Builds (Custom Version)

1. Go to **Actions** tab
2. Click **Build and Push Docker Images**
3. Click **Run workflow**
4. Enter version (e.g., `2.0.0`)
5. Click **Run workflow**

## 📊 Monitor Progress

### View Build Status

1. Go to **Actions** tab in your repository
2. See workflow runs and their status
3. Click on a run to see detailed logs

### Check Published Images

1. Go to your GitHub profile
2. Click **Packages** tab
3. See all published images and versions

### View Releases

1. Go to **Releases** in your repository
2. See version history and release notes

## 🎯 Using the Images

### Development (Local Builds)

```bash
docker-compose up -d
```

### Production (Published Images)

```bash
docker-compose -f docker-compose.prod.yml up -d
```

The `docker-compose.prod.yml` file is automatically updated with the latest version!

## 🔧 Common Tasks

### Make Images Public

By default, images are private. To make them public:

1. Go to your profile → **Packages**
2. Select a package (e.g., `orchestrator-api`)
3. Click **Package settings**
4. Scroll to **Danger Zone**
5. Click **Change visibility** → **Public**
6. Repeat for all images

### Bump Major/Minor Version

For breaking changes or new features:

```bash
# Manual trigger with custom version
# Go to Actions → Run workflow → Enter "2.0.0"

# Or create tag manually
git tag -a v2.0.0 -m "Release v2.0.0"
git push origin v2.0.0
```

### Skip CI for Documentation

```bash
git commit -m "docs: update README [skip ci]"
git push origin main
```

### Rollback to Previous Version

```bash
# Pull previous version
docker pull ghcr.io/YOUR_USERNAME/orchestrator-api:v1.2.2

# Update docker-compose to use specific version
# Edit docker-compose.prod.yml and change :latest to :v1.2.2
```

## 🐛 Troubleshooting

### Build Fails

**Check logs:**
1. Actions tab → Click failed workflow
2. Review error messages
3. Fix issues and push again

### Images Not Visible

**Make them public:**
- Profile → Packages → Package settings → Change visibility

### Permission Errors

**Fix permissions:**
- Settings → Actions → General
- Enable "Read and write permissions"

### Version Already Exists

**Delete and retry:**
```bash
git tag -d v1.2.3
git push origin :refs/tags/v1.2.3
# Push again
```

## 📚 Full Documentation

For detailed information:
- **[CI/CD Setup Guide](docs/deployment/CICD_SETUP.md)** - Complete setup and configuration
- **[Workflow README](.github/workflows/README.md)** - Workflow details
- **[Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md)** - Production deployment

## ✅ Checklist

Before your first push:

- [ ] Run `./scripts/init-version.sh`
- [ ] Configure repository permissions (Settings → Actions)
- [ ] Commit and push to main branch
- [ ] Watch Actions tab for first build
- [ ] Verify images are published
- [ ] Make images public (optional)
- [ ] Test pulling images
- [ ] Update production deployment

## 🎓 Best Practices

1. **Test locally first**: Build and test before pushing
2. **Use semantic versioning**: Major.Minor.Patch
3. **Write good commit messages**: Use conventional commits
4. **Monitor first build**: Watch the Actions tab
5. **Keep images private**: Unless you need them public

## 🚀 Next Steps

After setup:
1. ✅ Push code to trigger builds
2. ✅ Monitor workflow in Actions tab
3. ✅ Verify images are published
4. ✅ Test pulling and running images
5. ✅ Deploy to production using published images

---

**Need Help?** See [docs/deployment/CICD_SETUP.md](docs/deployment/CICD_SETUP.md) for detailed documentation.
