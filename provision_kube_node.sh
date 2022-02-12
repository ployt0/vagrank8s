#!/usr/bin/env bash

set -e

apt-get update
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
cat <<EOF > /etc/apt/sources.list.d/kubernetes.list
deb https://apt.kubernetes.io/ kubernetes-xenial main
EOF
apt-get update
apt-get install -y kubelet=1.23.3-00 kubeadm=1.23.3-00 kubectl=1.23.3-00 containerd
apt-mark hold kubelet kubeadm kubectl

modprobe br_netfilter
echo "net.bridge.bridge-nf-call-iptables = 1" >> /etc/sysctl.conf
echo 1 > /proc/sys/net/ipv4/ip_forward
sysctl -p

cat /etc/systemd/system/kubelet.service.d/10-kubeadm.conf
sed -i "s/^\(ExecStart=.*\$KUBELET_EXTRA_ARGS *\)\$/\1 --node-ip=$1/" /etc/systemd/system/kubelet.service.d/10-kubeadm.conf
sudo systemctl daemon-reload
sudo systemctl restart kubelet
