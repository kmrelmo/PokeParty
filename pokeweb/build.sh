#!/bin/bash
set -e

echo "building.."
docker build -t pokeparty .

echo "complete"
