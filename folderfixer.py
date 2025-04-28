# 🚨 WARNING: This deletes your existing broken .github folder — make sure you want to!
rm -rf .github
mkdir -p .github/workflows
mv run_harvest.yaml .github/workflows/run_harvest.yaml
git add .github/workflows/run_harvest.yaml
git commit -m "fix: recreate .github/workflows properly for GitHub Actions"
git push
