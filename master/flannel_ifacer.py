#!/usr/bin/env python3

"""
Equivalent kubectl commands are much less readable:
k get ds -n kube-system kube-flannel-ds -oyaml
k get ds -n kube-system kube-flannel-ds -o=custom-columns=IFACE:.spec.template.spec.containers[0].args
# Not sure of the next one:
kubectl patch ds -n kube-system kube-flannel-ds -p '{"spec":{"template":{"spec":{"containers":[{"name":"kube-flannel","args":"new args"}]}}}}'
"""

import sys

import yaml

iface_name = sys.argv[1]

with open("kube-flannel.yml") as f:
    eph_yaml = list(yaml.load_all(f, Loader=yaml.FullLoader))

ds = [x for x in eph_yaml if x["kind"] == "DaemonSet"][0]
container_args = ds["spec"]["template"]["spec"]["containers"][0]["args"]
iface_arg = "--iface={}".format(iface_name)
# Make it idempotent:
if iface_arg not in container_args:
    container_args.append(iface_arg)

with open("kube-flannel.yml", "w") as f:
  lded = yaml.dump_all(eph_yaml, f, default_flow_style=False)
