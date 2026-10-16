"""The deterministic verifier: each tool's checks live in its own module, on contract instances."""

from contract import Task, Tool

from . import metrics, runs


class _List:
    verify_input = staticmethod(runs.verify_list_input)
    verify_output = staticmethod(runs.verify_list_output)


class _Run:
    verify_input = staticmethod(runs.verify_run_input)
    verify_output = staticmethod(runs.verify_run_output)


TOOLS = {Tool.LIST_RUNS: _List, Tool.GET_RUN: _Run, Tool.COMPUTE_METRICS: metrics}
# task -> its output's check, verify_task(arguments, output, reference, workspace)
TASKS = {Task.AUDIT_RUN: metrics.verify_task}


def verify_input(tool, value):
    return TOOLS[Tool(tool)].verify_input(value)


def verify_output(tool, input_value, output_value, workspace):
    return TOOLS[Tool(tool)].verify_output(input_value, output_value, workspace)


def verify_task(task, arguments, output, reference, workspace):
    return TASKS[Task(task)](arguments, output, reference, workspace)
