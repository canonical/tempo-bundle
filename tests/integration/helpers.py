# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
import inspect
import logging
import os
from pathlib import Path
from typing import List, Union

from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


def get_this_script_dir() -> Path:
    filename = inspect.getframeinfo(inspect.currentframe()).filename  # type: ignore[arg-type]
    path = os.path.dirname(os.path.abspath(filename))
    return Path(path)


async def cli_deploy_bundle(
    ops_test: OpsTest, name: str, *, channel: str = "edge", overlays: List[Union[str, Path]] = None
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
    if not Path(name).is_file():
        run_args.append(f"--channel={channel}")

    retcode, stdout, stderr = await ops_test.run(*run_args)
    assert retcode == 0, f"Deploy failed: {(stderr or stdout).strip()}"
    logger.info(stdout)
