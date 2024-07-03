#!/usr/bin/env python3

# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

import pytest
from helpers import cli_deploy_bundle
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest, rendered_bundle):
    """
    Build the tempo bundle and deploy it in different modes.
    Assert on the unit status before any relations/configurations take place.
    """
    await cli_deploy_bundle(ops_test, str(rendered_bundle))
    await ops_test.model.wait_for_idle(status="active", timeout=1000, idle_period=90)


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
async def test_tls_overlay(ops_test: OpsTest, rendered_bundle):
    """
    Deploy the tempo bundle with tls overlay.
    Assert on the unit status before any relations/configurations take place.
    """
    overlays = ["overlays/tls-overlay.yaml"]
    await cli_deploy_bundle(ops_test, str(rendered_bundle), overlays=overlays)
    await ops_test.model.wait_for_idle(status="active", timeout=1000, idle_period=90)


# TODO: add tests for ingested traces
