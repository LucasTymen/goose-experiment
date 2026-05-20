# AI LAB ARCHITECTURE

## WSL Native

- Ollama
- Goose CLI
- Models:
  - mistral
  - llama3
  - codellama

## Docker AI Lab

- OpenWebUI
- Qdrant
- PostgreSQL
- Redis

## Production Stack

- SquidResearch
- n8n
- Flowise
- postgres_dev

## Isolation Strategy

Production and AI Lab are isolated:
- dedicated ports
- dedicated containers
- dedicated volumes
- no shared postgres
- no shared redis
