# Pre-Push Checklist

Before pushing the UI build fix to trigger CI/CD, verify these items:

## ✅ Local Changes Verified

- [ ] `workflow-ui/package.json` has updated build script:
  ```json
  "build": "tsc --project tsconfig.app.json --noEmit && vite build"
  ```

- [ ] `workflow-ui/Dockerfile` has fixed npm command:
  ```dockerfile
  RUN npm ci
  ```

- [ ] `.github/workflows/build-and-push-images.yml` has 5 services (not 6)

- [ ] Local build succeeds:
  ```bash
  cd workflow-ui && npm run build
  ```

## ✅ Optional: Docker Build Test

- [ ] Docker build succeeds locally:
  ```bash
  docker build -t test-ui -f workflow-ui/Dockerfile workflow-ui
  ```

## ✅ Git Status

- [ ] Check what files changed:
  ```bash
  git status
  ```

- [ ] Verify only expected files are modified:
  - workflow-ui/package.json
  - workflow-ui/Dockerfile
  - .github/workflows/build-and-push-images.yml
  - Documentation files

## ✅ Commit Message

Use a clear, descriptive commit message:

```bash
git commit -m "fix: resolve UI build TypeScript path alias issue

- Update build script to use tsconfig.app.json explicitly with --noEmit
- Fix npm ci command in Dockerfile (remove invalid flag)
- Remove mock-agent from CI/CD pipeline (local testing only)
- Update all documentation to reflect 5 images instead of 6

This fixes the TypeScript module resolution error where @/ path aliases
were not being resolved during the Docker build process."
```

## ✅ Before Pushing

- [ ] All changes committed
- [ ] Commit message is descriptive
- [ ] Ready to trigger CI/CD workflow

## ✅ After Pushing

- [ ] Go to GitHub Actions tab
- [ ] Watch "Build and Push Docker Images" workflow
- [ ] Verify all 5 jobs succeed:
  - [ ] orchestrator-api
  - [ ] orchestrator-executor
  - [ ] orchestrator-bridge
  - [ ] orchestrator-consumer
  - [ ] orchestrator-ui ← **Should succeed now!**

## ✅ Verify Success

- [ ] All jobs show green checkmarks
- [ ] No TypeScript errors in UI build logs
- [ ] Images published to GitHub Container Registry
- [ ] New Git tag created
- [ ] GitHub Release created
- [ ] docker-compose.prod.yml updated

## 🚀 Ready to Push?

If all items above are checked, you're ready!

**Quick push:**
```bash
./commit-ui-fix.sh
```

**Or manual:**
```bash
git push origin main
```

## 📞 If Something Goes Wrong

1. **Build still fails:**
   - Check GitHub to verify files were pushed
   - Clear GitHub Actions cache
   - Re-run workflow

2. **TypeScript errors persist:**
   - Verify tsconfig.app.json has path mappings
   - Check all src/lib/*.ts files exist
   - Review UI_BUILD_FIX_SUMMARY.md

3. **Need help:**
   - Review CICD_QUICK_START.md
   - Check docs/deployment/CICD_SETUP.md
   - Review workflow logs in Actions tab

---

**Status:** Ready to push  
**Expected Result:** All 5 images build successfully  
**Time to Complete:** ~5-10 minutes for full CI/CD pipeline
