#!/bin/bash
set -e

cd "$(dirname "$0")"

# 读取 .env 文件
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# 数据库配置
export POSTGRES_HOST=${POSTGRES_HOST:-localhost}
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
export BITMAGNET_POSTGRES="postgres://postgres:${POSTGRES_PASSWORD}@localhost:5432/bitmagnet?sslmode=disable"

# 启动 PostgreSQL (Docker)
echo "启动 PostgreSQL..."
if ! docker ps -q --filter "name=bitmagnet-postgres" | grep -q .; then
  docker run -d --name bitmagnet-postgres \
    -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres} \
    -e POSTGRES_DB=bitmagnet \
    -v "$(pwd)/data/db:/var/lib/postgresql/data" \
    -p 5432:5432 \
    --shm-size=2g \
    postgres:16-alpine

  # 等待 PostgreSQL 就绪
  echo "等待数据库启动..."
  for i in {1..30}; do
    if docker exec bitmagnet-postgres pg_isready -q; then
      echo "数据库就绪"
      break
    fi
    sleep 1
  done
else
  # 容器存在但可能未运行
  docker start bitmagnet-postgres 2>/dev/null || true
  echo "等待数据库启动..."
  for i in {1..30}; do
    if docker exec bitmagnet-postgres pg_isready -q; then
      echo "数据库就绪"
      break
    fi
    sleep 1
  done
fi

# 启动 bitmagnet
echo "启动 bitmagnet..."
./bitmagnet worker run --keys=http_server --keys=queue_server --keys=dht_crawler
