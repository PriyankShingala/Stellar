"""
Unit tests for Deterministic Sequence Validator and Protocol Parser.
"""

import unittest
from ai.sequence_validator.protocol_parser import ProtocolParser
from ai.sequence_validator.sequence_validator import SequenceValidator

class TestSequenceValidator(unittest.TestCase):
    
    def test_protocol_loader(self):
        sample_protocol = {
            "protocol_id": "TEST-SOP",
            "title": "Test Protocol",
            "steps": [
                {"step_number": 1, "step_id": "STEP_1", "action_name": "Pick vial"},
                {"step_number": 2, "step_id": "STEP_2", "action_name": "Seal vial"}
            ]
        }
        validator = SequenceValidator(sample_protocol)
        current_step = validator.state_machine.get_current_step()
        self.assertIsNotNone(current_step)
        self.assertEqual(current_step["step_id"], "STEP_1")

if __name__ == "__main__":
    unittest.main()
