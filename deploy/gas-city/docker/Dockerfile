# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e

FROM debian@sha256:7b140f374b289a7c2befc338f42ebe6441b7ea838a042bbd5acbfca6ec875818 AS verified-tools

COPY artifacts/gc /opt/verified/gc
COPY artifacts/bd /opt/verified/bd
COPY artifacts/dolt /opt/verified/dolt
COPY artifacts/aegis-runtime.whl /opt/verified/aegis-runtime.whl
RUN set -eu; \
    echo 'ee26f66f39be5bde1f3ab1cc28115f57c6c553b595add893bba93fd2bfd2f637  /opt/verified/gc' | sha256sum -c -; \
    echo 'f7dcf3d22eae0bf09d764a9a47ab5c6e263ee91b19f2243d9e0e077561cceb1e  /opt/verified/bd' | sha256sum -c -; \
    echo '72352f1d882472a7a8d6124e9c4dc12f80e2c2359ea95f1424c032e9250e35e6  /opt/verified/dolt' | sha256sum -c -; \
    echo '4fee99a8d1293019bfdb305635706437b655b2919b971f80185f14a35d26b99e  /opt/verified/aegis-runtime.whl' | sha256sum -c -; \
    chmod 0555 /opt/verified/gc /opt/verified/bd /opt/verified/dolt; \
    chmod 0444 /opt/verified/aegis-runtime.whl

FROM debian@sha256:7b140f374b289a7c2befc338f42ebe6441b7ea838a042bbd5acbfca6ec875818 AS worker-base

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       bash ca-certificates coreutils curl gh git jq less openssh-client procps \
       python3 python3-jsonschema ripgrep tini zsh \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 worker \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash worker

COPY --from=verified-tools /opt/verified/gc /usr/local/bin/gc
COPY --from=verified-tools /opt/verified/bd /usr/local/bin/bd
COPY --from=verified-tools /opt/verified/dolt /usr/local/bin/dolt
COPY --from=verified-tools /opt/verified/aegis-runtime.whl /opt/gas-city/aegis-runtime.whl
COPY docker/provider-supervisor.py /opt/gas-city/provider-supervisor.py
COPY docker/git-credential-github.sh /opt/gas-city/git-credential-github.sh
COPY docker/task-authority.py /opt/gas-city/task-authority.py
COPY docker/aegis-polecat-startup.py /opt/gas-city/aegis-polecat-startup.py
COPY docker/aegis-runtime-shim.py /opt/gas-city/aegis-runtime-shim.py
COPY config/city.worker.toml /opt/gas-city/city.worker.toml
COPY config/codex-preflight-models.json /opt/gas-city/codex-preflight-models.json
RUN echo 'afe48ad9b4a72c0c47bf13624450a9b31d33555d1048a6cee030e17ae6a1f7c8  /opt/gas-city/provider-supervisor.py' | sha256sum -c - \
    && echo '5ea3e3cad6b71fbaf6c976c0ba5e1e948fc0cb1267575c5611a8d3bde9c1c11f  /opt/gas-city/task-authority.py' | sha256sum -c - \
    && echo '61256361f680b47f75125b360e61c23fc8a3f7248b9c1a8abc59a1cfe6a17d32  /opt/gas-city/aegis-polecat-startup.py' | sha256sum -c - \
    && echo '5c8d153d31946e7773295e2c6496fa7ed4b566bda572b2bc61db0622528eedbc  /opt/gas-city/aegis-runtime-shim.py' | sha256sum -c - \
    && echo '4fee99a8d1293019bfdb305635706437b655b2919b971f80185f14a35d26b99e  /opt/gas-city/aegis-runtime.whl' | sha256sum -c - \
    && echo 'a6d5aa258d4036598eb877433c055d9be569e52053609b4b8e89898fb58a0ccf  /opt/gas-city/city.worker.toml' | sha256sum -c - \
    && echo '1487260f5deb22b5da6c3d306ae06444fc207b69881440dcc010cacb029f419c  /opt/gas-city/codex-preflight-models.json' | sha256sum -c - \
    && install -d -o root -g root -m 0555 /opt/gas-city/aegis-runtime \
        /opt/gas-city/model-preflight \
    && install -d -o root -g root -m 0555 /run/gas-city-git/private.git \
        /run/gas-city-trusted \
    && install -o root -g root -m 0444 /dev/null \
        /run/gas-city-trusted/git-broker.json \
    && python3 -m zipfile -e /opt/gas-city/aegis-runtime.whl /opt/gas-city/aegis-runtime \
    && find /opt/gas-city/aegis-runtime -type d -exec chmod 0555 {} + \
    && find /opt/gas-city/aegis-runtime -type f -exec chmod 0444 {} + \
    && PYTHONDONTWRITEBYTECODE=1 python3 -I -c 'import pathlib,sys; root="/opt/gas-city/aegis-runtime"; sys.path.insert(0,root); import jsonschema; from aegis_foundation import cli; assert pathlib.Path(cli.__file__).resolve().is_relative_to(pathlib.Path(root))' \
    && chmod 0444 /opt/gas-city/task-authority.py \
    && chmod 0444 /opt/gas-city/aegis-polecat-startup.py \
    && chmod 0444 /opt/gas-city/aegis-runtime.whl /opt/gas-city/aegis-runtime-shim.py \
        /opt/gas-city/city.worker.toml /opt/gas-city/codex-preflight-models.json \
    && chmod 0555 /opt/gas-city/provider-supervisor.py /opt/gas-city/git-credential-github.sh

ENV HOME=/home/worker \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    GIT_TERMINAL_PROMPT=0 \
    BD_DISABLE_METRICS=1 \
    OTEL_SDK_DISABLED=true \
    DISABLE_AUTOUPDATER=1

WORKDIR /workspace
USER 1000:1000
ENTRYPOINT ["/usr/bin/tini", "--", "python3", "/opt/gas-city/provider-supervisor.py"]

FROM worker-base AS codex-worker

USER root
COPY artifacts/codex/bin/codex /opt/codex/bin/codex
COPY artifacts/codex/bin/codex-code-mode-host /opt/codex/bin/codex-code-mode-host
COPY artifacts/codex/codex-path/rg /opt/codex/codex-path/rg
COPY artifacts/codex/codex-resources/zsh/bin/zsh /opt/codex/codex-resources/zsh/bin/zsh
RUN echo '2b3edc9cdfd1717fba3dbc92817205a8a2c7511d459e456d4817eeff6f78ed7a  /opt/codex/bin/codex' | sha256sum -c - \
    && echo '49c528deb71531b7bfdcaa32e07c12de03f43d91f13edeeda51d527dac2c911e  /opt/codex/bin/codex-code-mode-host' | sha256sum -c - \
    && echo 'ebeaf56f8a25e102e9419933423738b3a2a613a444fd749d695e15eba53f71f2  /opt/codex/codex-path/rg' | sha256sum -c - \
    && echo '67faaaa89242c4a332e16e508a1977cffc24bf7fca31d4411cdfd101f3831ef3  /opt/codex/codex-resources/zsh/bin/zsh' | sha256sum -c - \
    && chmod 0555 /opt/codex/bin/* /opt/codex/codex-path/rg \
        /opt/codex/codex-resources/zsh/bin/zsh \
    && ln -s /opt/codex/bin/codex /usr/local/bin/codex
ENV CODEX_HOME=/home/worker/.codex \
    GC_EXPECTED_MODEL=gpt-5.6-sol \
    GC_EXPECTED_EFFORT=xhigh \
    GC_TRANSCRIPT_ROOT=/home/worker/.codex/sessions
USER 1000:1000
CMD ["codex"]

FROM worker-base AS claude-worker

USER root
COPY artifacts/claude /usr/local/bin/claude
RUN echo 'e7d2ceb53ed4c2ced1fe7fc1c6331c98dc5f7b4c9b2722d9c5fa3dd5dff6f719  /usr/local/bin/claude' | sha256sum -c - \
    && chmod 0555 /usr/local/bin/claude
ENV CLAUDE_CONFIG_DIR=/home/worker/.claude \
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
    GC_EXPECTED_MODEL=claude-fable-5 \
    GC_TRANSCRIPT_ROOT=/home/worker/.claude/projects
USER 1000:1000
CMD ["claude"]

FROM debian@sha256:7b140f374b289a7c2befc338f42ebe6441b7ea838a042bbd5acbfca6ec875818 AS dolt-server

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       bash ca-certificates coreutils tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 dolt \
    && useradd --uid 1000 --gid 1000 --no-create-home \
       --home-dir /var/lib/dolt --shell /usr/sbin/nologin dolt \
    && install -d -o 1000 -g 1000 -m 0700 /var/lib/dolt /var/lib/dolt/data
COPY --from=verified-tools /opt/verified/dolt /usr/local/bin/dolt
COPY docker/dolt-entrypoint.sh /opt/gas-city/dolt-entrypoint.sh
COPY docker/dolt-healthcheck.sh /opt/gas-city/dolt-healthcheck.sh
COPY docker/dolt-bootstrap.yaml /opt/gas-city/dolt-bootstrap.yaml
COPY docker/dolt-server.yaml /opt/gas-city/dolt-server.yaml
# Compose supplies /tmp as a private writable tmpfs while the image root stays
# read-only. Dolt always loads (and may create) its global CLI config below
# $HOME before honoring the sql-server cfg_dir, so keep that ephemeral state
# off the immutable image and outside the persistent database volume.
ENV HOME=/tmp DOLT_DATA_DIR=/var/lib/dolt/data
USER 1000:1000
ENTRYPOINT ["/usr/bin/tini", "--", "bash", "/opt/gas-city/dolt-entrypoint.sh"]

FROM debian@sha256:7b140f374b289a7c2befc338f42ebe6441b7ea838a042bbd5acbfca6ec875818 AS egress-proxy

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       ca-certificates socat tini tinyproxy \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10002 gasproxy \
    && useradd --uid 10002 --gid 10002 --no-create-home \
       --home-dir /nonexistent --shell /usr/sbin/nologin gasproxy
COPY docker/tinyproxy.conf /etc/tinyproxy/tinyproxy.conf
COPY docker/tinyproxy.filter /etc/tinyproxy/filter
USER 10002:10002
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/bin/tinyproxy", "-d", "-c", "/etc/tinyproxy/tinyproxy.conf"]
