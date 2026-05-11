#!/bin/bash

PASS=0
FAIL=0

run_suite() {
  local name=$1
  local dir=$2
  local db_url=$3

  echo ""
  echo "════════════════════════════════════════"
  echo "  $name"
  echo "════════════════════════════════════════"

  cd /tests/$dir
  if DATABASE_URL="$db_url" pytest tests/ -v --tb=short --no-header; then
    PASS=$((PASS + 1))
  else
    FAIL=$((FAIL + 1))
  fi
  cd /tests
}

# FastAPI-сервисы используют asyncpg-драйвер → нужен aiosqlite-URL
run_suite "menu-service"      menu-service      "sqlite+aiosqlite:///./test.db"
run_suite "warehouse-service" warehouse-service "sqlite+aiosqlite:///./test.db"
run_suite "auth-service"      auth-service      "sqlite+aiosqlite:///./test.db"

# order-service — Flask, синхронный SQLAlchemy
run_suite "order-service"     order-service     "sqlite:///./test.db"

echo ""
echo "════════════════════════════════════════"
echo "  Итого: ✅ $PASS прошли  ❌ $FAIL упали"
echo "════════════════════════════════════════"

[ $FAIL -eq 0 ]