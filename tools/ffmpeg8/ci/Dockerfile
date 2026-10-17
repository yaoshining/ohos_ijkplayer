# Debian 官方 amd64 清单摘要；软件包固定于签名的不可变快照。
FROM debian@sha256:44bccdd61bf09a081b1db8c61cf49bfabf30ac7afcc970010137c0ab587b209c
RUN rm /etc/apt/sources.list.d/debian.sources /etc/apt/apt.conf.d/docker-clean && \
    printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20250204T000000Z/ bookworm main\ndeb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/20250204T000000Z/ bookworm-security main\n' > /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates build-essential clang bison flex m4 perl libparse-yapp-perl python3 pkg-config \
    autoconf automake autopoint libtool curl git unzip xz-utils rsync nasm patch && \
    mkdir -p /opt/host-provenance && \
    dpkg-query -W -f='${Package}\t${Version}\t${Architecture}\n' > /opt/host-provenance/packages.tsv && \
    sha256sum /var/cache/apt/archives/*.deb > /opt/host-provenance/deb-sha256.txt && \
    cp /etc/apt/sources.list /opt/host-provenance/sources.list
ENV LC_ALL=C TZ=UTC SOURCE_DATE_EPOCH=1755820644 PYTHONHASHSEED=1
WORKDIR /workspace
