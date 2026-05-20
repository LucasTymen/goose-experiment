#!/bin/bash

echo "=== DOCKER ==="
docker ps

echo
echo "=== OLLAMA ==="
curl -s http://10.255.255.254:11434/api/tags

echo
echo "=== OPENWEBUI ==="
curl -I http://localhost:3004

echo
echo "=== QDRANT ==="
curl -s http://localhost:6334

echo
echo "=== REDIS ==="
docker exec goose-redis redis-cli ping

echo
echo "=== POSTGRES ==="
docker exec goose-postgres pg_isready -U goose
