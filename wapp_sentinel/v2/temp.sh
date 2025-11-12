#!/bin/bash

RESOURCE_GROUP="napoleon-rg"
SOURCE_APP="api"
TARGET_APP=$1

if [ -z "$TARGET_APP" ]; then
  echo "Usage: ./replicate-env.sh <target-app-name>"
  exit 1
fi

# Get env vars and format them
ENV_VARS=$(az containerapp show \
  --name $SOURCE_APP \
  --resource-group $RESOURCE_GROUP \
  --query "properties.template.containers[0].env[*].[name,value]" \
  -o tsv | awk '{printf "%s=%s ", $1, $2}')

# Update target app
az containerapp update \
  --name $TARGET_APP \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars $ENV_VARS

echo "Environment variables replicated to $TARGET_APP"