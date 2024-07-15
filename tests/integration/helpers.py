# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
import inspect
import json
import logging
import os
from pathlib import Path
from typing import List, Union

import requests
from juju.application import Application
from juju.unit import Unit
from minio import Minio
from pytest_operator.plugin import OpsTest
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)
MINIO = "minio"
BUCKET_NAME = "tempo"
S3_INTEGRATOR = "s3-integrator"
ACCESS_KEY = "accesskey"
SECRET_KEY = "secretkey"


async def get_unit_address(ops_test: OpsTest, app_name, unit_no):
    status = await ops_test.model.get_status()
    app = status["applications"][app_name]
    if app is None:
        assert False, f"no app exists with name {app_name}"
    unit = app["units"].get(f"{app_name}/{unit_no}")
    if unit is None:
        assert False, f"no unit exists in app {app_name} with index {unit_no}"
    return unit["address"]


async def deploy_and_configure_minio(ops_test: OpsTest):
    config = {
        "access-key": ACCESS_KEY,
        "secret-key": SECRET_KEY,
    }
    await ops_test.model.deploy(MINIO, channel="edge", trust=True, config=config)
    await ops_test.model.wait_for_idle(apps=[MINIO], status="active", timeout=2000)
    minio_addr = await get_unit_address(ops_test, MINIO, "0")

    mc_client = Minio(
        f"{minio_addr}:9000",
        access_key="accesskey",
        secret_key="secretkey",
        secure=False,
    )

    # create tempo bucket
    found = mc_client.bucket_exists(BUCKET_NAME)
    if not found:
        mc_client.make_bucket(BUCKET_NAME)

    # configure s3-integrator
    s3_integrator_app: Application = ops_test.model.applications[S3_INTEGRATOR]
    s3_integrator_leader: Unit = s3_integrator_app.units[0]

    await s3_integrator_app.set_config(
        {
            "endpoint": f"minio-0.minio-endpoints.{ops_test.model.name}.svc.cluster.local:9000",
            "bucket": BUCKET_NAME,
        }
    )

    action = await s3_integrator_leader.run_action("sync-s3-credentials", **config)
    action_result = await action.wait()
    assert action_result.status == "completed"


def get_traces(tempo_host: str, service_name, is_tls=False):
    req = requests.get(
        "https://" if is_tls else "http://" + tempo_host + ":3200/api/search",
        params={"service.name": service_name},
        verify=False,
    )
    assert req.status_code == 200
    return json.loads(req.text)["traces"]


@retry(stop=stop_after_attempt(10), wait=wait_exponential(multiplier=1, min=4, max=10))
async def get_traces_patiently(tempo_host, service_name, is_tls):
    return get_traces(tempo_host, service_name, is_tls)


def get_this_script_dir() -> Path:
    filename = inspect.getframeinfo(inspect.currentframe()).filename  # type: ignore[arg-type]
    path = os.path.dirname(os.path.abspath(filename))
    return Path(path)


async def cli_deploy_bundle(
    ops_test: OpsTest, name: str, *, overlays: List[Union[str, Path]] = None
):
    """Deploy bundle from charmhub or from file."""
    overlay_args = []
    if overlays:
        for overlay in overlays:
            overlay_args.extend(["--overlay", str(overlay)])

    run_args = [
        "juju",
        "deploy",
        "--trust",
        "-m",
        ops_test.model_full_name,
        name,
    ] + overlay_args

    retcode, stdout, stderr = await ops_test.run(*run_args)
    assert retcode == 0, f"Deploy failed: {(stderr or stdout).strip()}"
    logger.info("Output %s", stdout)
