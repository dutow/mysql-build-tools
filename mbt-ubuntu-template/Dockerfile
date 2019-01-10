# A simple dockerfile for building MySQL / Percona server
# Source and build directories should be mounted under work
# Use with the work-with script

ARG ubuntuVersion
FROM ubuntu:$ubuntuVersion
ARG ubuntuVersionName
MAINTAINER Zsolt Parragi <zsolt.parragi@cancellar.hu>

RUN DEBIAN_FRONTEND=noninteractive\
    apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y build-essential git cmake ninja-build bison gdb \
            software-properties-common wget \
            libncurses5-dev libssl-dev libaio-dev libreadline-dev systemtap-sdt-dev libmecab-dev \
            zlib1g-dev libpam-dev libnuma-dev libwrap0-dev libldap2-dev libcurl4-openssl-dev \
            libprotobuf-dev protobuf-compiler \
            curl subversion git xterm valgrind libjemalloc-dev libjemalloc1 \
            python3-mysql.connector python3 vim \
            eatmydata subunit python-mysqldb libjson-perl devscripts debconf debhelper fakeroot \
            lsb-release perl po-debconf psmisc dh-systemd libzstd-dev

# install clang
RUN DEBIAN_FRONTEND=noninteractive\
    wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add - && \
    (if [ "$ubuntuVersionName" = "trusty" ] ; then \
       add-apt-repository -y ppa:ubuntu-toolchain-r/test ; \
       apt-add-repository "deb http://apt.llvm.org/$ubuntuVersionName/ llvm-toolchain-$ubuntuVersionName-4.0 main" ; \
       apt-get -yq purge cmake ; \
       wget -q https://cmake.org/files/v3.10/cmake-3.10.2-Linux-x86_64.sh ; \
       sh cmake-*.sh --skip-license ; \
       rm cmake-*.sh ; \
       cmake --version ; \
      fi) && \
    apt-add-repository "deb http://apt.llvm.org/$ubuntuVersionName/ llvm-toolchain-$ubuntuVersionName-5.0 main" && \
    apt-add-repository "deb http://apt.llvm.org/$ubuntuVersionName/ llvm-toolchain-$ubuntuVersionName-6.0 main" && \
    apt-get update && \
    apt-get install -y clang-4.0 clang-5.0 clang-6.0 lldb-5.0

# FixUID
RUN addgroup --gid 1000 docker && \
    adduser --uid 1000 --ingroup docker --home /home/docker --shell /bin/sh --disabled-password --gecos "" docker

RUN USER=docker && \
    GROUP=docker && \
    curl -SsL https://github.com/boxboat/fixuid/releases/download/v0.2/fixuid-0.2-linux-amd64.tar.gz | tar -C /usr/local/bin -xzf - && \
    chown root:root /usr/local/bin/fixuid && \
    chmod 4755 /usr/local/bin/fixuid && \
    mkdir -p /etc/fixuid && \
    printf "user: $USER\ngroup: $GROUP\n" > /etc/fixuid/config.yml

RUN \
    mkdir /work && \
    chown -R docker:docker /work

# Add vault binary
RUN wget -q -O vault.zip https://releases.hashicorp.com/vault/0.9.6/vault_0.9.6_linux_amd64.zip && \
    unzip vault.zip -d /usr/local/bin && \
    rm vault.zip 

USER docker:docker

# add an msanified libcxx for testing mysql with msan
# Note: doesn't really work - requires a patched clang / mysql
RUN mkdir /work/libcxx-msan-trunk/ && \
    cd /work/libcxx-msan-trunk/ && \
    svn co http://llvm.org/svn/llvm-project/llvm/trunk llvm && \
    (cd llvm/projects && svn co http://llvm.org/svn/llvm-project/libcxx/trunk libcxx) && \
    (cd llvm/projects && svn co http://llvm.org/svn/llvm-project/libcxxabi/trunk libcxxabi) && \
    mkdir -p build && cd build && \
    CC=clang-4.0 CXX=clang++-4.0 cmake ../llvm -DCMAKE_INSTALL_PREFIX=.. -DCMAKE_BUILD_TYPE=Release -DLLVM_USE_SANITIZER=Memory && \
    make install-libcxx install-libcxxabi

RUN mkdir /work/bin &&\
    cd /work/bin &&\
    wget https://llvm.org/svn/llvm-project/compiler-rt/trunk/lib/asan/scripts/asan_symbolize.py &&\
    chmod +x asan_symbolize.py

ENTRYPOINT ["fixuid"]

