"""
Active SOP Protocol Step Progress & Checklist Panel Widget.
"""

class ProtocolPanelWidget:
    """Widget displaying SOP steps, highlighting active step and compliance status."""
    def __init__(self, protocol_data=None):
        self.protocol_data = protocol_data or {}
        self.current_step_index = 0

    def update_active_step(self, step_number: int, status: str):
        """Update active step indicator."""
        self.current_step_index = step_number
