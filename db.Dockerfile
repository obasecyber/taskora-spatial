FROM postgis/postgis:16-3.4

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-server-dev-16 build-essential git ca-certificates \
    && git clone --depth 1 --branch v0.8.0 https://github.com/pgvector/pgvector.git /tmp/pgvector \
    && make -C /tmp/pgvector \
    && make -C /tmp/pgvector install \
    && rm -rf /tmp/pgvector \
    && apt-get purge -y build-essential git \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*