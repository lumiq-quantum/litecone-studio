# CI/CD Setup Checklist

Use this checklist to ensure your CI/CD pipeline is properly configured.

## ✅ Pre-Setup

- [ ] Repository is on GitHub
- [ ] You have admin access to the repository
- [ ] Docker images are defined in docker-compose.yml
- [ ] Dockerfiles exist for all services

## ✅ Initial Setup

### 1. Version Initialization
- [ ] Run `./scripts/init-version.sh`
- [ ] Initial version tag created (e.g., v0.1.0)
- [ ] Tag pushed to remote repository

### 2. Repository Configuration
- [ ] Go to Settings → Actions → General
- [ ] Enable "Read and write permissions"
- [ ] Enable "Allow GitHub Actions to create and approve pull requests"
- [ ] Click Save

### 3. Workflow File
- [ ] `.github/workflows/build-and-push-images.yml` exists
- [ ] Workflow file is committed to repository
- [ ] All 5 production services are listed in the matrix

## ✅ First Build

### Trigger Build
- [ ] Code committed to main/master branch
- [ ] Push to remote repository
- [ ] Workflow triggered automatically

### Monitor Build
- [ ] Go to Actions tab
- [ ] See "Build and Push Docker Images" workflow running
- [ ] All jobs show green checkmarks
- [ ] No error messages in logs

### Verify Images
- [ ] Go to your profile → Packages
- [ ] See 5 packages created:
  - [ ] orchestrator-api
  - [ ] orchestrator-executor
  - [ ] orchestrator-bridge
  - [ ] orchestrator-consumer
  - [ ] orchestrator-ui
- [ ] Each package has tags: latest, v{version}
- [ ] Mock agent is NOT published (local testing only)

### Verify Release
- [ ] Go to Releases tab
- [ ] New release created (e.g., v0.1.1)
- [ ] Release notes include image list
- [ ] Git tag exists

### Verify Files
- [ ] `docker-compose.prod.yml` created/updated
- [ ] File committed to repository

## ✅ Image Access

### Pull Images
- [ ] Can pull image: `docker pull ghcr.io/YOUR_USERNAME/orchestrator-api:latest`
- [ ] Can pull specific version: `docker pull ghcr.io/YOUR_USERNAME/orchestrator-api:v0.1.1`
- [ ] Images work when run locally

### Make Public (Optional)
- [ ] Go to Packages
- [ ] For each package:
  - [ ] Click Package settings
  - [ ] Change visibility to Public
  - [ ] Confirm change

## ✅ Testing

### Local Testing
- [ ] Pull published images
- [ ] Run with docker-compose.prod.yml
- [ ] All services start successfully
- [ ] Services communicate correctly
- [ ] API responds to requests

### Version Bumping
- [ ] Make a small change
- [ ] Commit and push to main
- [ ] New version created (patch incremented)
- [ ] New images published
- [ ] New release created

### Manual Trigger
- [ ] Go to Actions → Build and Push Docker Images
- [ ] Click "Run workflow"
- [ ] Enter custom version (e.g., 1.0.0)
- [ ] Workflow runs successfully
- [ ] Specified version is used

## ✅ Documentation

- [ ] Read CICD_QUICK_START.md
- [ ] Read docs/deployment/CICD_SETUP.md
- [ ] Read .github/workflows/README.md
- [ ] Team members informed of new CI/CD process

## ✅ Production Deployment

### Preparation
- [ ] Production environment ready
- [ ] Environment variables configured
- [ ] docker-compose.prod.yml reviewed
- [ ] Deployment strategy defined

### Deployment
- [ ] Pull images on production server
- [ ] Run docker-compose.prod.yml
- [ ] Services start successfully
- [ ] Health checks pass
- [ ] Monitoring configured

### Rollback Plan
- [ ] Know how to pull previous version
- [ ] Tested rollback procedure
- [ ] Documented rollback steps

## ✅ Monitoring & Maintenance

### Regular Checks
- [ ] Monitor Actions tab for failed builds
- [ ] Review build logs periodically
- [ ] Check image sizes
- [ ] Verify version increments correctly

### Alerts (Optional)
- [ ] GitHub notifications enabled
- [ ] Email alerts for failed builds
- [ ] Slack/Discord integration (if needed)

### Updates
- [ ] Keep workflow file updated
- [ ] Update documentation as needed
- [ ] Review and update version strategy

## ✅ Security

### Image Security
- [ ] Images kept private (unless public needed)
- [ ] No secrets in Dockerfiles
- [ ] No secrets in images
- [ ] Base images are up to date

### Access Control
- [ ] Only authorized users can push to main
- [ ] Branch protection rules configured
- [ ] Required reviews for PRs (optional)

### Scanning (Optional)
- [ ] Image vulnerability scanning enabled
- [ ] Security alerts configured
- [ ] Regular security reviews

## ✅ Advanced Features (Optional)

### Multi-Environment
- [ ] Separate workflows for staging/production
- [ ] Environment-specific tags
- [ ] Environment variables per environment

### Additional Automation
- [ ] Automated testing in workflow
- [ ] Code quality checks
- [ ] Dependency updates (Dependabot)

### Notifications
- [ ] Slack notifications on build
- [ ] Discord webhooks
- [ ] Email notifications

## 🎯 Success Criteria

Your CI/CD is fully operational when:

- ✅ Every push to main triggers automatic build
- ✅ All 5 production images build successfully
- ✅ Images are published to GHCR
- ✅ Version tags are created automatically
- ✅ GitHub Releases are created
- ✅ docker-compose.prod.yml is updated
- ✅ Images can be pulled and run
- ✅ Production deployment works
- ✅ Team understands the process

## 📞 Need Help?

If any item is not checked:

1. **Review documentation:**
   - [CICD_QUICK_START.md](../CICD_QUICK_START.md)
   - [docs/deployment/CICD_SETUP.md](../docs/deployment/CICD_SETUP.md)
   - [.github/workflows/README.md](workflows/README.md)

2. **Check workflow logs:**
   - Actions tab → Click workflow run
   - Review error messages
   - Check job logs

3. **Common issues:**
   - Permission errors → Check repository settings
   - Build failures → Check Dockerfile syntax
   - Tag conflicts → Delete and recreate tag
   - Image not visible → Make package public

4. **Get support:**
   - Check GitHub Actions documentation
   - Review workflow file comments
   - Open an issue in repository

## 📝 Notes

Use this space for notes specific to your setup:

```
Date completed: _______________
Initial version: _______________
Team members trained: _______________
Production deployment date: _______________
Issues encountered: _______________
_______________________________________________
_______________________________________________
_______________________________________________
```

---

**Checklist Version:** 1.0  
**Last Updated:** 2024  
**Maintained By:** DevOps Team
