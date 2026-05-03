import json
from typing import Any

import aiofiles

from src.domain.interfaces.state_storage import StateStorage


class JsonFileStorage(StateStorage):
    def __init__(
        self,
        base_path: str = './workflow_states',
    ) -> None:
        self.base_path = base_path

    async def save(
        self,
        workflow_name: str,
        step_index: int,
        context: Any,  # noqa: ANN401
    ) -> None:
        data: dict[str, Any] = {
            'step_index': step_index,
            'context': context,
        }

        async with aiofiles.open(f'{self.base_path}/{workflow_name}.json', 'w') as file:
            await file.write(json.dumps(data, default=str))

    async def load(self, workflow_name: str) -> tuple[int, Any] | None:
        try:
            async with aiofiles.open(f'{self.base_path}/{workflow_name}.json', 'r') as file:
                data = json.loads(await file.read())
            return data['step_index'], data['context']
        except FileNotFoundError:
            return None
