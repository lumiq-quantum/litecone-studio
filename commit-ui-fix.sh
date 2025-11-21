#!/bin/bash
# Quick script to commit and push the UI build fix

set -e

echo "🔍 Checking git status..."
git status

echo ""
echo "📝 Adding changed files..."
git add .gitignore
git add workflow-ui/package.json
git add workflow-ui/Dockerfile
git add workflow-ui/src/lib/
git add .github/workflows/build-and-push-images.yml
git add docs/
git add *.md
git add scripts/

echo ""
echo "✅ Files staged for commit"
echo ""
echo "📋 Files to be committed:"
git status --short

echo ""
read -p "Proceed with commit? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Commit cancelled"
    exit 1
fi

echo ""
echo "💾 Committing changes..."
git commit -m "fix: resolve UI build TypeScript path alias issue

- Update build script to use tsconfig.app.json explicitly with --noEmit
- Fix npm ci command in Dockerfile (remove invalid flag)
- Remove mock-agent from CI/CD pipeline (local testing only)
- Update all documentation to reflect 5 images instead of 6
- Add comprehensive CI/CD documentation and setup guides

This fixes the TypeScript module resolution error where @/ path aliases
were not being resolved during the Docker build process."

echo ""
echo "✅ Changes committed!"
echo ""
read -p "Push to origin? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "⚠️  Changes committed locally but not pushed"
    echo "   Run 'git push origin main' when ready"
    exit 0
fi

echo ""
echo "🚀 Pushing to origin..."
git push origin main

echo ""
echo "✅ Changes pushed successfully!"
echo ""
echo "🎯 Next steps:"
echo "   1. Go to GitHub Actions tab"
echo "   2. Watch the 'Build and Push Docker Images' workflow"
echo "   3. Verify all 5 images build successfully"
echo "   4. Check that images are published to GHCR"
echo ""
echo "📍 GitHub Actions: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
