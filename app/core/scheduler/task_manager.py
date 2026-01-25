import asyncio
from datetime import datetime


class AppTask:
    def __init__(self, task_name: str, task: asyncio.Task) -> None:
        self.task_name = task_name
        self.task = task


class TaskManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self.tasks: list[AppTask] = []

    def add_task(self, task_name: str, task: asyncio.Task) -> None:
        self.tasks.append(AppTask(task_name, task))

    async def run_tasks(self) -> None:
        await asyncio.gather(*[task.task for task in self.tasks])


def get_task_manager_with_default_task() -> TaskManager:
    return TaskManager()
