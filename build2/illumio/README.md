# Illumio Core for Kubernetes & OpenShift

- [Illumio Core for Kubernetes \& OpenShift](#illumio-core-for-kubernetes--openshift)
  - [Introduction](#introduction)
  - [Prerequisites](#prerequisites)
  - [Values](#values)
  - [Private Repository](#private-repository)
  - [Installation](#installation)
    - [Custom namespace](#custom-namespace)
  - [Uninstallation](#uninstallation)
  - [Migrate existing deployment](#migrate-existing-deployment)
    - [Annotate and label resource](#annotate-and-label-resource)
    - [Delete C-VEN DaemonSet](#delete-c-ven-daemonset)
- [Important Optional Parameters](#important-optional-parameters)
  - [Cluster Mode](#cluster-mode)
  - [CLAS storage](#clas-storage)
  - [Pod Priority](#pod-priority)
  - [NodePort traffic enforcement disabling](#nodeport-traffic-enforcement-disabling)
  - [Common Parameters](#common-parameters)
  - [Root CA Certificate](#root-ca-certificate)
  - [Kubelink nodeSelector](#kubelink-nodeselector)
  - [Image Pull Policy](#image-pull-policy)
  - [Resources](#resources)
  - [Metrics](#metrics)
    - [First installation with metrics](#first-installation-with-metrics)
    - [Upgrade and enable metrics](#upgrade-and-enable-metrics)
    - [Upgrade with enabled metrics](#upgrade-with-enabled-metrics)
    - [InfluxDB parameters](#influxdb-parameters)
- [CLAS Features](#clas-features)
  - [Degraded Mode](#degraded-mode)
  - [Flat Network Support](#flat-network-support)
  - [Wait for Policy](#wait-for-policy)
  - [Support bundle](#support-bundle)
  - [Kubernetes workload metadata](#kubernetes-workload-metadata)
  - [Workloads in host network](#workloads-in-host-network)
  - [Label-set optimized policy](#label-set-optimized-policy)
  - [Firewall backend](#firewall-backend)
- [Parameters](#parameters)

## Introduction

This chart helps with the deployment of Illumio Core for Kubernetes or OpenShift on your distributed, on-premises systems.

Disclaimer: Copyright 2024 Illumio, Inc. All Rights Reserved.

[Overview of Illumio Products](https://www.illumio.com/products)

[Core Concepts](https://docs.illumio.com/core/23.5/Content/Guides/kubernetes-and-openshift/overview/concepts.htm)

[Product Guide](https://docs.illumio.com/core/23.5/Content/LandingPages/Guides/kubernetes-and-openshift.htm)

[Installation Guide](https://docs.illumio.com/core/23.5/Content/Guides/kubernetes-and-openshift/deployment-helm/_ch-deployment-helm.htm)

## Prerequisites

1. Deploy and configure PCE
2. [Create Cluster in PCE](https://docs.illumio.com/core/23.5/Content/Guides/kubernetes-and-openshift/deployment-helm/create-a-container-cluster-in-the-pce.htm)
3. [Create pairing profile in PCE](https://docs.illumio.com/core/23.5/Content/Guides/kubernetes-and-openshift/deployment-helm/create-a-pairing-profie-for-your-cluster-nodes.htm)
4. [Install this chart](#Installation)

[Full List of Supported Configurations:](https://docs.illumio.com/core/23.5/Content/Guides/kubernetes-and-openshift/deployment/host-and-cluster-requirements.htm)

| Component  | Description                                 | Value      |
| :--------- | :------------------------------------------ | :--------- |
| Kubernetes | Minimal supported Kubernetes version        | `>=1.20`   |
| OpenShift  | Minimal supported OpenShift version         | `>=4.8`    |
| PCE        | Policy Compute Engine (deployed separately) | `>=21.5.x` |

According to official [Helm documentation](#https://helm.sh/docs/topics/registries/#enabling-oci-support), if the version of Helm is lower than `3.8.0`, following command must be executed in the installation environment:

```bash
$ export HELM_EXPERIMENTAL_OCI=1
```

## Values

Prepare the `illumio-values.yaml` file in advance, making sure it contains the following mandatory parameters:

```yaml
pce_url: URL_PORT                 # PCE URL with port, e.g. mypce.example.com:8443
cluster_id: ILO_CLUSTER_UUID      # Cluster ID from PCE, e.g. cc4997c1-40...
cluster_token: ILO_CLUSTER_TOKEN  # Cluster Token from PCE, e.g. 1_170b...
cluster_code: ILO_CODE            # Pairing Profile key from PCE, e.g. 1391c...
containerRuntime: containerd      # Container runtime engine used in cluster, 
                                  #   allowed values are [containerd, crio, k3s_containerd]
containerManager: kubernetes      # Container manager used in cluster, 
                                  #   allowed values are [kubernetes, openshift]
```

## Private Repository

If the infrastructure requires the use of private repository, contact Illumio Support for further asssistance.

## Installation

If you are looking to migrate an already existing Illumio installation to a Helm chart, refer to section [Migrate existing deployment](#Migrate existing deployment)

In case the `illumio-system` namespace already exists, omit the `--create-namespace` flag.

```bash
$ helm install illumio -f illumio-values.yaml oci://quay.io/illumio/illumio --version 5.7.0 --namespace illumio-system --create-namespace
```

### Custom namespace

Historically, it was expected that IC4K would be installed in the `illumio-system` namespace. From version 5.7.0, it is possible to install the release into a custom namespace. The release namespace is overridden by default for backward compatibility using the variable `namespaceOverride: illumio-system`.

Unset this variable, and the chart will be installed into `.Release.Namespace` specified as helm parameter. Example to install into "ilo" namespace:

```bash
$ helm install illumio -f illumio-values.yaml oci://quay.io/illumio/illumio --version 5.7.0 --namespace ilo --create-namespace --set namespaceOverride=null
```

Or:

```bash
$ helm install illumio -f illumio-values.yaml oci://quay.io/illumio/illumio --version 5.7.0 --namespace ilo --create-namespace --set namespaceOverride=ilo
```

## Uninstallation

Due to the nature of Illumio C-VEN, uninstalling the Illumio Helm chart release takes around 2 minutes to complete. Uninstallation will also unpair C-VENs from PCE.

```bash
$ helm uninstall illumio --namespace illumio-system
$ kubectl delete namespace illumio-system
```

When chart is deployed using ArgoCD, there is no pre-delete hook that unpairs C-VENs, and unpair must be done by changing `clusterMode` value to `unpair`. After all C-VEN Workloads are removed from PCE, it's safe to delete IC4K from the cluster.

From version `5.7.0`, the chart and C-VEN support unpairing with VEN tampering protection enabled. The valid maintenance token must be in `cven.maintenanceToken` variable. Steps to unpair K8s cluster:

**Using ArgoCD:**

- set `clusterMode` to `unpair` and set valid maintenance token to `cven.maintenanceToken`
- perform Sync
- delete application after all C-VEN Workloads are removed from PCE

**Using Helm:**

- set valid maintenance token to `cven.maintenanceToken`
- run `helm upgrade` to apply the change
- run `helm uninstall`

## Migrate existing deployment

This section describes the steps to migrate a manually deployed Illumio installation to a Helm managed deployment. For upgrading Helm installation to a newer version, follow standard Helm practice with `helm upgrade` command.

The migration from manually deployed Illumio to Helm chart has to be done in 3 steps:

1. [Annotate and label resources](#Annotate and label resources)
2. [Delete C-VEN DaemonSet](#Delete C-VEN DaemonSet)
3. [Install Helm chart](#Installation)

### Annotate and label resource

From version `3.0.0` Helm supports _adopting_ already deployed resources with correct name, annotations and labels.
Required annotations and labels are:

```yaml
annotations:
  meta.helm.sh/release-name: illumio
  meta.helm.sh/release-namespace: illumio-system
labels:
  app.kubernetes.io/managed-by: Helm
```

To annotate and label all Illumio resources, use the commands below (provided the names of resources match your deployment). Note the `--overwrite` flag which will replace any existing ownership annotations that might be already assigned.

```bash
kubectl -n illumio-system annotate secret illumio-ven-config meta.helm.sh/release-name=illumio --overwrite
kubectl -n illumio-system annotate secret illumio-ven-config meta.helm.sh/release-namespace=illumio-system --overwrite
kubectl -n illumio-system label secret illumio-ven-config app.kubernetes.io/managed-by=Helm --overwrite
kubectl -n illumio-system annotate secret illumio-kubelink-config meta.helm.sh/release-name=illumio --overwrite
kubectl -n illumio-system annotate secret illumio-kubelink-config meta.helm.sh/release-namespace=illumio-system --overwrite
kubectl -n illumio-system label secret illumio-kubelink-config app.kubernetes.io/managed-by=Helm --overwrite
kubectl -n illumio-system annotate secret illumio-secret meta.helm.sh/release-name=illumio --overwrite
kubectl -n illumio-system annotate secret illumio-secret meta.helm.sh/release-namespace=illumio-system --overwrite
kubectl -n illumio-system label secret illumio-secret app.kubernetes.io/managed-by=Helm --overwrite
kubectl -n illumio-system annotate configmap illumio-config meta.helm.sh/release-name=illumio --overwrite
kubectl -n illumio-system annotate configmap illumio-config meta.helm.sh/release-namespace=illumio-system --overwrite
kubectl -n illumio-system label configmap illumio-config app.kubernetes.io/managed-by=Helm --overwrite
kubectl -n illumio-system annotate serviceaccount illumio-ven meta.helm.sh/release-name=illumio --overwrite
kubectl -n illumio-system annotate serviceaccount illumio-ven meta.helm.sh/release-namespace=illumio-system --overwrite
kubectl -n illumio-system label serviceaccount illumio-ven app.kubernetes.io/managed-by=Helm --overwrite
kubectl -n illumio-system annotate clusterrole illumio-kubelink meta.helm.sh/release-name=illumio --overwrite
kubectl -n illumio-system annotate clusterrole illumio-kubelink meta.helm.sh/release-namespace=illumio-system --overwrite
kubectl -n illumio-system label clusterrole illumio-kubelink app.kubernetes.io/managed-by=Helm --overwrite
kubectl -n illumio-system annotate clusterrolebinding illumio-ven meta.helm.sh/release-name=illumio --overwrite
kubectl -n illumio-system annotate clusterrolebinding illumio-ven meta.helm.sh/release-namespace=illumio-system --overwrite
kubectl -n illumio-system label clusterrolebinding illumio-ven app.kubernetes.io/managed-by=Helm --overwrite
kubectl -n illumio-system annotate clusterrole illumio-ven meta.helm.sh/release-name=illumio --overwrite
kubectl -n illumio-system annotate clusterrole illumio-ven meta.helm.sh/release-namespace=illumio-system --overwrite
kubectl -n illumio-system label clusterrole illumio-ven app.kubernetes.io/managed-by=Helm --overwrite
kubectl -n illumio-system annotate serviceaccount illumio-kubelink meta.helm.sh/release-name=illumio --overwrite
kubectl -n illumio-system annotate serviceaccount illumio-kubelink meta.helm.sh/release-namespace=illumio-system --overwrite
kubectl -n illumio-system label serviceaccount illumio-kubelink app.kubernetes.io/managed-by=Helm --overwrite
kubectl -n illumio-system annotate deployment illumio-kubelink meta.helm.sh/release-name=illumio --overwrite
kubectl -n illumio-system annotate deployment illumio-kubelink meta.helm.sh/release-namespace=illumio-system --overwrite
kubectl -n illumio-system label deployment illumio-kubelink app.kubernetes.io/managed-by=Helm --overwrite
kubectl -n illumio-system annotate clusterrolebinding illumio-kubelink meta.helm.sh/release-name=illumio --overwrite
kubectl -n illumio-system annotate clusterrolebinding illumio-kubelink meta.helm.sh/release-namespace=illumio-system --overwrite
kubectl -n illumio-system label clusterrolebinding illumio-kubelink app.kubernetes.io/managed-by=Helm --overwrite
```

The output should look similar to this:

```bash
...
clusterrolebinding.rbac.authorization.k8s.io/illumio-kubelink annotated
clusterrolebinding.rbac.authorization.k8s.io/illumio-kubelink annotated
clusterrolebinding.rbac.authorization.k8s.io/illumio-kubelink labeled
```

### Delete C-VEN DaemonSet

The next step in upgrading an older release to a Helm managed one is removing the C-VEN DaemonSet. Save any custom labels and validations included in the DaemonSet and reapply them later.

```bash
kubectl delete daemonset illumio-ven -n illumio-system
```

The last remaining step is installing Helm chart, follow the steps in [Installation](#Installation) section. Filling in the fields in `illumio-values.yaml` is still mandatory.

# Important Optional Parameters

Disclaimer: Users are discouraged from editing or adding other values besides those mentioned in this README file.

## Cluster Mode

This parameter selects the mode in which Illumio system handles the cluster. Supported values:

- `legacy` - the default, PCE manages individual Pods as Container Workloads
- `clas` - Cluster Local Actor Store, PCE manages cluster workloads as Kubernetes Workloads
- `migrateLegacyToClas` - use for upgrade to CLAS mode, see Product Guide
- `migrateClasToLegacy` - use for downgrade from CLAS mode, see Product Guide
- `unpair` - unpair C-VENs from PCE before deletion

```yaml
clusterMode: legacy
```

## CLAS storage

Kubelink in CLAS mode uses etcd as a local cache for policy and runtime data. Variable `storage.sizeGi` is used to set the size of ephemeral storage.

```yaml
storage:
  registry: "quay.io/illumio"
  repo: "storage"
  imageTag: "3.6.6"
  imagePullPolicy: "IfNotPresent"
  sizeGi: 1
```

## Pod Priority

Kubelink Pod and CVEN Pods have `priorityClassName` specified by default. This can be disabled by setting `priorityClasses.enabled` to `false`. Default values of `priorityClassName` can be changed by setting `kubelink` and `cven` values.

```yaml
priorityClasses:
  enabled: true
  kubelink: system-cluster-critical
  cven: system-node-critical
```

## NodePort traffic enforcement disabling

Starting from C-VEN 22.5, NodePort ingress traffic is enforced by default. To allow NodePort traffic, additional policy rules are needed. If this behaviour is undesired, it can be controlled by setting `enforceNodePortTraffic: never`.

Default values:

```yaml
enforceNodePortTraffic: always
```

## Common Parameters

There is an option to specify Common Labels and Common Annotations in `illumio-values.yaml`:

```yaml
commonLabels: {} # Labels applied to all deployed objects
commonAnnotations: {} # Annotations applied to all deployed objects
```

## Root CA Certificate

[Reference Root CA Certificate](https://product-docs-repo.illumio.com/Tech-Docs/Containers/out/en/kubernetes-and-openshift/deployment-with-helm-chart--kubernetes-3-0-0-and-later-/prepare-your-environment.html#UUID-f3f04455-bc60-8ec1-5043-e3b121c7847a_id_createaconfigmaptostoreyourrootcacertificatehelm)

If you are using a private PKI to sign the PCE certificate, make sure you add to `illumio-values.yaml` the references to the root CA certificate that signed the PCE certificate, as shown below:

```yaml
extraVolumeMounts:
  - name: root-ca
    mountPath: /etc/pki/tls/ilo_certs/
    readOnly: false
extraVolumes:
  - name: root-ca
    configMap:
      name: root-ca-config
```

## Kubelink nodeSelector

If the infrastructure requires Kubelink to run on the control-plane node, add the below configuration to `illumio-values.yaml` (the selector label or name may differ). Keep in mind that this only applies to Kubelink deployment.

```yaml
nodeSelector:
  node-role.kubernetes.io/control-plane: ""
```

Kubelink deployment also supports two more settings:

1. Option to ignore certificate verification of PCE
2. The verbosity level of logging

```yaml
ignore_cert: true
verbosity: 0
```

## Image Pull Policy

Illumio Core for Kubernetes & Openshift provides an option to specify default image pull policy for each of its components.

```yaml
kubelink:
  imagePullPolicy: "Always"
cven:
  imagePullPolicy: "Always"
```

## Resources

Resources limits and requests are defined as chart values for Kubelink Deployment and CVEN DaemonSet. Values for both components can be changed in `illumio-values.yaml`, and each `resources` section is used as a whole for the corresponding container, effectively replacing the default `resources` definition.

```yaml
kubelink:
  resources:
    limits:
      memory: 500Mi
    requests:
      memory: 200Mi
      cpu: 200m

cven:
  resources:
    limits:
      memory: 300Mi
    requests:
      memory: 100Mi
      cpu: 250m

storage:
  resources:
    limits:
      memory: 500Mi
    requests:
      memory: 200Mi
      cpu: 100m
```

## Metrics

Illumio Core for Kubernetes & OpenShift provides tools for collecting and visualization of runtime metrics since IC4K chart version 4.4. The chart contains InfluxDB as a dependency. To enable metrics use:

```yaml
metrics:
  enabled: true
```

Please refer to https://github.com/bitnami/charts/tree/main/bitnami/influxdb/ for a complete list of available parameters. To set a value in the `illumio-values.yaml` for InfluxDB subchart the `influxdb` section must be used.

> **Warning:** Secrets for the InfluxDB must be specified during the upgrade.

### First installation with metrics

Use the standard command, secrets will be generated.

```bash
$ helm install illumio -f illumio-values.yaml oci://quay.io/illumio/illumio --version 5.7.0 --namespace illumio-system --create-namespace
```

### Upgrade and enable metrics

To upgrade Illumio Core for Kubernetes & OpenShift deployed with the previous chart version or without metrics enabled, the user has to generate secrets for the version with enabled metrics.

```bash
export ADMIN_USER_PASSWORD=`LC_ALL=LC tr -dc A-Za-z0-9 </dev/urandom | head -c 20 ; echo`

export ADMIN_USER_TOKEN=`LC_ALL=LC tr -dc A-Za-z0-9 </dev/urandom | head -c 20 ; echo`

helm upgrade illumio -f illumio-values.yaml oci://quay.io/illumio/illumio --version 5.7.0 --namespace illumio-system --set influxdb.auth.admin.password=$ADMIN_USER_PASSWORD --set influxdb.auth.admin.token=$ADMIN_USER_TOKEN
```

### Upgrade with enabled metrics

To upgrade Illumio Core for Kubernetes & OpenShift deployed with enabled metrics user has to pass existing secrets.

```bash
export ADMIN_USER_PASSWORD=$(kubectl get secret --namespace illumio-system illumio-influxdb -o jsonpath="{.data.admin-user-password}" | base64 -d)

export ADMIN_USER_TOKEN=$(kubectl get secret --namespace illumio-system illumio-influxdb -o jsonpath="{.data.admin-user-token}" | base64 -d)

helm upgrade illumio -f illumio-values.yaml oci://quay.io/illumio/illumio --version 5.7.0 --namespace illumio-system --set influxdb.auth.admin.password=$ADMIN_USER_PASSWORD --set influxdb.auth.admin.token=$ADMIN_USER_TOKEN
```

### InfluxDB parameters

The InfluxDB deployed with default options will create a persistent volume with a capacity 8Gi and use the default storage class from the cluster. The current Illumio metrics data size for 1 day is approximately 55Mi, and the retention policy for the Illumio bucket is set to 30 days. 4Gi capacity should be enough room for Illumio metrics. Example setting:

```yaml
influxdb:
  persistence:
    size: 4Gi
    storageClass: kops-csi-1-21
```

Setting for disabling the metrics persistence:

```yaml
influxdb:
  persistence:
    enabled: false
```

# CLAS Features

## Degraded Mode

Kubelink running in CLAS mode delivers policy for Kubernetes Workloads even if the PCE is unavailable due to an upgrade, connectivity problems, or other reasons. In this degraded mode, new Pods of existing Workloads get the latest policy version cached in CLAS storage. When Kubelink detects a new Kubernetes Workload **labeled the same way and in the same namespace** as an existing Kubernetes Workload, it will deliver the existing, cached policy to Pods of this new Workload.

When Kubelink cannot find a cached policy (that is, when labels of a new Workload do not match those of any existing Workload in the same namespace), Kubelink delivers a "fail open" or "fail closed" policy based on the Helm Chart parameter `degradedModePolicyFail` setting, which can be specified in the illumio-values.yaml file when installing. The default parameter value is `open`, which opens the firewall of new Pods. The `closed` value means the firewall of new Pods is programmed to block all network connectivity. The actual behavior of `closed` depends on the Container Workload Profile's Enforcement setting: all connectivity is blocked if the Enforcement of the namespace is set to "Full".

When Kubelink detects the PCE is available again, it will synchronize policy and labels, and continue normal operation.

The degraded mode can be disabled by setting `disableDegradedMode: true` in illumio-values.yaml and performing `helm upgrade`. With disabled degraded mode, Kubelink/CLAS will not deliver policy based on matching labels. Kubelink will continue to run and deliver the cached policy to existing Workloads and not deliver the policy to new Workloads. It will keep retrying to communicate with PCE and continue normal operation after PCE is available again.

> **Note:** If the PCE was inaccessible due to database restoration or maintenance, we advise restarting Kubelink by deleting its Pod to synchronize the current state.

Default values:

```yaml
degradedModePolicyFail: open
disableDegradedMode: false
```

## Flat Network Support

Starting in version 5.2.0, the Kubelink Operator supports flat network CNIs in CLAS mode, a feature that was previously only available in non-CLAS mode. This update includes compatibility with flat network types such as Azure CNI Pod Subnet and Amazon VPC CNI. To enable a flat network CNI, set the `networkType` parameter to `flat` in the Helm Chart's `illumio-values.yaml` file during installation.

Also note that in CLAS-enabled flat networks, if a pod communicates with a virtual machine outside the cluster using private IP addresses, you must enable the annotation `meta.illumio.podIPObservability`. This is a scenario in which the virtual machine is in a private network and has an IP address from the same range as cluster nodes and pods. In this case, the PCE needs to know the private IP address of the pod to be able to open a connection on the virtual machine. The main benefit of CLAS is that the PCE no longer directly manages individual pods, so the implementation expects a specific annotation on such pods. Traffic between such private IPs will be blocked without this annotation, and will appear in the UI as blocked.

In this case, when the application communicates through private IPs, add the following annotation so that Kubelink can then report the private IPs of Kubernetes Workloads to the PCE:

```yaml
metadata:
  annotations:
    meta.illumio.podIPObservability: "true"
```

## Wait for Policy

With a new Wait For Policy feature, CLAS-enabled Kubelink can be configured to automatically and transparently delay the start of an application container in a pod until a policy is properly applied to that container. This synchronizes the benefit of automatic container creation with the protection of proper policy convergence into the new container.

This Wait For Policy feature replaces the existing local policy convergence controller, also known as a readiness gate. A readiness gate required manually adding the readinessGate condition into spec of Kubernetes workload. Wait For Policy uses an automatically injected init container, which requires no change to the user application.

The Wait For Policy feature is disabled by default. To enable it, change the `waitForPolicy: enabled` value to true in the Helm Chart illumio-values.yaml file.

For more information, see [Product Guide](https://docs.illumio.com/core/23.5/Content/LandingPages/Guides/kubernetes-and-openshift.htm)

## Support bundle

To assist the Illumio Support team with more details for troubleshooting, Kubelink 5.2.0 provides a support bundle that collects up to 2 GB of logs, metrics, and other data inside its pod. Future versions will add the option to upload these support bundles to the PCE. Currently, you must copy this support bundle by running the script `/support_bundle.sh` inside the Kubelink pod. The script generates debug data, creates a gzipped tar archive using `stdout` as output, and encodes this data using Base64.

Use the following command to generate and transfer the Kubelink support bundle from its pod:

```sh
kubectl -n illumio-system exec deploy/illumio-kubelink -- /support_bundle.sh | base64 -d > kubelink_support.tgz
```

## Kubernetes workload metadata

Kubelink reports Kubernetes workloads with its labels and annotations. Starting from Kubernetes Operator 5.4.0, only
Illumio annotations are reported. To include other annotation keys, use `userAllowedAnnotations` list:

```yaml
userAllowedAnnotations:
  - "deployment.kubernetes.io/revision"
```

## Workloads in host network

Starting from Kubernetes Operator 5.4.0, Kubelink does not create K8s Workload on PCE if the workload is in the host network. Pods of these workloads don't have separate network namespaces. Policy for these workloads must be part of the policy for Nodes. This was always the case, legacy non-CLAS mode works the same way.

For visibility, it's possible to turn on the reporting of workloads in the host network with the setting `reportHostNetworkKubernetesWorkloads: true`. Workloads will be counted into Workload limits, and policy instructions for Pods in the host network will be ignored like in previous versions.

## Label-set optimized policy

This optimization can reduce the size of the policy sent from PCE. Instead of sending policy for each Kubernetes workload, PCE groups policies using Kubernetes Workload PCE labels. Kubernetes Workloads with a unique set of PCE labels will not benefit from this optimization.

```yaml
policyLabelSetEnable: true
```

## Firewall backend

C-VEN is designed to automatically select the appropriate firewall CLI, choosing between nft and xtables-nft-multi/iptables-legacy. While manual backend selection is possible, it is generally not recommended.

Should a backend switch be necessary, you must first execute helm uninstall. This step is crucial for clearing old or unused firewall tables, which prevents potential conflicts. Successful operation of C-VEN depends on the chosen backend aligning with the one utilized by kube-proxy.

```yaml
firewallBackend: "nftables"
```



# Parameters

| Name                                       | Description                                                             | Default Value             | Accepted Values                                           |
| :----------------------------------------- | :---------------------------------------------------------------------- | :------------------------ | :-------------------------------------------------------- |
| `pce_url`                                  | URL connection to PCE with port                                         | `""`                      |                                                           |
| `cluster_id`                               | Cluster ID for created cluster in PCE                                   | `""`                      |                                                           |
| `cluster_token`                            | Cluster Token for created cluster in PCE                                | `""`                      |                                                           |
| `cluster_code`                             | Cluster Code from Pairing Profile                                       | `""`                      |                                                           |
| `namespaceOverride`                        | Override the namespace for Illumio resources                            | `"illumio-system"`        |                                                           |
| `containerRuntime`                         | Container Runtime used in cluster                                       | `"containerd"`            | `[containerd, crio, k3s_containerd]`                      |
| `containerManager`                         | Container Manager used in cluster                                       | `"kubernetes"`            | `[kubernetes, openshift]`                                 |
| `clusterMode`                              | See "Cluster Mode" section                                              | `"legacy"`                | `[legacy, migrateClasToLegacy,migrateLegacyToClas, clas]` |
| `enforceNodePortTraffic`                   | See "Cluster Mode" section                                              | `"always"`                | `[always, never]`                                         |
| `priorityClasses.enabled`                  | Enables priorityClassName                                               | `true`                    | `[true, false]`                                           |
| `priorityClasses.kubelink`                 | Kubelink Deployment priorityClassName                                   | `system-cluster-critical` |                                                           |
| `priorityClasses.cven`                     | CVEN DaemonSet priorityClassName                                        | `system-node-critical`    |                                                           |
| `degradedModePolicyFail`                   | See "CLAS Degraded Mode" section                                        | `"open"`                  | `[open, closed]`                                          |
| `disableDegradedMode`                      | Disable CLAS Degraded Mode                                              | `false`                   | `[true, false]`                                           |
| `reportHostNetworkKubernetesWorkloads`     | See "Workloads in host network" section                                 | `false`                   | `[true, false]`                                           |
| `imagePullSecret.username`                 | Username for connecting to quay.io registry                             | `""`                      |                                                           |
| `imagePullSecret.password`                 | Password for connecting to quay.io registry                             | `""`                      |                                                           |
| `commonLabels`                             | Add common labels to all deployed objects                               | `{}`                      |                                                           |
| `commonAnnotations`                        | Add common annotations to all deployed objects                          | `{}`                      |                                                           |
| `extraVolumeMounts`                        | PCE CA Certificates for Kubelink and C-VEN                              | `{}`                      |                                                           |
| `extraVolumes`                             | PCE CA Certificates for Kubelink and C-VEN                              | `{}`                      |                                                           |
| `ignore_cert`                              | Skip certificate verification of `pce_url` in Kubelink                  | `false`                   | `[true, false]`                                           |
| `networkType`                              | Cluster network type                                                    | `"overlay"`               | `[overlay, flat]`                                         |
| `verbosity`                                | Verbosity level for logs                                                | `0`                       | `[0, 1, 2]`                                               |
| `kubelink.imagePullPolicy`                 | Kubelink imagePullPolicy level                                          | `IfNotPresent`            | `[IfNotPresent, Always, Never]`                           |
| `cven.imagePullPolicy`                     | C-VEN imagePullPolicy level                                             | `IfNotPresent`            | `[IfNotPresent, Always, Never]`                           |
| `cven.hostBasePath`                        | Path for C-VEN data directory on Nodes (/opt/illumio_ven_data)          | `/opt`                    |                                                           |
| `cven.tolerations`                         | C-VEN Daemonset tolerations                                             | `array`                   | `array`                                                   |
| `cven.firewallBackend`                     | C-VEN firewall backend                                                  | `"auto"`                  | `["auto", "iptables", "nftables]`                         |
| `cven.aggressiveTamperingDetection`       | faster detection of unauthorized firewall changes                       | `false`                   | `[true, false]`                                           |
| `kubelink.pceApiTimeout`                   | HTTP request timeout, in seconds                                        | `1200`                    | `60 - 7200`                                               |
| `kubelink.pceApiMinBackoff`                | backoff delay before request retry, in seconds                          | `60`                      | `5 - 600`                                                 |
| `kubelink.pceApiMaxBackoff`                | max backoff delay, in seconds                                           | `240`                     | `60 - 1200`                                               |
| `kubelink.pceApiPolicyInterval`            | Interval for polling new policy, in seconds                             | `30`                      | `10 - 3600`                                               |
| `kubelink.lastAppliedPolicyUpdateInterval` | Interval for updating last applied policy timestamp, in seconds         | `120`                     | `5 - inf`                                                 |
| `kubelink.resources`                       | See "Resources" section                                                 | `object`                  |                                                           |
| `cven.resources`                           | See "Resources" section                                                 | `object`                  |                                                           |
| `storage.resources`                        | See "Resources" section                                                 | `object`                  |                                                           |
| `metrics.enabled`                          | Enable metrics                                                          | `false`                   | `[true, false]`                                           |
| `policyLabelSetEnable`                     | Enable label-set policy optimization                                    | `true`                    | `[true, false]`                                           |
| `argoCD`                                   | Chart is deployed with ArgoCD                                           | `false`                   | `[true, false]`                                           |
| `httpProxy`                                | HTTP proxy URL to be used for Kubelink and C-VEN requests               | `""`                      |                                                           |
| `useTLS`                                   | C-VENs to Kubelink gRPC communication is encrypted, if both supports it | `true`                    | `[true, false]`                                           |
