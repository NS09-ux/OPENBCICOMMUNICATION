"""
Option B — Everything on Raspberry Pi: run BCI stream and send commands to the robot.

Usage on the Pi (Cyton plugged into Pi USB):
  python bci_to_robot.py --ssvep              # use SSVEP commands, robot = print only
  python bci_to_robot.py --ssvep --robot ros  # use SSVEP, publish to ROS cmd_vel

Config: config/pipeline_config.py (set CYTON_SERIAL_PORT to /dev/ttyUSB0 or /dev/ttyACM0).
"""

from __future__ import annotations

import sys
import time
import signal
from pathlib import Path

_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from stream_openbci import run_stream
from robot_driver import get_driver


def main():
    import argparse
    p = argparse.ArgumentParser(description="BCI stream on Pi → robot (Option B)")
    p.add_argument("--port", default=None, help="Serial port (default: from config, e.g. /dev/ttyUSB0)")
    p.add_argument("--ssvep", action="store_true", help="Use SSVEP; send FRONT/LEFT/etc. to robot")
    p.add_argument("--robot", default="print", choices=("print", "ros"),
                   help="Robot driver: print (no robot) or ros (publish cmd_vel)")
    p.add_argument("--timeout", type=float, default=3.0,
                   help="Stop robot if no command received for this many seconds")
    p.add_argument("--quiet", action="store_true", help="Less console output")
    args = p.parse_args()

    driver = get_driver(args.robot)
    last_cmd_time = [time.time()]  # use list so callback can mutate

    def on_features(feats):
        if args.ssvep and "command" in feats:
            cmd = feats.get("command", "NONE")
        else:
            cmd = "NONE"
        last_cmd_time[0] = time.time()
        driver.set_command(cmd)

    # Optional: background thread that stops robot on timeout
    def timeout_check():
        while True:
            time.sleep(0.5)
            if time.time() - last_cmd_time[0] > args.timeout:
                driver.stop()

    import threading
    timeout_thread = threading.Thread(target=timeout_check, daemon=True)
    timeout_thread.start()

    def on_exit(*_):
        driver.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, on_exit)
    signal.signal(signal.SIGTERM, on_exit)

    print(f"Robot driver: {args.robot}. SSVEP: {args.ssvep}. Timeout: {args.timeout}s. Ctrl+C to stop.")
    run_stream(
        port=args.port,
        on_features=on_features,
        verbose=not args.quiet,
        ssvep=args.ssvep,
    )


if __name__ == "__main__":
    main()
