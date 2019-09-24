#!/usr/bin/env bash
export $(grep -v '^#' .env | xargs | tr -d '\r')
export PYTHONPATH='~/NoShowFOMO/'