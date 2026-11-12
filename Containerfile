# KantanOS (簡単) — family desktop OS built on Universal Blue / Bazzite.
# Full edition: KDE Plasma + NVIDIA open drivers + Steam/Game Mode pieces from Bazzite.
ARG BASE_IMAGE=ghcr.io/ublue-os/bazzite-nvidia-open
ARG BASE_TAG=stable

# Build context kept out of the final image
FROM scratch AS ctx
COPY build_files /build
COPY system_files /system

FROM ${BASE_IMAGE}:${BASE_TAG}

ARG KANTAN_VERSION=0.1.0
ARG KANTAN_EDITION=full
# Build stamp (date) and the address installed PCs update from (may be empty)
ARG KANTAN_BUILD=dev
ARG KANTAN_IMAGE=

RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=cache,dst=/var/log \
    --mount=type=tmpfs,dst=/tmp \
    KANTAN_VERSION=${KANTAN_VERSION} KANTAN_EDITION=${KANTAN_EDITION} \
    KANTAN_BUILD=${KANTAN_BUILD} KANTAN_IMAGE=${KANTAN_IMAGE} \
    bash /ctx/build/build.sh

RUN bootc container lint
