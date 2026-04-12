from pydantic import BaseModel


class Action(BaseModel):
    aimed_layer: str
    clock_frequency_ratio: float
    aimed_receiver: str
    bandwidth_ratio: float