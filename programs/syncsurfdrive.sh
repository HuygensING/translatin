#!/bin/zsh

cd ..
rclone -v sync --no-update-modtime --delete-excluded --exclude '.DS_Store' datasource surfdrive:Translatin-Sources-Curated
# rclone -v sync --no-update-modtime  --delete-excluded --exclude '.DS_Store' curatedscans surfdrive:Translatin-Sources-Scans
