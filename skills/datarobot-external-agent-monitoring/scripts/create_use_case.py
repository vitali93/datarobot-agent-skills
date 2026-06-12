#!/usr/bin/env python3
# Copyright (c) 2026 DataRobot, Inc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Resolve a DataRobot Use Case to use as the OTel telemetry target.

A Use Case is the default (primary) telemetry entity for external agent
monitoring: telemetry is associated with it via the `experiment_container`
entity type, and traces appear under the Use Case's Tracing tab. This works
for both DataRobot-native agents and agents built elsewhere (brownfield).

Two modes:
    --use-case-id <id>   Validate an existing Use Case the user already has.
    --name "<name>"      Create a new Use Case (when the user has none yet).

Usage:
    python create_use_case.py --name "My Agent Monitoring"
    python create_use_case.py --use-case-id 6123abc...

Env vars:
    DATAROBOT_API_TOKEN  - DataRobot API token
    DATAROBOT_ENDPOINT   - DataRobot API endpoint (e.g. https://app.datarobot.com/api/v2)
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import datarobot as dr


def _base_url(api_endpoint: str) -> str:
    """Strip a trailing /api/v2 to get the instance base URL."""
    base = api_endpoint.rstrip("/")
    if base.endswith("/api/v2"):
        base = base[: -len("/api/v2")]
    return base


def _result(use_case: dr.UseCase, api_endpoint: str) -> dict:
    """Build the telemetry-target descriptor for a Use Case."""
    base = _base_url(api_endpoint)
    return {
        "use_case_id": use_case.id,
        "entity_id": f"experiment_container-{use_case.id}",
        "otel_endpoint": f"{base}/otel",
        "tracing_url": f"{base}/usecases/{use_case.id}/tracing",
    }


def resolve_use_case(
    name: str | None, description: str | None, use_case_id: str | None
) -> dict:
    """Validate an existing Use Case or create a new one for telemetry.

    Args:
        name: Display name for a Use Case to create (create mode).
        description: Optional description for the new Use Case (auto if omitted).
        use_case_id: Existing Use Case ID to validate and reuse (validate mode).

    Returns:
        Dict with use_case_id, entity_id, otel_endpoint, and tracing_url.
    """
    token = os.getenv("DATAROBOT_API_TOKEN")
    endpoint = os.getenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2")

    if not token:
        print("Error: DATAROBOT_API_TOKEN env var is required", file=sys.stderr)
        sys.exit(1)

    dr.Client(token=token, endpoint=endpoint)

    if use_case_id:
        # Validate mode: confirm the Use Case exists and is reachable.
        use_case = dr.UseCase.get(use_case_id)
    else:
        # Create mode: auto-describe when no description is provided.
        use_case = dr.UseCase.create(
            name=name,
            description=description
            or f"OTel telemetry target for external agent monitoring ({name})",
        )

    return _result(use_case, endpoint)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Resolve a DataRobot Use Case as an external agent OTel target"
    )
    parser.add_argument(
        "--name",
        help="Display name for a new Use Case (create mode)",
    )
    parser.add_argument(
        "--description",
        default="",
        help="Optional description for the new Use Case (auto-generated if omitted)",
    )
    parser.add_argument(
        "--use-case-id",
        dest="use_case_id",
        help="Existing Use Case ID to validate and reuse (validate mode)",
    )
    args = parser.parse_args()

    if not args.name and not args.use_case_id:
        print(
            "Error: provide either --use-case-id (existing) or --name (create new)",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        result = resolve_use_case(args.name, args.description, args.use_case_id)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
