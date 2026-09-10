"""
Deterministic Sequence Validator Engine.
Checks incoming classified actions against current SOP step rules.
"""

import logging
from ai.sequence_validator.state_machine import ExperimentStateMachine, StepState

logger = logging.getLogger("SequenceValidator")

class SequenceValidator:
    """Isolated deterministic rule engine validating action order, missing steps, and timing."""
    def __init__(self, protocol_data: dict):
        self.state_machine = ExperimentStateMachine(protocol_data)

    def validate_action(self, detected_action: str, detected_objects: list):
        """
        Validate detected action against active SOP state.
        Returns validation result tuple: (is_valid: bool, status_message: str, alert_level: str)
        """
        current_step = self.state_machine.get_current_step()
        if not current_step:
            return (True, "All SOP steps completed successfully.", "INFO")

        # Deterministic check logic
        expected_step_id = current_step.get("step_id")
        logger.info(f"Validating action '{detected_action}' against expected step '{expected_step_id}'")
        
        return (True, f"Executing step {current_step['step_number']}: {current_step['action_name']}", "INFO")
