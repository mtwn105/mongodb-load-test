#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mvn -B -q package dependency:copy-dependencies -DincludeScope=runtime -DoutputDirectory=.tools/lib

sha256sum -c DEPENDENCIES.sha256
sha256sum -c vendor/SHA256SUMS
