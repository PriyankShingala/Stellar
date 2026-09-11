"""
Unit tests for Deterministic Sequence Validator (ai/sequence_validator/).
Validates SOP-WATER-001 "Bottle and Glass Water Transfer" protocol enforcement,
wrong-order detection, skipped steps, duplicate events, and InteractionReasoner integration.
"""

import os
import unittest
from ai.sequence_validator.protocol_parser import ProtocolParser
from ai.sequence_validator.sequence_validator import SequenceValidator, DEFAULT_WATER_TRANSFER_PROTOCOL
from ai.sequence_validator.state_machine import StepState
from ai.inference.interaction_reasoner import InteractionReasoner


class TestSequenceValidator(unittest.TestCase):

    def setUp(self):
        self.validator = SequenceValidator()  # Defaults to SOP-WATER-001

    # -------------------------------------------------------------
    # 1. Protocol Loading Tests
    # -------------------------------------------------------------
    def test_water_transfer_protocol_yaml(self):
        """Verify loading SOP-WATER-001 from backend/config/protocols/water_transfer_sop.yaml."""
        yaml_path = os.path.join("backend", "config", "protocols", "water_transfer_sop.yaml")
        self.assertTrue(os.path.exists(yaml_path), f"Protocol file missing: {yaml_path}")

        protocol_data = ProtocolParser.load_protocol(yaml_path)
        self.assertEqual(protocol_data["protocol_id"], "SOP-WATER-001")
        self.assertEqual(len(protocol_data["steps"]), 5)
        self.assertEqual(protocol_data["steps"][0]["action_name"], "bottle_pickup")
        self.assertEqual(protocol_data["steps"][1]["action_name"], "glass_pickup")
        self.assertEqual(protocol_data["steps"][2]["action_name"], "pouring")
        self.assertEqual(protocol_data["steps"][3]["action_name"], "glass_put_down")
        self.assertEqual(protocol_data["steps"][4]["action_name"], "bottle_put_down")

    def test_default_protocol_initialization(self):
        """Verify SequenceValidator initializes with 5-step SOP-WATER-001 by default."""
        self.assertEqual(self.validator.state_machine.protocol_id, "SOP-WATER-001")
        self.assertEqual(len(self.validator.state_machine.steps), 5)
        current = self.validator.state_machine.get_current_step()
        self.assertIsNotNone(current)
        self.assertEqual(current["step_id"], "STEP_BOTTLE_PICKUP")
        self.assertEqual(current["action_name"], "bottle_pickup")
        self.assertEqual(self.validator.state_machine.step_states["STEP_BOTTLE_PICKUP"], StepState.IN_PROGRESS)

    def test_legacy_protocol_loader(self):
        """Verify existing bio protocol compatibility."""
        sample_protocol = {
            "protocol_id": "TEST-SOP",
            "title": "Test Protocol",
            "steps": [
                {"step_number": 1, "step_id": "STEP_1", "action_name": "Pick vial"},
                {"step_number": 2, "step_id": "STEP_2", "action_name": "Seal vial"}
            ]
        }
        val = SequenceValidator(sample_protocol)
        current = val.state_machine.get_current_step()
        self.assertEqual(current["step_id"], "STEP_1")

    # -------------------------------------------------------------
    # 2. Happy Path 5-Step Sequence Progression
    # -------------------------------------------------------------
    def test_complete_happy_path_5_step_sequence(self):
        """Sequential execution of 01 -> 02 -> 03 -> 04 -> 05 completes experiment."""
        # Step 1: bottle_pickup
        r1 = self.validator.validate_event("bottle_pickup")
        self.assertTrue(r1["valid"])
        self.assertEqual(r1["deviation_type"], "NONE")
        self.assertEqual(r1["current_step_number"], 1)
        self.assertFalse(r1["is_completed"])
        self.assertEqual(r1["step_states"]["STEP_BOTTLE_PICKUP"], "COMPLETED")
        self.assertEqual(r1["step_states"]["STEP_GLASS_PICKUP"], "IN_PROGRESS")

        # Step 2: glass_pickup
        r2 = self.validator.validate_event("glass_pickup")
        self.assertTrue(r2["valid"])
        self.assertEqual(r2["current_step_number"], 2)
        self.assertEqual(r2["step_states"]["STEP_GLASS_PICKUP"], "COMPLETED")
        self.assertEqual(r2["step_states"]["STEP_POUR_WATER"], "IN_PROGRESS")

        # Step 3: pouring
        r3 = self.validator.validate_event("pouring")
        self.assertTrue(r3["valid"])
        self.assertEqual(r3["current_step_number"], 3)
        self.assertEqual(r3["step_states"]["STEP_POUR_WATER"], "COMPLETED")
        self.assertEqual(r3["step_states"]["STEP_GLASS_PUT_DOWN"], "IN_PROGRESS")

        # Step 4: glass_put_down
        r4 = self.validator.validate_event("glass_put_down")
        self.assertTrue(r4["valid"])
        self.assertEqual(r4["current_step_number"], 4)
        self.assertEqual(r4["step_states"]["STEP_GLASS_PUT_DOWN"], "COMPLETED")
        self.assertEqual(r4["step_states"]["STEP_BOTTLE_PUT_DOWN"], "IN_PROGRESS")

        # Step 5: bottle_put_down
        r5 = self.validator.validate_event("bottle_put_down")
        self.assertTrue(r5["valid"])
        self.assertEqual(r5["current_step_number"], 5)
        self.assertTrue(r5["is_completed"])
        self.assertEqual(r5["step_states"]["STEP_BOTTLE_PUT_DOWN"], "COMPLETED")
        self.assertIn("completed successfully", r5["status_message"])

    # -------------------------------------------------------------
    # 3. Deviation Tests (Wrong Order, Skipped Steps, Unexpected)
    # -------------------------------------------------------------
    def test_wrong_order_pouring_before_glass_pickup(self):
        """Attempting Step 3 (pouring) while expecting Step 2 (glass_pickup) fails with WRONG_ORDER."""
        # Complete Step 1
        self.validator.validate_event("bottle_pickup")
        self.assertEqual(self.validator.state_machine.get_current_step()["step_number"], 2)

        # Attempt Step 3 prematurely
        res = self.validator.validate_event("pouring")
        self.assertFalse(res["valid"])
        self.assertEqual(res["deviation_type"], "WRONG_ORDER")
        self.assertEqual(res["alert_level"], "WARNING")
        self.assertIn("Wrong order", res["status_message"])
        self.assertIn("glass_pickup", res["status_message"])

        # Confirm state machine did NOT advance (still on Step 2)
        curr = self.validator.state_machine.get_current_step()
        self.assertEqual(curr["step_number"], 2)
        self.assertEqual(curr["action_name"], "glass_pickup")
        self.assertEqual(self.validator.state_machine.step_states["STEP_GLASS_PICKUP"], StepState.IN_PROGRESS)

    def test_skipped_step_behavior(self):
        """Jumping from Step 1 directly to Step 4 (glass_put_down) triggers SKIPPED_STEP."""
        # Complete Step 1
        self.validator.validate_event("bottle_pickup")

        # Jump directly to Step 4 (bypassing steps 2 and 3)
        res = self.validator.validate_event("glass_put_down")
        self.assertFalse(res["valid"])
        self.assertEqual(res["deviation_type"], "SKIPPED_STEP")
        self.assertEqual(res["alert_level"], "CRITICAL")
        self.assertIn("skipping mandatory", res["status_message"])

        # State machine remains on Step 2
        self.assertEqual(self.validator.state_machine.get_current_step()["step_number"], 2)

    def test_duplicate_events_handled_safely(self):
        """Duplicate/repeated event for already-completed step returns ALREADY_COMPLETED and does not corrupt state."""
        # Complete Step 1
        r1 = self.validator.validate_event("bottle_pickup")
        self.assertTrue(r1["valid"])

        # Repeat Step 1 event
        dup = self.validator.validate_event("bottle_pickup")
        self.assertFalse(dup["valid"])
        self.assertEqual(dup["deviation_type"], "ALREADY_COMPLETED")
        self.assertEqual(dup["alert_level"], "INFO")
        self.assertIn("already completed", dup["status_message"])

        # State remains safely at Step 2
        self.assertEqual(self.validator.state_machine.get_current_step()["step_number"], 2)

    def test_unexpected_action(self):
        """Unrecognized actions not in the protocol return UNEXPECTED_ACTION."""
        res = self.validator.validate_event("sanitize_hands")
        self.assertFalse(res["valid"])
        self.assertEqual(res["deviation_type"], "UNEXPECTED_ACTION")
        self.assertEqual(res["alert_level"], "WARNING")

        # State remains at Step 1
        self.assertEqual(self.validator.state_machine.get_current_step()["step_number"], 1)

    # -------------------------------------------------------------
    # 4. Experiment Completion Handling
    # -------------------------------------------------------------
    def test_experiment_completion(self):
        """Once all 5 steps complete, subsequent events report completion without corruption."""
        for act in ["bottle_pickup", "glass_pickup", "pouring", "glass_put_down", "bottle_put_down"]:
            self.validator.validate_event(act)

        self.assertTrue(self.validator.state_machine.is_completed())
        self.assertIsNone(self.validator.state_machine.get_current_step())

        # Post-completion event
        res = self.validator.validate_event("bottle_pickup")
        self.assertTrue(res["valid"])
        self.assertTrue(res["is_completed"])
        self.assertIsNone(res["current_step_number"])
        self.assertIn("completed successfully", res["status_message"])

    # -------------------------------------------------------------
    # 5. Integration with InteractionReasoner Output
    # -------------------------------------------------------------
    def test_integration_with_interaction_reasoner(self):
        """Feed actual InteractionReasoner outputs into SequenceValidator.process_interaction()."""
        reasoner = InteractionReasoner()
        validator = SequenceValidator()

        # Helper to construct mock pose
        def make_pose(lw=None, rw=None):
            return {
                "detected": True,
                "body_keypoints": {
                    "left_wrist": {"px": lw[0], "py": lw[1]} if lw else None,
                    "right_wrist": {"px": rw[0], "py": rw[1]} if rw else None
                }
            }

        bottle_box = [100, 200, 180, 400]
        glass_box = [400, 250, 480, 370]
        bottle_tilted = [360, 220, 480, 300]

        objs_table = [
            {"label": "bottle", "bbox": bottle_box, "confidence": 0.9},
            {"label": "glass", "bbox": glass_box, "confidence": 0.9}
        ]

        # Step 1: Pick up bottle (right hand approaches)
        p1 = make_pose(lw=(50, 50), rw=(140, 300))
        reasoner.update(p1, objs_table)
        out1 = reasoner.update(p1, objs_table)
        self.assertIn("bottle_pickup", out1["events"])

        res1 = validator.process_interaction(out1)
        self.assertEqual(len(res1), 1)
        self.assertTrue(res1[0]["valid"])
        self.assertEqual(res1[0]["current_step_number"], 1)

        # Step 2: Pick up glass (left hand approaches)
        p2 = make_pose(lw=(440, 300), rw=(140, 300))
        reasoner.update(p2, objs_table)
        out2 = reasoner.update(p2, objs_table)
        self.assertIn("glass_pickup", out2["events"])

        res2 = validator.process_interaction(out2)
        self.assertEqual(len(res2), 1)
        self.assertTrue(res2[0]["valid"])
        self.assertEqual(res2[0]["current_step_number"], 2)

        # Step 3: Pouring (sustained for min_pouring_frames)
        objs_pour = [
            {"label": "bottle", "bbox": bottle_tilted, "confidence": 0.88},
            {"label": "glass", "bbox": glass_box, "confidence": 0.88}
        ]
        p3 = make_pose(lw=(440, 300), rw=(420, 260))
        for _ in range(reasoner.min_pouring_frames):
            out3 = reasoner.update(p3, objs_pour)
        self.assertIn("pouring", out3["events"])

        res3 = validator.process_interaction(out3)
        self.assertEqual(len(res3), 1)
        self.assertTrue(res3[0]["valid"])
        self.assertEqual(res3[0]["current_step_number"], 3)

        # Step 4: Put down glass (left hand moves away for 3 frames)
        p4 = make_pose(lw=(50, 50), rw=(140, 300))
        for _ in range(2):
            reasoner.update(p4, objs_table)
        out4 = reasoner.update(p4, objs_table)
        self.assertIn("glass_put_down", out4["events"])

        res4 = validator.process_interaction(out4)
        self.assertEqual(len(res4), 1)
        self.assertTrue(res4[0]["valid"])
        self.assertEqual(res4[0]["current_step_number"], 4)

        # Step 5: Put down bottle (right hand moves away for 3 frames)
        p5 = make_pose(lw=(50, 50), rw=(600, 600))
        for _ in range(2):
            reasoner.update(p5, objs_table)
        out5 = reasoner.update(p5, objs_table)
        self.assertIn("bottle_put_down", out5["events"])

        res5 = validator.process_interaction(out5)
        self.assertEqual(len(res5), 1)
        self.assertTrue(res5[0]["valid"])
        self.assertEqual(res5[0]["current_step_number"], 5)
        self.assertTrue(res5[0]["is_completed"])

    def test_anti_cascade_guard_limits_to_one_step_per_frame(self):
        """Verify process_interaction advances at most ONE step per video frame when multi-events burst."""
        validator = SequenceValidator()
        mock_burst = {"events": ["bottle_pickup", "glass_pickup"]}

        results = validator.process_interaction(mock_burst)
        self.assertEqual(len(results), 2)
        # First event is accepted and advances step 1 -> step 2
        self.assertTrue(results[0]["valid"])
        self.assertEqual(results[0]["event"], "bottle_pickup")

        # Second event in the same frame is blocked by anti-cascade guard
        self.assertFalse(results[1]["valid"])
        self.assertEqual(results[1]["deviation_type"], "CASCADE_GUARD_HELD")

        # State machine index must be 1 (at Step 2: glass_pickup), NOT advanced to Step 3!
        self.assertEqual(validator.state_machine.current_step_index, 1)
        self.assertEqual(validator.state_machine.get_current_step()["action_name"], "glass_pickup")


if __name__ == "__main__":
    unittest.main()
