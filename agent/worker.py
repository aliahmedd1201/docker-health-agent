"""Temporal worker: polls the task queue and runs workflows and activities."""
import asyncio
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker

import activities as a
from config import TASK_QUEUE, TEMPORAL_HOST
from workflows import AutoHealWorkflow, DockerMonitorWorkflow


async def main():
    client = await Client.connect(TEMPORAL_HOST)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[DockerMonitorWorkflow, AutoHealWorkflow],
        activities=[a.plan_action, a.analyze, a.list_containers,
                    a.check_health, a.get_logs, a.restart_container],
        activity_executor=ThreadPoolExecutor(max_workers=5),  # activities are sync
    )
    print(f"Worker listening on '{TASK_QUEUE}' at {TEMPORAL_HOST}", flush=True)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
