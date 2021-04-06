#!/bin/bash
export PATH=/shell/bin:${PATH}

kubectl config --kubeconfig=config-demo set-cluster K8_CLUSTER --server="$1" --insecure-skip-tls-verify
kubectl config --kubeconfig=config-demo set-credentials token --token="$2"
kubectl config --kubeconfig=config-demo set-context K8 --cluster=K8_CLUSTER --user=token --namespace="$3"
export KUBECONFIG=config-demo
kubectl config use-context K8
if [ -n "$4" ]; then
    kubectl exec -it "$4" -- sh -c "clear; (bash || ash || sh)"
else
    bash
fi
