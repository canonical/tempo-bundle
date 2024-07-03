# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
import logging
import subprocess
from pathlib import Path

import pytest
from helpers import get_this_script_dir

logger = logging.getLogger(__name__)

SCALING_MONOLITHIC = "scaling-monolithic"
MINIMAL_MIRCOSERVICES = "minimal-microservices"
RECOMMENDED_MIRCOSERVICES = "recommended-microservices"


def pytest_addoption(parser):
    """
    Adds an option "mode" to run the tests using different modes.
    """
    parser.addoption(
        "--mode",
        action="store",
        default="scaling-monolithic",
        help="Choose which `mode` of the tempo-bundle to run the tests on.",
        choices=(SCALING_MONOLITHIC, MINIMAL_MIRCOSERVICES, RECOMMENDED_MIRCOSERVICES),
    )


@pytest.fixture()
def rendered_bundle(pytestconfig) -> Path:
    """Returns the pathlib.Path for the bundle file generated.
    request.param will hold the different modes to run the tempo bundle in.
    """

    # get mode from passed config option
    mode = pytestconfig.getoption("mode")
    # build bundle.yaml
    cmd = [
        "/usr/bin/env",
        "python3",
        f"{get_this_script_dir()}/../../render_bundle.py",
        f"{get_this_script_dir()}/../../bundle.yaml",
        "--channel=edge",
        f"--mode={mode}",
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.error(e.stdout.decode())
        raise e

    bundle_path = get_this_script_dir() / ".." / ".." / "bundle.yaml"
    if not bundle_path.exists():
        raise FileNotFoundError("Expected a 'bundle.yaml' to be present")

    return bundle_path


@pytest.fixture()
def expected_layout(pytestconfig) -> dict:
    """
    Returns the expected deployment layout of apps and unit replicas of the current mode of operation.
    """
    # get mode from passed config option
    mode = pytestconfig.getoption("mode")
    if mode == RECOMMENDED_MIRCOSERVICES or mode == MINIMAL_MIRCOSERVICES:
        return {
            "tempo-worker-querier": 1,
            "tempo-worker-query-frontend": 1,
            "tempo-worker-ingester": 1,
            "tempo-worker-distributor": 1,
            "tempo-worker-compactor": 1,
            "tempo-worker-metrics-generator": 1,
            "s3-integrator": 1,
            "tempo": 1,
        }

    return {
        "tempo-worker": 3,
        "s3-integrator": 1,
        "tempo": 1,
    }
