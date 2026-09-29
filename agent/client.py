"""Command-line client.

    python client.py "is backend healthy?"   ask a question
    python client.py heal                    run one auto-heal pass now
    python client.py schedule [minutes]      run auto-heal automatically (default: every 2 min)
"""
import asyncio
import sys
import uuid
from datetime import timedelta

from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleAlreadyRunningError,
    ScheduleIntervalSpec,
    ScheduleSpec,
)

from config import TASK_QUEUE, TEMPORAL_HOST
from workflows import AutoHealWorkflow, DockerMonitorWorkflow

SCHEDULE_ID = "autoheal-schedule"


async def create_schedule(client: Client, minutes: int) -> str:
    schedule = Schedule(
        action=ScheduleActionStartWorkflow(
            AutoHealWorkflow.run, id="autoheal-scheduled", task_queue=TASK_QUEUE),
        spec=ScheduleSpec(intervals=[ScheduleIntervalSpec(every=timedelta(minutes=minutes))]),
    )
    try:
        await client.create_schedule(SCHEDULE_ID, schedule)
        return f"Schedule '{SCHEDULE_ID}' created: auto-heal every {minutes} minute(s)."
    except ScheduleAlreadyRunningError:
        return f"Schedule '{SCHEDULE_ID}' already exists (see Schedules in the Temporal UI)."


async def main():
    client = await Client.connect(TEMPORAL_HOST)
    args = sys.argv[1:]
    run_id = uuid.uuid4().hex[:8]

    if args[:1] == ["schedule"]:
        minutes = int(args[1]) if len(args) > 1 else 2
        print(await create_schedule(client, minutes))
        return
    if args == ["heal"]:
        result = await client.execute_workflow(
            AutoHealWorkflow.run, id=f"autoheal-{run_id}", task_queue=TASK_QUEUE)
    else:
        question = " ".join(args) or "show container status"
        result = await client.execute_workflow(
            DockerMonitorWorkflow.run, question, id=f"ask-{run_id}", task_queue=TASK_QUEUE)

    print("\n".join(result) if isinstance(result, list) else result)


if __name__ == "__main__":
    asyncio.run(main())
