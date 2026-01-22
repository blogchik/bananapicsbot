#!/bin/bash
# GitHub Container Registry package cleanup script
# This script removes old package versions while keeping the most recent ones

set -e

OWNER="blogchik"
PACKAGE_TYPE="container"
REPO_NAME="bananapicsbot"
PACKAGES=("api" "bot")

# Number of versions to keep (excluding semantic versions and main branch)
KEEP_SHA_VERSIONS=5

echo "GitHub Package Cleanup Script"
echo "=============================="
echo ""

# Check if gh CLI is authenticated
if ! gh auth status > /dev/null 2>&1; then
    echo "Error: gh CLI is not authenticated"
    echo "Please run: gh auth login"
    exit 1
fi

# Function to get all package versions
get_package_versions() {
    local package_name=$1
    local full_package="$REPO_NAME%2F$package_name"
    echo "Fetching versions for $REPO_NAME/$package_name..."

    # Using GitHub API to list package versions
    gh api "users/$OWNER/packages/$PACKAGE_TYPE/$full_package/versions" \
        --jq '.[] | {id: .id, tags: .metadata.container.tags, created_at: .created_at}' 2>/dev/null || {
        echo "Error: Unable to fetch package versions. Make sure you have read:packages scope."
        echo "To add scope: gh auth refresh -h github.com -s delete:packages,write:packages,read:packages"
        return 1
    }
}

# Function to delete a package version
delete_package_version() {
    local package_name=$1
    local version_id=$2
    local tags=$3
    local full_package="$REPO_NAME%2F$package_name"

    echo "  Deleting version: $tags (ID: $version_id)"
    gh api --method DELETE "users/$OWNER/packages/$PACKAGE_TYPE/$full_package/versions/$version_id" || {
        echo "  Warning: Failed to delete version $version_id"
    }
}

# Function to clean up old SHA-tagged versions
cleanup_package() {
    local package_name=$1
    local full_package="$REPO_NAME%2F$package_name"

    echo ""
    echo "Processing package: $REPO_NAME/$package_name"
    echo "-----------------------------------"

    # Get all versions
    local versions=$(gh api "users/$OWNER/packages/$PACKAGE_TYPE/$full_package/versions" \
        --jq '.[] | {id: .id, tags: .metadata.container.tags, created: .created_at}' 2>/dev/null)

    if [ -z "$versions" ]; then
        echo "  No versions found or unable to access"
        return
    fi

    # Parse versions and categorize
    local sha_versions=()
    local keep_tags=("main" "latest")

    # Get all version IDs with sha- prefix (excluding latest N)
    local sha_count=0
    while IFS= read -r line; do
        local version_id=$(echo "$line" | jq -r '.id' 2>/dev/null || echo "")
        local tags=$(echo "$line" | jq -r '.tags[]' 2>/dev/null || echo "")

        if [ -z "$version_id" ] || [ "$version_id" = "null" ]; then
            continue
        fi

        # Check if this version has only sha- tags
        local has_sha=false
        local has_keep=false

        for tag in $tags; do
            if [[ $tag == sha-* ]]; then
                has_sha=true
            fi

            for keep_tag in "${keep_tags[@]}"; do
                if [[ $tag == $keep_tag* ]] || [[ $tag =~ ^[0-9]+\.[0-9]+(\.[0-9]+)?$ ]]; then
                    has_keep=true
                    break
                fi
            done
        done

        # If version has only sha tags and we have more than KEEP_SHA_VERSIONS
        if [ "$has_sha" = true ] && [ "$has_keep" = false ]; then
            sha_count=$((sha_count + 1))
            if [ $sha_count -gt $KEEP_SHA_VERSIONS ]; then
                echo "  Found old SHA version to delete: $tags"
                sha_versions+=("$version_id|$tags")
            else
                echo "  Keeping recent SHA version: $tags"
            fi
        else
            echo "  Keeping version: $tags"
        fi
    done < <(echo "$versions" | jq -c '.')

    # Delete old SHA versions
    if [ ${#sha_versions[@]} -eq 0 ]; then
        echo "  No old versions to delete"
    else
        echo ""
        echo "  Deleting ${#sha_versions[@]} old SHA versions..."
        for version_data in "${sha_versions[@]}"; do
            IFS='|' read -r version_id tags <<< "$version_data"
            delete_package_version "$package_name" "$version_id" "$tags"
        done
    fi
}

# Main execution
echo "This script will clean up old SHA-tagged package versions"
echo "Keeping policies:"
echo "  - All semantic version tags (e.g., 0.1.2, 0.1)"
echo "  - main/latest tags"
echo "  - Most recent $KEEP_SHA_VERSIONS SHA-tagged versions"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted"
    exit 0
fi

# Process each package
for package in "${PACKAGES[@]}"; do
    cleanup_package "$package"
done

echo ""
echo "Cleanup completed!"
echo ""
echo "To verify, visit:"
echo "  https://github.com/users/$OWNER/packages/container/$REPO_NAME%2Fapi"
echo "  https://github.com/users/$OWNER/packages/container/$REPO_NAME%2Fbot"
