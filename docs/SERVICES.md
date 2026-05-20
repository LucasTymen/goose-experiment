# SERVICES
CONTAINER ID   IMAGE                                COMMAND                  CREATED          STATUS                          PORTS                                                   NAMES
fb42ba540387   ghcr.io/open-webui/open-webui:main   "bash start.sh"          34 minutes ago   Up 9 minutes (healthy)          0.0.0.0:3004->8080/tcp, [::]:3004->8080/tcp             goose-openwebui
0d2f0baf7eaa   postgres:16                          "docker-entrypoint.s…"   46 minutes ago   Up 46 minutes                   0.0.0.0:5434->5432/tcp, [::]:5434->5432/tcp             goose-postgres
4b0f29c2354d   qdrant/qdrant                        "./entrypoint.sh"        46 minutes ago   Up 46 minutes                   6334/tcp, 0.0.0.0:6334->6333/tcp, [::]:6334->6333/tcp   goose-qdrant
3dcfd729e7ed   redis:7                              "docker-entrypoint.s…"   46 minutes ago   Up 46 minutes                   0.0.0.0:6374->6379/tcp, [::]:6374->6379/tcp             goose-redis
a09cbf3e690b   squidresearch-enriched-linux         "uvicorn main:app --…"   7 weeks ago      Up 35 hours                     127.0.0.1:8081->8080/tcp                                enriched-linux-container
61eabdcf66f6   squidresearch-web                    "/bin/bash /usr/src/…"   2 months ago     Up 35 hours                     0.0.0.0:8001->8000/tcp, [::]:8001->8000/tcp             django_dev
088e28c882ae   docker.n8n.io/n8nio/n8n:latest       "tini -- /docker-ent…"   2 months ago     Up 35 hours                     0.0.0.0:5680->5678/tcp, [::]:5680->5678/tcp             n8n_dev
d114e20fa741   flowiseai/flowise:latest             "flowise start"          2 months ago     Up 35 hours                     0.0.0.0:3002->3000/tcp, [::]:3002->3000/tcp             flowise_dev
2fcde1185959   squidresearch-beat                   "celery -A squidrese…"   2 months ago     Restarting (1) 14 seconds ago                                                           celery_beat_dev
a1158b56cd9e   squidresearch-worker                 "celery -A squidrese…"   2 months ago     Restarting (1) 14 seconds ago                                                           celery_worker_dev
1830136f7a9b   dperson/torproxy:latest              "/sbin/tini -- /usr/…"   2 months ago     Up 35 hours (healthy)           8118/tcp, 9050-9051/tcp                                 tor_dev
62d6c3b66f6c   redis:7-alpine                       "docker-entrypoint.s…"   2 months ago     Up 35 hours                     6379/tcp                                                redis_dev
05b1da5ba15f   postgres:15                          "docker-entrypoint.s…"   2 months ago     Up 35 hours                     127.0.0.1:5432->5432/tcp                                postgres_dev
eb37708816f6   e195b2889efd                         "docker-entrypoint.s…"   7 months ago     Up 35 hours                     5432/tcp                                                a703d5f914cf_postgres

# NETWORKS
NETWORK ID     NAME                                  DRIVER    SCOPE
7c69e107152b   bridge                                bridge    local
2610f5ade5ee   docker_default                        bridge    local
8cb524c6791f   host                                  host      local
8aaa73dc5d42   n8n_n8n_internal                      bridge    local
0af1549f0781   n8n_postgres_network                  bridge    local
df3d9ec5ab22   none                                  null      local
b8449ed22d11   squidresearch_dev_network             bridge    local
9f6bf2aead2f   squidresearch_enriched_network        bridge    local
3ae76a0a63da   squidresearch_network                 bridge    local
7bc65c30be58   squidresearch_squidresearch_network   bridge    local

# VOLUMES
DRIVER    VOLUME NAME
local     2b8dff88636d0b0ba0d5144cd8f3d6ed6b9e8038de0bd11b70d8257574fc9edf
local     5ceb7bd15c46781802359fb3f8f5ee273bd5afc63b96bc13a2f3128082a2ac57
local     6dbec43b362e5d907265c2b99011cf2af3d53f5b7e83b745a97820d942cbf74f
local     7b5ad1d5d8b2fa7d68b2ac3ddbf35529ff5e62d83f64c92883c1d67b4632bc44
local     21f9e7a07dbb9e780fd40091b78fbb1e68e9fc328bd757d385f24f15b0257202
local     84f4e624c4e4882f695d1a05896d455e901746031a0b0d9dc7d0169d1773ad66
local     627faef0998d111f6d46dd4ffc90d7079522ef57742e460e008abe23cc7abeef
local     6535bb9770ebd209f44f83fea6fbc9357df60ccb2bf4c9f47c003b98dd5a52be
local     bea0809efc1b9ce8be870a8c5292148affdcb67c32c57b913247652e8c49b908
local     cebba8286b1ae8096b90b3a5357b520ce4b5aafa25679bccbb0dfd134ad9137d
local     d266cb80810ab5cf93802dcef022304aa9b6abc32fe8340c78e41ad15878148c
local     docker_ollama_data
local     docker_openwebui_data
local     docker_postgres_data
local     docker_qdrant_data
local     n8n_flowise_data
local     n8n_n8n_data
local     n8n_n8n_postgres_data
local     n8n_pgadmin_data
local     n8n_postgres_data
local     squidresearch_enriched_results_data
local     squidresearch_enriched_tools_data
local     squidresearch_flowise_dev_data
local     squidresearch_mobile_expo_cache
local     squidresearch_n8n_dev_data
local     squidresearch_postgres_data
local     squidresearch_postgres_dev_data
local     squidresearch_redis_data
local     squidresearch_redis_dev_data

# IMAGES
REPOSITORY                      TAG              IMAGE ID       CREATED         SIZE
redis                           7                abe89191aa1b   8 hours ago     113MB
postgres                        16               f40a5645a21f   8 hours ago     451MB
ollama/ollama                   latest           333628ba5b2f   5 days ago      6.55GB
qdrant/qdrant                   latest           c57c657048b4   8 days ago      188MB
ghcr.io/open-webui/open-webui   main             bc3b0d67bd37   9 days ago      4.76GB
squidresearch-enriched-linux    latest           40155c45ce05   7 weeks ago     2.21GB
squidresearch-mobile            latest           720ee993b539   3 months ago    887MB
squidresearch-web               latest           ae72297eee64   3 months ago    5.68GB
squidresearch-beat              latest           848a86bc344c   3 months ago    5.68GB
squidresearch-worker            latest           b70301e34894   3 months ago    5.68GB
squidresearch-flower            latest           4c810cdab4f9   3 months ago    5.68GB
squidresearch-frontend          latest           1136a9de0db4   3 months ago    263MB
<none>                          <none>           3607832ddd39   3 months ago    5.68GB
redis                           7-alpine         e08bd8d5a677   3 months ago    41.4MB
docker.n8n.io/n8nio/n8n         latest           7617ff2a461f   3 months ago    961MB
postgres                        15               7064d8f3d970   4 months ago    444MB
<none>                          <none>           c773641ab7d0   5 months ago    5.53GB
<none>                          <none>           3fbc64afec7b   5 months ago    5.53GB
<none>                          <none>           27069ca70a93   5 months ago    5.52GB
<none>                          <none>           610fb297103d   5 months ago    5.52GB
postgres                        17               3fe059c96160   7 months ago    453MB
<none>                          <none>           c48bd20342ec   8 months ago    244MB
<none>                          <none>           f1e192ff223d   8 months ago    1.24GB
<none>                          <none>           938bdfcc1984   8 months ago    1.24GB
<none>                          <none>           00211a8d41fc   8 months ago    1.24GB
squidresearch                   latest           7f00d3dfc19b   8 months ago    1.24GB
n8nio/n8n                       latest           43ad3c8495ed   9 months ago    1.03GB
postgres                        <none>           e195b2889efd   9 months ago    445MB
flowiseai/flowise               latest           0261e271d953   9 months ago    3.03GB
hello-world                     latest           1b44b5a3e06a   9 months ago    10.1kB
python                          3.11             180fd10e6c85   9 months ago    1.1GB
n8nio/n8n                       1.105.3          67df7b0728a7   9 months ago    1.02GB
dpage/pgadmin4                  latest           2c990ea76ddb   10 months ago   531MB
node                            20.19.4-alpine   7cdef5a33192   10 months ago   135MB
redis                           <none>           f218e591b571   10 months ago   41.4MB
dperson/torproxy                latest           6652ac4f9e48   5 years ago     29.1MB

# OLLAMA MODELS
NAME                ID              SIZE      MODIFIED     
codellama:latest    8fdf8f752f6e    3.8 GB    33 hours ago    
llama3:latest       365c0bd3c000    4.7 GB    33 hours ago    
mistral:latest      6577803aa9a0    4.4 GB    33 hours ago    
