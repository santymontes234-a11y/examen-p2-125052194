FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless python3 openssh-server openssh-client \
    curl ca-certificates procps \
    && rm -rf /var/lib/apt/lists/*

ENV HADOOP_VERSION=3.3.6
RUN curl -fsSL https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz \
    | tar -xz -C /opt \
    && ln -s /opt/hadoop-${HADOOP_VERSION} /opt/hadoop

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV HADOOP_HOME=/opt/hadoop
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

# Usuario sin contraseña de login (acceso solo por llave)
RUN useradd -m -s /bin/bash hadoop \
    && mkdir -p /run/sshd /data/input /data/output \
    && chown -R hadoop:hadoop /data /opt/hadoop-${HADOOP_VERSION}

# sshd: solo llaves, sin password
RUN sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config \
    && sed -i 's/^#\?PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 22
ENTRYPOINT ["/entrypoint.sh"]
