# Next Steps — In Order

You have the code. Here’s what to do next, in order.

---

## 1. Finish setup on your PC (if not done)

- [ ] Cyton works with `python stream_openbci.py` (you see "Streaming from Cyton..." and feature lines).
- [ ] In `config/pipeline_config.py`: set **EMG** (10 ch) or **EEG** (16 ch), **ACTIVE_CHANNELS**, **CYTON_DAISY**, and **CYTON_SERIAL_PORT** to match your board and wiring.
- [ ] Optional: run `python stream_openbci.py --ssvep` and confirm you see `command=...` lines (needs occipital channels for real SSVEP).

---

## 2. Copy the project to the Raspberry Pi

- [ ] Copy the whole **OPENBCICOMMUNICATION** folder to the Pi (e.g. `/home/pi/OPENBCICOMMUNICATION`) via USB, git clone, or SCP.
- [ ] On the Pi: `cd` into that folder and run `pip3 install -r requirements.txt`.
- [ ] Plug the Cyton dongle into the Pi; run `ls /dev/ttyUSB* /dev/ttyACM*` and note the port (e.g. `/dev/ttyUSB0`).
- [ ] If you get "Permission denied" later: `sudo usermod -aG dialout $USER`, then log out and back in.
- [ ] Edit `config/pipeline_config.py` on the Pi: set **CYTON_SERIAL_PORT** to that port (e.g. `"/dev/ttyUSB0"`).
- [ ] Run `python3 stream_openbci.py` on the Pi and confirm it streams (same as on PC).
- [ ] Run `python3 bci_to_robot.py --ssvep` and confirm you see `[robot_driver] command=...` (no real robot yet).

Details: **docs/ON_THE_RASPBERRY_PI.md**.

---

## 3. Set up ROS (when you’re ready for the robot)

- [ ] Install ROS on the machine that will talk to the robot (Pi or PC), e.g. ROS Noetic.
- [ ] Install `rospy` and `geometry_msgs` (usually with the ROS install).
- [ ] Start **roscore** (or your robot’s ROS master).
- [ ] If the robot is on another computer: set **ROS_MASTER_URI** (and **ROS_IP**) so this machine and the robot use the same ROS master.

---

## 4. Connect BCI to the robot via ROS

- [ ] On the Pi (or PC), with ROS sourced:
  ```bash
  source /opt/ros/noetic/setup.bash
  cd /path/to/OPENBCICOMMUNICATION
  python3 bci_to_robot.py --ssvep --robot ros
  ```
- [ ] Confirm the robot’s controller subscribes to **cmd_vel** (standard for many bases). If it subscribes to something else, change the topic in `robot_driver.py` (ROSDriver) or add a small node that subscribes to **cmd_vel** and republishes to the robot’s topic.
- [ ] Test: BCI should publish Twist messages; robot should move (e.g. FRONT = forward, LEFT = turn left). Use **Ctrl+C** to stop; the driver sends zero velocity on exit.
- [ ] Optional: add a timeout so if no BCI command is received for a few seconds, the robot stops (already in `bci_to_robot.py` via `--timeout`).

---

## 5. Optional: run on the Pi at startup

- [ ] Once everything works, create a systemd service (or add to rc.local) so the Pi runs `bci_to_robot.py --ssvep --robot ros` on boot when you want it.

---

## Summary checklist

| # | Step |
|---|------|
| 1 | Confirm stream works on PC; set config (EMG/EEG, port, channels). |
| 2 | Copy project to Pi; install deps; set USB port in config; test stream and `bci_to_robot.py --ssvep`. |
| 3 | Install ROS; start roscore; set ROS_MASTER_URI if robot is on another machine. |
| 4 | Run `bci_to_robot.py --ssvep --robot ros`; confirm robot moves from BCI. |
| 5 | (Optional) Auto-start the script on the Pi. |

That’s the full sequence. Do 1 → 2 → 3 → 4 in order; 5 when you’re happy with the rest.
