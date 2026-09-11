"""
Deterministic Sequence Validator Engine.
Designed for PRAYOG-AI / Stellar HAR system for Bharatiya Antariksh Station (BAS) Experiments.

Validates incoming interaction events against active SOP protocol rules, enforcing:
- Correct step progression (01 bottle_pickup -> 02 glass_pickup -> 03 pouring -> 04 glass_put_down -> 05 bottle_put_down)
- Wrong-order detection (e.g. pouring before glass_pickup)
- Skipped-step detection (bypassing mandatory steps)
- Duplicate / idempotent event safety
- Explainable, deterministic structured status reporting
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from ai.sequence_validator.state_machine import ExperimentStateMachine, StepState

logger = logging.getLogger("SequenceValidator")

# Built-in Default Protocol for the MVP Experiment
DEFAULT_WATER_TRANSFER_PROTOCOL = {
    "protocol_id": "SOP-WATER-001",
    "title": "Bottle and Glass Water Transfer",
    "description": "Standard Operating Procedure for transfer of water from bottle to glass during BAS microgravity experiments.",
    "version": "1.0",
    "steps": [
        {
            "step_number": 1,
            "step_id": "STEP_BOTTLE_PICKUP",
            "action_name": "bottle_pickup",
            "required_objects": ["bottle"],
            "mandatory": True
        },
        {
            "step_number": 2,
            "step_id": "STEP_GLASS_PICKUP",
            "action_name": "glass_pickup",
            "required_objects": ["glass"],
            "mandatory": True
        },
        {
            "step_number": 3,
            "step_id": "STEP_POUR_WATER",
            "action_name": "pouring",
            "required_objects": ["bottle", "glass"],
            "mandatory": True
        },
        {
            "step_number": 4,
            "step_id": "STEP_GLASS_PUT_DOWN",
            "action_name": "glass_put_down",
            "required_objects": ["glass"],
            "mandatory": True
        },
        {
            "step_number": 5,
            "step_id": "STEP_BOTTLE_PUT_DOWN",
            "action_name": "bottle_put_down",
            "required_objects": ["bottle"],
            "mandatory": True
        }
    ]
}


class SequenceValidator:
    """
    Deterministic rule engine validating experiment action order, detecting sequence violations,
    and tracking SOP step transitions.
    """

    def __init__(self, protocol_data: Optional[dict] = None):
        if protocol_data is None:
            protocol_data = DEFAULT_WATER_TRANSFER_PROTOCOL

        self.protocol_data = protocol_data
        self.state_machine = ExperimentStateMachine(protocol_data)

    def reset(self):
        """Reset the internal state machine back to step 1."""
        self.state_machine.reset()
        logger.info(f"SequenceValidator reset to initial state for protocol {self.state_machine.protocol_id}.")

    def process_interaction(self, reasoner_output: dict) -> List[dict]:
        """
        Process output dictionary from InteractionReasoner and validate any triggered events.
        Enforces anti-cascade guard: advances at most ONE protocol step per video frame.

        Args:
            reasoner_output: Dictionary output from InteractionReasoner.update().

        Returns:
            List of structured validation result dicts, one for each event in reasoner_output["events"].
        """
        if not reasoner_output or not isinstance(reasoner_output, dict):
            return []

        events = reasoner_output.get("events", [])
        results = []
        step_advanced_this_frame = False

        for event in events:
            if step_advanced_this_frame:
                # Anti-cascade guard: Do not advance multiple protocol steps in a single video frame.
                current_step = self.state_machine.get_current_step()
                results.append({
                    "valid": False,
                    "event": event,
                    "current_step_number": current_step.get("step_number") if current_step else None,
                    "current_step_id": current_step.get("step_id") if current_step else None,
                    "expected_action": current_step.get("action_name") if current_step else None,
                    "deviation_type": "CASCADE_GUARD_HELD",
                    "status_message": f"Event '{event}' deferred by anti-cascade guard: at most one step may advance per frame.",
                    "alert_level": "INFO",
                    "is_completed": self.state_machine.is_completed(),
                    "step_states": self.state_machine.get_step_states()
                })
                logger.info(f"Anti-cascade guard prevented second step advance in same frame for event '{event}'.")
                continue

            val_res = self.validate_event(event, context=reasoner_output)
            results.append(val_res)

            # Check if this event successfully advanced a step
            if val_res.get("valid") is True and val_res.get("deviation_type") == "NONE":
                step_advanced_this_frame = True

        return results

    def validate_event(self, event: str, context: Optional[dict] = None) -> dict:
        """
        Validate an interaction event against the current active SOP step.

        Args:
            event: Action/interaction event name (e.g. "bottle_pickup", "pouring").
            context: Optional context dictionary (e.g. from InteractionReasoner).

        Returns:
            Structured dictionary:
            {
                "valid": bool,
                "event": str,
                "current_step_number": int | None,
                "current_step_id": str | None,
                "expected_action": str | None,
                "deviation_type": str,  # "NONE" | "WRONG_ORDER" | "SKIPPED_STEP" | "ALREADY_COMPLETED" | "UNEXPECTED_ACTION"
                "status_message": str,
                "alert_level": str,     # "INFO" | "WARNING" | "CRITICAL"
                "is_completed": bool,
                "step_states": dict
            }
        """
        steps = self.state_machine.steps
        curr_idx = self.state_machine.current_step_index

        # 1. Check if experiment is already fully completed
        if self.state_machine.is_completed():
            msg = f"All {len(steps)} steps of {self.state_machine.protocol_id} completed successfully."
            return {
                "valid": True,
                "event": event,
                "current_step_number": None,
                "current_step_id": None,
                "expected_action": None,
                "deviation_type": "NONE",
                "status_message": msg,
                "alert_level": "INFO",
                "is_completed": True,
                "step_states": self.state_machine.get_step_states()
            }

        current_step = self.state_machine.get_current_step()
        expected_action = current_step.get("action_name")
        curr_num = current_step.get("step_number")
        curr_id = current_step.get("step_id")

        # 2. Case A: Correct Event matching current active step
        if event == expected_action:
            self.state_machine.advance_step()
            is_comp = self.state_machine.is_completed()

            if is_comp:
                status_msg = f"Step {curr_num} ({expected_action}) completed. All {len(steps)} steps of {self.state_machine.protocol_id} completed successfully!"
            else:
                next_step = self.state_machine.get_current_step()
                status_msg = f"Step {curr_num} ({expected_action}) completed successfully. Next: Step {next_step['step_number']} ({next_step['action_name']})."

            logger.info(f"Step {curr_num} completed successfully: {event}")
            return {
                "valid": True,
                "event": event,
                "current_step_number": curr_num,
                "current_step_id": curr_id,
                "expected_action": expected_action,
                "deviation_type": "NONE",
                "status_message": status_msg,
                "alert_level": "INFO",
                "is_completed": is_comp,
                "step_states": self.state_machine.get_step_states()
            }

        # 3. Case B: Duplicate / Already Completed Action
        earlier_actions = [s.get("action_name") for s in steps[:curr_idx]]
        if event in earlier_actions:
            status_msg = f"Action '{event}' was already completed in an earlier step. Currently awaiting Step {curr_num}: '{expected_action}'."
            logger.info(f"Duplicate event ignored: {status_msg}")
            return {
                "valid": False,
                "event": event,
                "current_step_number": curr_num,
                "current_step_id": curr_id,
                "expected_action": expected_action,
                "deviation_type": "ALREADY_COMPLETED",
                "status_message": status_msg,
                "alert_level": "INFO",
                "is_completed": False,
                "step_states": self.state_machine.get_step_states()
            }

        # 4. Case C: Out-of-Order / Future Step Action
        later_steps = steps[curr_idx + 1:]
        matching_future = [s for s in later_steps if s.get("action_name") == event]

        if matching_future:
            future_step = matching_future[0]
            future_idx = steps.index(future_step)

            if future_idx == curr_idx + 1:
                # Immediate next step attempted before current step completed
                deviation_type = "WRONG_ORDER"
                alert_level = "WARNING"
                status_msg = f"Wrong order: '{event}' belongs to Step {future_step['step_number']} ('{future_step['step_id']}'), but Step {curr_num} ('{expected_action}') must be completed first."
            else:
                # Bypassed one or more mandatory steps
                deviation_type = "SKIPPED_STEP"
                alert_level = "CRITICAL"
                status_msg = f"Protocol violation: Attempted '{event}' (Step {future_step['step_number']}), skipping mandatory Step {curr_num} ('{expected_action}')."

            logger.warning(f"Sequence deviation detected: {status_msg}")
            return {
                "valid": False,
                "event": event,
                "current_step_number": curr_num,
                "current_step_id": curr_id,
                "expected_action": expected_action,
                "deviation_type": deviation_type,
                "status_message": status_msg,
                "alert_level": alert_level,
                "is_completed": False,
                "step_states": self.state_machine.get_step_states()
            }

        # 5. Case D: Unexpected Action not in protocol
        all_actions = [s.get("action_name") for s in steps]
        status_msg = f"Unexpected action '{event}' is not recognized in protocol {self.state_machine.protocol_id}. Awaiting Step {curr_num}: '{expected_action}'."
        logger.warning(f"Unexpected action: {status_msg}")
        return {
            "valid": False,
            "event": event,
            "current_step_number": curr_num,
            "current_step_id": curr_id,
            "expected_action": expected_action,
            "deviation_type": "UNEXPECTED_ACTION",
            "status_message": status_msg,
            "alert_level": "WARNING",
            "is_completed": False,
            "step_states": self.state_machine.get_step_states()
        }

    def validate_action(self, detected_action: str, detected_objects: Optional[list] = None) -> Tuple[bool, str, str]:
        """
        Backward-compatible validation method returning (is_valid, status_message, alert_level).
        """
        res = self.validate_event(detected_action)
        return (res["valid"], res["status_message"], res["alert_level"])
