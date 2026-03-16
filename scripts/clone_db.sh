#!/bin/bash

SOURCE_DB=$1
TARGET_DB=$2

# Usage: ./clone_db.sh postgres preview_feature_db
psql -h $HOST -U $USER -d postgres -c "CREATE DATABASE \"$TARGET_DB\" TEMPLATE \"$SOURCE_DB\";"
