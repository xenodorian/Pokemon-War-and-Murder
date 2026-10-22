#!/bin/sh
# TEST_SRC_ROM=/abs/candidate.gba tests a candidate stage output before it is made the release.
# usage: TEST_...=.. tools/mk_test_rom.sh OUT.gba   Scratch test ROM = copy of the one ROM + tools/test_stage.py. OUT must be outside the repo.
set -e
cd "$(dirname "$0")/.."
case "$1" in /*) ;; *) echo "OUT must be an absolute path outside the repo"; exit 1;; esac
case "$1" in "$(pwd)"/*) echo "OUT must be outside the repo"; exit 1;; esac
python3 tools/test_stage.py "${TEST_SRC_ROM:-PokemonWarAndMurder.gba}" "$1" >/dev/null
