"""
Finite State Machine (FSM) tracking experiment step transitions.
"""

from enum import Enum, auto
import time

class StepState(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    SKIPPED = auto()
    VIOLATED = auto()

class ExperimentStateMachine:
    """Deterministic state tracker enforcing sequential step progression."""
    def __init__(self, protocol_data: dict):
        self.protocol_id = protocol_data.get("protocol_id")
        self.steps = protocol_data.get("steps", [])
        self.current_step_index = 0
        self.step_states = {step["step_id"]: StepState.PENDING for step in self.steps}
        self.step_start_time = None

    def get_current_step(self):
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance_step(self):
        if self.current_step_index < len(self.steps):
            step_id = self.steps[self.current_step_index]["step_id"]
            self.step_states[step_id] = StepState.COMPLETED
            self.current_step_index += 1
            self.step_start_time = time.time()
            return True
        return False
