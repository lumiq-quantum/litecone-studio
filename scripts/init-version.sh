#!/bin/bash
# Initialize version tagging for CI/CD pipeline

set -e

echo "🏷️  Initializing Version Tags for CI/CD"
echo "========================================"
echo

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

# Check if there are any existing tags
EXISTING_TAGS=$(git tag -l "v*" | wc -l)

if [ "$EXISTING_TAGS" -gt 0 ]; then
    echo "📋 Existing version tags found:"
    git tag -l "v*" | sort -V | tail -5
    echo
    LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
    echo "Latest tag: $LATEST_TAG"
    echo
    read -p "Do you want to create a new tag? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "✅ Using existing tags. CI/CD will auto-increment from $LATEST_TAG"
        exit 0
    fi
fi

# Prompt for initial version
echo "Enter initial version (default: 0.1.0):"
read -r VERSION
VERSION=${VERSION:-0.1.0}

# Validate version format
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Error: Invalid version format. Use semantic versioning (e.g., 1.0.0)"
    exit 1
fi

VERSION_TAG="v$VERSION"

# Check if tag already exists
if git rev-parse "$VERSION_TAG" >/dev/null 2>&1; then
    echo "❌ Error: Tag $VERSION_TAG already exists"
    exit 1
fi

# Create the tag
echo
echo "Creating tag: $VERSION_TAG"
git tag -a "$VERSION_TAG" -m "Initial release $VERSION_TAG"

echo "✅ Tag created successfully!"
echo

# Ask if user wants to push
read -p "Push tag to remote? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "Pushing tag to origin..."
    git push origin "$VERSION_TAG"
    echo "✅ Tag pushed successfully!"
    echo
    echo "🚀 CI/CD Pipeline Setup Complete!"
    echo
    echo "Next steps:"
    echo "1. Push code to main/master branch to trigger automatic builds"
    echo "2. Check GitHub Actions tab to monitor the workflow"
    echo "3. View published images at: https://github.com/$GITHUB_REPOSITORY/packages"
    echo
    echo "The next push will auto-increment to v$VERSION → v0.1.1"
else
    echo "✅ Tag created locally. Push manually with:"
    echo "   git push origin $VERSION_TAG"
fi

echo
echo "📚 For more information, see: docs/deployment/CICD_SETUP.md"
