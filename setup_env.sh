#!/usr/bin/env bash
export $(grep -v '^#' .env | xargs)
export PYTHONPATH='/home/bdyetton/NoShowFOMO/'