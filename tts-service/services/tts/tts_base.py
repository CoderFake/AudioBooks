from abc import ABC, abstractmethod
from typing import Optional


class TTSBase(ABC):
    @abstractmethod
    async def synthesize(self, text: str, output_file: str) -> None:
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        pass

    @property
    @abstractmethod
    def supported_voices(self) -> list:
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> list:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass