from functools import lru_cache
from pathlib import Path

import click

from .. import Workflow
from ..core import CachedFilesystem, Graph, get_spec_hashes, pass_context



@click.command()
@click.argument("targets", nargs=-1)
@pass_context
def serve(ctx, targets):
    """Touch output files to update timestamps.

    """
    workflow = Workflow.from_context(ctx)
    filesystem = CachedFilesystem()
    graph = Graph.from_targets(workflow.targets, filesystem)
    endpoints = filter_names(graph, targets) if targets else graph.endpoints()
    with get_spec_hashes(working_dir=ctx.working_dir, config=ctx.config) as spec_hashes:
        touch_workflow(endpoints, graph, spec_hashes)