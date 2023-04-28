import logging
from typing import Any, List

logger = logging.getLogger(__name__)


class EntryProcessor:
    async def aprocess(self,
                       entry: Any,
                       ) -> List[Any]:
        pass


class PassthruProcessor(EntryProcessor):
    async def aprocess(self,
                       entry: Any,
                       ) -> List[Any]:
        return [entry]
