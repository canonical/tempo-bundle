# Tempo bundle

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [Tempo bundle](#tempo-bundle)
    - [Usage](#usage)
        - [Monolithic deployment](#monolithic-deployment)
    - [Overlays](#overlays)
    - [Publishing](#publishing)

<!-- markdown-toc end -->



[Tempo](https://grafana.com/oss/tempo/) is is a distributed tracing backend by Grafana, supporting Jaeger, Zipkin, and OpenTelemetry protocols.

Tempo is a single binary that can be configured to run in several modes to take up different roles in the ingestion/read pipeline, such as `distributor`, `compactor` and so on, [read the official docs for a more detailed explanation.](https://grafana.com/docs/tempo/latest/operations/architecture/#tempo-architecture).

Charmed Tempo consists of two charms, a [coordinator](https://github.com/canonical/tempo-coordinator-k8s-operator) and a [worker](https://github.com/canonical/tempo-worker-k8s-operator).

The coordinator is responsible for creating the configuration files for each worker and deciding whether the cluster is in a coherent state, based on the roles that each worker has adopted.

Several worker applications can be deployed and related to the coordinator, taking on different roles and enabling independent scalability of the various components of the stack.

The coordinator charm acts as a single access point for bundle-level integrations, such as TLS, ingress, self-monitoring, etc..., and as a single source of truth for bundle-level configurations that otherwise would have to be repeated (and kept in sync) between the individual worker nodes.


This Juju bundle deploys Tempo and a small object storage server, consisting of the following interrelated charmed operators:

- [Tempo Coordinator](https://charmhub.io/tempo-coordinator-k8s) ([source](https://github.com/canonical/tempo-coordinator-k8s-operator))
- [Tempo Worker](https://charmhub.io/tempo-worker-k8s) ([source](https://github.com/canonical/tempo-worker-k8s-operator))
- [s3integrator](https://charmhub.io/s3-integrator) ([source](https://github.com/canonical/s3-integrator))

This bundle is under development.
Join us on:

- [Discourse](https://charmhub.io/topics/canonical-observability-stack)
- [Matrix chat](https://matrix.to/#/#cos:ubuntu.com)

## Usage

Before deploying the bundle you may want to create a dedicated model for Tempo components:

```shell
juju add-model tempo
```

### Monolithic deployment
The bundle deploys Tempo in its [monolithic mode](https://grafana.com/docs/tempo/latest/setup/deployment/#monolithic-mode), which runs all required components in a single process and is the default mode of operation. Monolithic mode is the simplest way to deploy Grafana Tempo and is useful if you want to get started quickly or want to work with Grafana Tempo in a development environment.

```shell
tox -e render-bundle -- bundle.yaml
juju deploy ./bundle.yaml --trust
```

The bundle will deploy:

- 3 `tempo-worker` units (`tempo-worker-k8s` charm)
- 1 `coordinator` unit (`tempo-coordinator-k8s` charm)
- 1 `s3-integrator` unit (`s3-integrator` charm)

[note]
The default number of worker units is an odd number to prevent split-brain situations, and greater than 1 for the deployment to be HA.
[/note]


## Overlays

We also make available some [**overlays**](https://juju.is/docs/sdk/bundle-reference) for convenience:

* the [`tls` overlay](https://github.com/canonical/tempo-bundle/blob/main/overlays/tls-overlay.yaml) adds an internal CA to encrypt all inter-workload communications.

In order to use the overlays above, you need to:

1. Download the overlays (or clone the repository)
2. Pass the `--overlay <path-to-overlay-file-1> --overlay <path-to-overlay-file-2> ...` arguments to the `juju deploy` command

For example, to deploy the Tempo bundle with the tls overlay, you would do the following:

```sh
curl -L https://raw.githubusercontent.com/canonical/tempo-bundle/main/overlays/tls-overlay.yaml -O
juju deploy tempo-bundle --channel=edge --trust --overlay ./tls-overlay.yaml
```

## Publishing
```shell
./render_bundle.py bundle.yaml --channel=edge
charmcraft pack
charmcraft upload tempo-bundle.zip
charmcraft release tempo-bundle --channel=edge --revision=1
```
