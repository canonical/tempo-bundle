# Overview

This documents explains the processes and practices recommended for
contributing enhancements to the Tempo bundle.

- Generally, before developing enhancements to this charm, you should consider
  [opening an issue](https://github.com/canonical/tempo-bundle) explaining
  your use case.
- If you would like to chat with us about your use cases or proposed
  implementation, you can reach us on the
  [Charmhub Mattermost](https://chat.charmhub.io/charmhub/channels/charm-dev)
  or [Discourse](https://discourse.charmhub.io/).
- All enhancements require review before being merged.
  Apart from code quality and test coverage, the review will also take into
  account the Juju administrator user experience using the bundle.

## Development

This bundle is comprised of three charms:

- [tempo-coordinator-k8s](https://github.com/canonical/tempo-coordinator-k8s-operator/)
- [tempo-worker-k8s](https://github.com/canonical/tempo-worker-k8s-operator/)
- [s3-integrator](https://github.com/canonical/s3-integrator)

### Deploy with local charms

To deploy the bundle using only/some local charms, you need to [render](#render-bundle) the
[`bundle.yaml.j2`](bundle.yaml.j2) template while passing the charms' local paths as arguments to the render command.
Then, [deploy](#deploy-bundle) the rendered bundle as usual.

#### Render bundle with local charms

You can render a `bundle.yaml` using:

```shell
tox -e render-bundle -- --channel=edge \
  --coordinator=<PATH_TO_TEMPO_COORDINATOR_CHARM> \
  --s3=<PATH_TO_S3_INTEGRATOR_CHARM> \
  --worker=<PATH_TO_TEMPO_WORKER_CHARM>
```

#### Deploy bundle

Now,`juju add-model foo` and deploy the bundle with `juju deploy ./bundle.yaml --trust`

#### Deploy MinIO

For local dev/evaluation deployments, you can deploy MinIO to act as an S3 object storage and to provide S3 credentials to `s3-integrator`.

```shell
juju deploy minio --channel edge --trust  
juju config minio access-key=YOUR_MINIO_ACCESS_KEY  
juju config minio secret-key=YOUR_MINIO_SECRET  
```

Then, deploy MinIO client and setup buckets.

```shell
sudo snap install minio-client --edge --devmode
minio-client config host add local http://MINIO_IP_ADDRESS:9000 YOUR_MINIO_ACCESS_KEY YOUR_MINIO_SECRET
minio-client mb local/tempo
```

Then, configure `s3-integrator`.

```shell
juju config s3-integrator endpoint=http://MINIO_IP_ADDRESS:9000
juju config s3-integrator bucket=tempo
juju run s3-integrator/leader sync-s3-credentials access-key=YOUR_MINIO_ACCESS_KEY secret-key=YOUR_MINIO_SECRET
```

## Testing

By default, all charms are deployed from charmhub. Alternatively, you can pass
local paths (or alternative charm names) as
[command line arguments](tests/integration/conftest.py) to pytest.

For a pure bundle test, no arguments should be provided. This way, the bundle
yaml is rendered with default values (all charms deployed from charmhub).

```shell
tox -e integration
```

You can also specify the channel:

```shell
tox -e integration -- --channel=stable
```

To keep the model and applications running after the test suite has exited:

```shell
tox -e integration -- --keep-models
```
