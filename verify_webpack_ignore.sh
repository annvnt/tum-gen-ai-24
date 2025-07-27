#!/bin/bash

echo "🔍 Verifying webpack cache files are properly ignored by git..."

# Check if .gitignore contains webpack patterns
echo "📋 Checking .gitignore configuration..."
if grep -q "webpack" .gitignore; then
    echo "✅ Webpack patterns found in .gitignore"
else
    echo "❌ Webpack patterns missing from .gitignore"
fi

# Check if .next is ignored
echo "📋 Checking .next directory ignore status..."
if git check-ignore web/.next > /dev/null 2>&1; then
    echo "✅ web/.next directory is properly ignored"
else
    echo "❌ web/.next directory is not ignored"
fi

# Check for any still-tracked webpack files
echo "📋 Checking for tracked webpack cache files..."
tracked_files=$(git ls-files | grep -E "(\.pack|\.pack\.gz|\.hot-update|webpack-cache)")
if [ -n "$tracked_files" ]; then
    echo "❌ Still tracked files found:"
    echo "$tracked_files"
else
    echo "✅ No webpack cache files are tracked by git"
fi

# Test if new cache files would be ignored
echo "📋 Testing ignore patterns..."
touch web/.next/test.pack.gz 2>/dev/null || true
touch web/.next/cache/webpack/test.123.pack.gz 2>/dev/null || true

if git check-ignore web/.next/test.pack.gz > /dev/null 2>&1; then
    echo "✅ .pack.gz files are properly ignored"
else
    echo "❌ .pack.gz files are not ignored"
fi

# Clean up test files
rm -f web/.next/test.pack.gz web/.next/cache/webpack/test.123.pack.gz

echo "🎉 Verification complete!"