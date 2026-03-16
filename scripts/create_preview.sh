#!/bin/bash

BRANCH=$1
DB_NAME="preview_${BRANCH}"

./clone_db.sh postgres $DB_NAME

# Assuming Coolify API is used here to deploy or start the docker container
# curl -X POST ...
echo "Preview DB $DB_NAME cloned. Start isolated docker instance on Coolify using this DB!"
