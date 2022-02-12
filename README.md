# vagrank8s

Kubernetes nodes through Vagrant.

Spin up the master first, then the (2) nodes:

1. `cd master`
2. `vagrant up`
3. `cd ../node1`
4. `vagrant up`
5. `cd ../node2`
6. `vagrant up`


## Manual Regression Tests

These tests should all work and be performed when evaluating changes.
I've given them in script form as a concession towards eventual automation.
We have the vagrants so there's not a resource issue, running locally.

For reasons of clarity, time, and the expressiveness of natural language,
the tests shall remain minimally automated, as part of this readme. Though
it isn't mentioned here, as far as possible without access to the kubectl
server, commands run directly on the node should be transferable to all nodes
to prove bi-directional interoperability.



### An Echo Service

Do this first so that the addresses can be shared with nodes. Create the
service on port 8080:

```shell
kubectl create deployment hello-node --image=k8s.gcr.io/echoserver:1.10 --replicas=2
kubectl expose deployment hello-node --type=LoadBalancer --port=8080
```

Check ping and curl from each node get a response from the service (curl only,
won't ping) from any and all pods.

```shell
sleep 10
pod1_ip=`k get pod -l app=hello-node -o=custom-columns=IP:.status.podIP | sed -n '2 p'`
pod2_ip=`k get pod -l app=hello-node -o=custom-columns=IP:.status.podIP | sed -n '3 p'`
svc_ip=`k get svc hello-node -o=custom-columns=CLUSTER-IP:.spec.clusterIP | tail -n 1`
ping -c3 -W2 $pod1_ip
ping -c3 -W2 $pod2_ip
host_collection=""
for i in {1..10}; do
  hosty=($(curl -s $svc_ip:8080 | grep Hostname))
  host_collection+=" ${hosty[1]}"
done
echo $host_collection | tr " " "\n" | sort -u

# We must match these against the pod names from k get pods. Or, approximately:
echo $host_collection | tr " " "\n" | sort -u | [ $(wc -l) -eq 2 ] && echo "PASS" || echo "FAIL"
```

### Host Network Limitation

Create a number of these, replacing `shell-demo1` with `shell-demo{2,3}`

```shell
for i in {1..3}; do
cat << EOF | kubectl create -f -
apiVersion: v1
kind: Pod
metadata:
  name: shell-demo$i
spec:
  volumes:
  - name: shared-data
    emptyDir: {}
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: shared-data
      mountPath: /usr/share/nginx/html
  hostNetwork: true
  dnsPolicy: Default
EOF
done
```

Get pod status and you will see that each shares the IP of the node that hosts
it and as such each node fails to host more than one. Any pod unfortunate enough
to be created alongside an existing one will only attain "RUNNING" status for
a few seconds before failing with STATUS: `ERROR` until about 1 minute since
launching. After this minute it changes to `CrashLoopBackOff`.

Delete all but one of them:

```shell
for i in {2..3}; do
  kubectl delete pod shell-demo$i
done
```


### Network A Pod Sees

Get a disposable pod:

```shell
kubectl run curl-myone --image=radial/busyboxplus:curl -i --tty --rm
```

Check its IP with `ip a`. That's in the hosting node's subnet.

Check can ping pods and curl services in other subnets, on other nodes.

Automating with busyboxplus "worked" once:
```shell
kubectl run curl-myone --image=radial/busyboxplus:curl -ti --rm -- sh -c "curl 10.244.1.2:8080"
```
But don't use it because it will forever after moan about:
`Internal error occurred: error attaching to container: container is in CONTAINER_EXITED state`


Instead we can use shell-demo1 from before:

```shell
kubectl exec -ti shell-demo1 -- /bin/bash -c "curl $svc_ip:8080"
host_collection=""
for i in {1..10}; do
  hosty=($(kubectl exec -ti shell-demo1 -- /bin/bash -c "curl $svc_ip:8080" | grep Hostname))
  host_collection+=" ${hosty[1]}"
done
echo $host_collection | tr " " "\n" | sort -u
echo $host_collection | tr " " "\n" | sort -u | [ $(wc -l) -eq 2 ] && echo "PASS" || echo "FAIL"
kubectl exec -ti shell-demo1 -- /bin/bash -c "apt-get update && apt-get install iputils-ping -y"
kubectl exec -ti shell-demo1 -- /bin/bash -c "ping -c3 -W2 $pod1_ip"
kubectl exec -ti shell-demo1 -- /bin/bash -c "ping -c3 -W2 $pod2_ip"
kubectl exec -ti shell-demo1 -- /bin/bash -c "curl -s $svc_ip:8080 | grep Hostname"
```
