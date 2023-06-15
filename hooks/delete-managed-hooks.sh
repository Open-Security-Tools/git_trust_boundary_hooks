# exit when any command fails
set -e

# Change to this script's directory
cd "$(dirname "$0")"

echo "Deleting managed hooks..."
rm -rf pre-commit
rm -rf commit-msg
rm -rf pre-push
rm -rf trust_boundary
rm -rf full_scan
rm -rf delete-managed-hooks.sh
