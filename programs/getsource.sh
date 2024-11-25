#!/bin/zsh

cd ..
rclone -v sync --no-update-modtime --delete-excluded --exclude '.DS_Store' surfdrive:Shared/TransLatin\ Curated\ JB datasource/fromjb
