#!/bin/bash
set -e

# Instala las llaves montadas desde el host (si existen)
if [ -f /ssh_keys/id_rsa.pub ]; then
    mkdir -p /home/hadoop/.ssh
    cp /ssh_keys/id_rsa     /home/hadoop/.ssh/id_rsa
    cp /ssh_keys/id_rsa.pub /home/hadoop/.ssh/id_rsa.pub
    cp /ssh_keys/id_rsa.pub /home/hadoop/.ssh/authorized_keys
    printf "Host *\n  StrictHostKeyChecking no\n  UserKnownHostsFile /dev/null\n" > /home/hadoop/.ssh/config
    chown -R hadoop:hadoop /home/hadoop/.ssh
    chmod 700 /home/hadoop/.ssh
    chmod 600 /home/hadoop/.ssh/id_rsa /home/hadoop/.ssh/authorized_keys /home/hadoop/.ssh/config
fi

# Hadoop necesita JAVA_HOME también para sesiones por ssh
echo "export JAVA_HOME=$JAVA_HOME" >> /opt/hadoop/etc/hadoop/hadoop-env.sh

/usr/sbin/sshd -D
