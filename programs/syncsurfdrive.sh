#!/bin/zsh

cd ..

if [[ -e datasource/transcriptions/tei ]]; then
    rm -rf datasource/transcriptions/tei
fi
mkdir -p datasource/transcriptions
cp -a tei datasource/transcriptions
rclone -v sync --no-update-modtime --delete-excluded --exclude '.DS_Store' datasource surfdrive:Translatin-Sources-Curated
# rclone -v sync --no-update-modtime  --delete-excluded --exclude '.DS_Store' curatedscans surfdrive:Translatin-Sources-Scans
