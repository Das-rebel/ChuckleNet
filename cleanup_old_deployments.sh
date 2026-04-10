#!/bin/bash

# Cleanup old/failed deployments
# Keep only the latest working deployment

echo "Cleaning up old deployments..."

# Delete old openclaw deployments
echo "Deleting openclaw-bridge..."
gcloud functions delete openclaw-bridge --region=asia-south1 --quiet 2>/dev/null || true

echo "Deleting openclaw-bridge-enhanced..."
gcloud functions delete openclaw-bridge-enhanced --region=asia-south1 --quiet 2>/dev/null || true

echo "Deleting openclaw-bridge-full..."
gcloud functions delete openclaw-bridge-full --region=asia-south1 --quiet 2>/dev/null || true

# Delete failed quantum-claw deployment attempt
echo "Deleting quantum-claw-v2-1774065801 (failed)..."
gcloud functions delete quantum-claw-v2-1774065801 --region=asia-south1 --quiet 2>/dev/null || true

echo ""
echo "Cleanup complete!"
echo ""
echo "Active deployments:"
gcloud functions list --regions=asia-south1 --format="table(name,status,updateTime)" | grep -E "NAME|openclaw|quantum"

