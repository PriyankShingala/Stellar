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
        self.protocol_id = protocol_data.get("protocol_id", "UNKNOWN")
        self.title = protocol_data.get("title", "")
        self.steps = protocol_data.get("steps", [])
        self.current_step_index = 0
        self.step_states = {step["step_id"]: StepState.PENDING for step in self.steps}
        if self.steps:
            self.step_states[self.steps[0]["step_id"]] = StepState.IN_PROGRESS
        self.step_start_time = time.time() if self.steps else None

    def get_current_step(self):
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance_step(self) -> bool:
        if self.current_step_index < len(self.steps):
            step_id = self.steps[self.current_step_index]["step_id"]
            self.step_states[step_id] = StepState.COMPLETED
            self.current_step_index += 1
            self.step_start_time = time.time()
            if self.current_step_index < len(self.steps):
                next_id = self.steps[self.current_step_index]["step_id"]
                self.step_states[next_id] = StepState.IN_PROGRESS
            return True
        return False

    def is_completed(self) -> bool:
        """Check if all protocol steps have been completed."""
        return len(self.steps) > 0 and self.current_step_index >= len(self.steps)

    def get_step_states(self) -> dict:
        """Return dictionary mapping step_id to state string name."""
        return {step_id: state.name for step_id, state in self.step_states.items()}

    def reset(self):
        """Reset the state machine back to the initial step."""
        self.current_step_index = 0
        self.step_states = {step["step_id"]: StepState.PENDING for step in self.steps}
        if self.steps:
            self.step_states[self.steps[0]["step_id"]] = StepState.IN_PROGRESS
        self.step_start_time = time.time() if self.steps else None
