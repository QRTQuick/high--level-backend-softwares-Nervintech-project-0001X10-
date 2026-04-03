#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/native"
mkdir -p "$BUILD_DIR"

OS_NAME="$(uname -s)"
if [[ "$OS_NAME" == "Darwin" ]]; then
  EXT="dylib"
else
  EXT="so"
fi

CFLAGS=(-O2 -fPIC)
CXXFLAGS=(-O2 -fPIC)
LDFLAGS=(-shared)

printf "Building native libraries into %s\n" "$BUILD_DIR"

gcc "${CFLAGS[@]}" "${LDFLAGS[@]}" \
  "$ROOT_DIR/native/c/risk_score.c" \
  -o "$BUILD_DIR/libdefender_c.$EXT"

g++ "${CXXFLAGS[@]}" "${LDFLAGS[@]}" \
  "$ROOT_DIR/native/cpp/anomaly_score.cpp" \
  -o "$BUILD_DIR/libdefender_cpp.$EXT"

gcc "${CFLAGS[@]}" "${LDFLAGS[@]}" \
  "$ROOT_DIR/native/asm/entropy_x86_64.S" \
  -o "$BUILD_DIR/libdefender_asm.$EXT"

printf "Native build complete.\n"
ls -lh "$BUILD_DIR"
