#!/usr/bin/env python3

# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

import pytest
from helpers import (
    S3_INTEGRATOR,
    cli_deploy_bundle,
    deploy_and_configure_minio,
    get_traces_patiently,
    get_unit_address,
)
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)

COORDINATOR = "tempo"


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest, rendered_bundle):
    """
    Build the tempo bundle and deploy it in different modes.
    Assert on the unit status before any relations/configurations take place.
    """
    await cli_deploy_bundle(ops_test, str(rendered_bundle))
    # they will remain on blocked, as s3 integrator didn't provide tempo with an endpoint yet.
    await ops_test.model.wait_for_idle(
        apps=[S3_INTEGRATOR, COORDINATOR], status="blocked", timeout=1000, idle_period=90
    )


@pytest.mark.abort_on_fail
async def test_deployment_layout(ops_test: OpsTest, expected_layout):
    """
    Test that the current mode's expected deployment layout is applied correctly.
    """

    deployed_apps = ops_test.model.applications
    assert len(expected_layout) == len(deployed_apps)
    for app_name, unit_no in expected_layout.items():
        deployed_app = deployed_apps.get(app_name, None)
        assert deployed_app is not None, f"expected application {app_name} is not deployed."
        assert (
            len(deployed_app.units) == unit_no
        ), f"expected replicated units for {app_name} is {unit_no}."


@pytest.mark.abort_on_fail
async def test_deployments_active(ops_test: OpsTest):
    """
    Configure an s3-compatible charm for Tempo to use as storage.
    Assert that after successful configurations, all workloads are in active/idle state.
    """

    await deploy_and_configure_minio(ops_test)
    await ops_test.model.wait_for_idle(status="active", timeout=1000, idle_period=90)


@pytest.mark.abort_on_fail
async def test_ingested_charm_traces(ops_test: OpsTest):
    """
    Test traces are getting injested into Tempo.
    """
    # adjust update-status interval to generate a charm tracing span faster
    await ops_test.model.set_config({"update-status-hook-interval": "30s"})
    coordinator_addr = await get_unit_address(ops_test, COORDINATOR, "0")
    assert await get_traces_patiently(coordinator_addr, "tempo-charm", False)

    # adjust back to the default interval time
    await ops_test.model.set_config({"update-status-hook-interval": "5m"})


@pytest.mark.abort_on_fail
async def test_tls_overlay(ops_test: OpsTest, rendered_bundle):
    """
    Deploy the tempo bundle with tls overlay.
    Assert on the unit status before any relations/configurations take place.
    """
    overlays = ["overlays/tls-overlay.yaml"]
    await cli_deploy_bundle(ops_test, str(rendered_bundle), overlays=overlays)
    await ops_test.model.wait_for_idle(status="active", timeout=1000, idle_period=90)


@pytest.mark.abort_on_fail
async def test_ingested_charm_traces_tls(ops_test: OpsTest):
    """
    Test traces are getting injested into Tempo while TLS is enabled.
    """
    # adjust update-status interval to generate a charm tracing span faster
    await ops_test.model.set_config({"update-status-hook-interval": "30s"})
    coordinator_addr = await get_unit_address(ops_test, COORDINATOR, "0")
    assert get_traces_patiently(coordinator_addr, "tempo-charm", True)

    # adjust back to the default interval time
    await ops_test.model.set_config({"update-status-hook-interval": "5m"})
