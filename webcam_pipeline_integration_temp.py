"""
Temporary Standalone End-to-End OpenCV Integration Script for Stellar MVP.
Integrates: Camera -> PoseEstimator -> ObjectDetector -> InteractionReasoner -> SequenceValidator

Protocol: SOP-WATER-001 (Bottle and Glass Water Transfer)
1. bottle_pickup
2. glass_pickup
3. pouring
4. glass_put_down
5. bottle_put_down

Press 'q' or 'ESC' to exit.
Press 'r' to reset protocol sequence back to Step 1.
"""

import sys
import os
import time
import cv2
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ai.inference.pose_estimator import PoseEstimator
from ai.inference.object_detector import ObjectDetector
from ai.inference.interaction_reasoner import InteractionReasoner
from ai.sequence_validator.sequence_validator import SequenceValidator


def format_step_name(step_dict: dict) -> str:
    """Format step dictionary for display."""
    if not step_dict:
        return "ALL STEPS COMPLETED"
    num = step_dict.get("step_number", 0)
    action = step_dict.get("action_name", "unknown")
    return f"STEP 0{num}: {action.replace('_', ' ').upper()}"


def draw_hud(
    frame: np.ndarray,
    pose_results: dict,
    object_detections: list,
    reasoner_output: dict,
    validator_events: list,
    validator: SequenceValidator,
    fps: float,
    last_event_msg: str
) -> np.ndarray:
    """Render cinematic astronaut telemetry overlay on the OpenCV frame."""
    h, w = frame.shape[:2]
    overlay = frame.copy()

    # 1. Top HUD Bar (Dark translucent rectangle)
    cv2.rectangle(overlay, (0, 0), (w, 82), (10, 14, 23), -1)
    cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)

    # Top brand and protocol title
    cv2.putText(
        frame, "STELLAR AI | ON-BOARD BAS EXPERIMENT PIPELINE DEMO",
        (16, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (56, 189, 248), 2, cv2.LINE_AA
    )

    # Current SOP Step Status
    curr_step = validator.state_machine.get_current_step()
    is_completed = validator.state_machine.is_completed()

    if is_completed:
        sop_txt = "PROTOCOL STATUS: ALL 5 STEPS COMPLETED (CERTIFIED)"
        sop_color = (0, 255, 127)  # Emerald green
    else:
        sop_txt = f"ACTIVE SOP: {format_step_name(curr_step)}"
        sop_color = (11, 158, 245)  # Amber

    cv2.putText(
        frame, sop_txt,
        (16, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.65, sop_color, 2, cv2.LINE_AA
    )

    # FPS & Controls reminder
    fps_txt = f"FPS: {fps:.1f} | 'r': Reset | 'q': Quit"
    cv2.putText(
        frame, fps_txt,
        (w - 280, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (148, 163, 184), 1, cv2.LINE_AA
    )

    # 2. Bottom Telemetry Bar (Dark translucent rectangle)
    overlay_bot = frame.copy()
    bot_h = 100
    cv2.rectangle(overlay_bot, (0, h - bot_h), (w, h), (10, 14, 23), -1)
    cv2.addWeighted(overlay_bot, 0.78, frame, 0.22, 0, frame)

    # Pose Status
    pose_detected = pose_results.get("detected", False)
    carried = pose_results.get("carried_forward", False)
    if pose_detected:
        pose_txt = "POSE: TRACKING (12 JOINTS)"
        pose_col = (0, 255, 0)
    elif carried:
        pose_txt = f"POSE: SMOOTHED (+{pose_results.get('carry_count')})"
        pose_col = (0, 255, 255)
    else:
        pose_txt = "POSE: SEARCHING"
        pose_col = (100, 116, 139)

    cv2.putText(frame, pose_txt, (16, h - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.45, pose_col, 1, cv2.LINE_AA)

    # Detections count
    bottle_count = sum(1 for d in object_detections if d.get("label") == "bottle")
    glass_count = sum(1 for d in object_detections if d.get("label") == "glass")
    obj_txt = f"OBJECTS: BOTTLE({bottle_count}) | GLASS({glass_count})"
    cv2.putText(frame, obj_txt, (230, h - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    # Interaction Reasoner: Wrists & Pouring
    held = reasoner_output.get("held_objects", {}) if reasoner_output else {}
    l_held = held.get("left")
    r_held = held.get("right")
    l_str = f"L-WRIST: {l_held.upper() if l_held else 'FREE'}"
    r_str = f"R-WRIST: {r_held.upper() if r_held else 'FREE'}"

    is_pouring = reasoner_output.get("is_pouring", False) if reasoner_output else False
    pour_str = "POURING: ACTIVE" if is_pouring else "POURING: NO"
    pour_col = (0, 255, 127) if is_pouring else (148, 163, 184)

    cv2.putText(frame, f"{l_str} | {r_str}", (16, h - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (11, 158, 245), 1, cv2.LINE_AA)
    cv2.putText(frame, pour_str, (320, h - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.45, pour_col, 1, cv2.LINE_AA)

    # Last Validation Audit Event
    audit_txt = f"AUDIT: {last_event_msg}"
    cv2.putText(frame, audit_txt, (16, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    return frame


def main():
    print("=" * 70)
    print("STELLAR AI - END-TO-END PIPELINE WEBCAM VERIFICATION DEMO")
    print("Camera -> PoseEstimator -> ObjectDetector -> InteractionReasoner -> SequenceValidator")
    print("=" * 70)
    print("Controls:")
    print("  'q' or ESC : Quit application")
    print("  'r'        : Reset SOP-WATER-001 back to Step 1\n")

    # 1. Initialize Pipeline Models
    print("[INIT] Loading MediaPipe PoseEstimator (12 joints)...")
    pose_estimator = PoseEstimator(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    print("[INIT] Loading YOLOv8n ObjectDetector (bottle + glass)...")
    object_detector = ObjectDetector(conf_threshold=0.25)

    print("[INIT] Initializing Deterministic InteractionReasoner...")
    interaction_reasoner = InteractionReasoner()

    print("[INIT] Initializing Deterministic SequenceValidator (SOP-WATER-001)...")
    sequence_validator = SequenceValidator()

    # 2. Camera Setup
    camera_index = 0
    print(f"[CAMERA] Opening cv2.VideoCapture({camera_index})...")
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"ERROR: Could not open camera {camera_index}. Check device connection.")
        pose_estimator.close()
        return

    # 5-frame warm-up
    print("[CAMERA] Sensor warm-up (5 frames)...")
    for w_i in range(5):
        ret, warm_frame = cap.read()
        if not ret or warm_frame is None:
            print("ERROR: Camera failed during warm-up phase.")
            cap.release()
            pose_estimator.close()
            return

    print("[CAMERA] Camera ready. Beginning live inference loop.\n")
    window_name = "Stellar AI - Fallback OpenCV End-to-End Demo (Press 'q' to Quit)"

    frame_count = 0
    start_time = time.time()
    last_event_msg = "Awaiting Step 01 (bottle_pickup)..."

    try:
        while True:
            t0 = time.time()
            ret, frame = cap.read()

            if not ret or frame is None:
                print("\n[DIAGNOSTICS] Invalid/empty frame received from camera. Terminating loop cleanly.")
                break

            frame_count += 1

            # 1. Pose Landmark Estimation
            pose_results = pose_estimator.estimate_pose(frame)

            # 2. Object Detection on SAME frame
            object_detections = object_detector.detect(frame)

            # 3. Deterministic Interaction Reasoning
            reasoner_output = interaction_reasoner.update(pose_results, object_detections)

            # 4. SOP Sequence Validation
            validator_events = sequence_validator.process_interaction(reasoner_output)

            # Process validated events
            for res in validator_events:
                evt = res.get("event")
                valid = res.get("valid")
                msg = res.get("status_message", "")
                last_event_msg = msg

                if valid:
                    step_num = res.get("current_step_number")
                    print(f"\n>>> [VALIDATOR SUCCESS] Step {step_num} ({evt}) verified! -> {msg}")
                else:
                    dev_type = res.get("deviation_type")
                    print(f"\n>>> [VALIDATOR DEVIATION: {dev_type}] Event '{evt}' -> {msg}")

            # Calculate FPS
            elapsed = time.time() - t0
            fps = 1.0 / max(elapsed, 1e-4)

            # Periodic console diagnostics
            if frame_count % 30 == 0:
                tot_fps = frame_count / (time.time() - start_time)
                sm = sequence_validator.state_machine
                curr_st = sm.get_current_step()
                curr_act = curr_st.get("action_name") if curr_st else "COMPLETED"
                held = reasoner_output.get("held_objects", {})
                print(f"[Frame {frame_count:04d} | {tot_fps:.1f} FPS] "
                      f"Target Step: {curr_act} | "
                      f"Held: L={held.get('left')}, R={held.get('right')} | "
                      f"Pouring={reasoner_output.get('is_pouring')}")

            # Draw Overlays
            annotated = frame.copy()
            pose_estimator.draw_landmarks(annotated, pose_results, draw_rack_bounds=False)
            object_detector.draw_detections(annotated, object_detections)

            # Draw HUD
            annotated = draw_hud(
                annotated,
                pose_results,
                object_detections,
                reasoner_output,
                validator_events,
                sequence_validator,
                fps,
                last_event_msg
            )

            # Display frame
            cv2.imshow(window_name, annotated)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q') or key == 27:
                print("\n[USER] Exit requested by key press.")
                break
            elif key == ord('r') or key == ord('R'):
                sequence_validator.reset()
                interaction_reasoner.reset()
                last_event_msg = "Protocol reset to Step 01 (bottle_pickup)."
                print("\n[RESET] Protocol state and reasoner reset back to Step 1.")

    except Exception as e:
        print(f"\n[ERROR] Exception in integration loop: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n[CLEANUP] Releasing camera and OpenCV resources...")
        cap.release()
        cv2.destroyAllWindows()
        pose_estimator.close()
        print("[CLEANUP] All resources released cleanly.")


if __name__ == "__main__":
    main()
