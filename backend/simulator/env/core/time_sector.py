from abc import ABC, abstractmethod

class TimeSector(ABC):
    def __init__(self, frequency: int):
        self.frequency = frequency  # slots per orbit
        self.counter = 0
        self.period = 0

    @abstractmethod
    def action(self) -> None:
        """每次 tick 时触发的动作，子类必须实现"""
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """每次 reset 时触发的动作，子类必须实现"""
        raise NotImplementedError

    def init(self) -> None:
        self.action()

    def tick(self) -> None:
        self.counter += 1
        if self.counter >= self.frequency:
            self.period += 1
            self.counter = 0
            self.action()

    def reset(self) -> None:
        self.counter = 0
        self.period = 0
        self.clear()
