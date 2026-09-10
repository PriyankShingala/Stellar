"""
Hardware Camera Feed Verification Utility Script.
"""

import cv2
import sys

def test_camera(device_id=0):
    print(f"Testing camera feed on device index {device_id}...")
    cap = cv2.VideoCapture(device_id)
    if not cap.isOpened():
        print(f"Error: Could not open camera device {device_id}")
        return False
    
    ret, frame = cap.read()
    if ret:
        print(f"Success! Frame captured successfully. Resolution: {frame.shape[1]}x{frame.shape[0]}")
    else:
        print("Error: Could not read frame from camera.")
    cap.release()
    return ret

if __name__ == "__main__":
    dev_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    test_camera(dev_id)
