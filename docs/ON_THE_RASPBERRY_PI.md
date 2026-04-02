# On the Raspberry Pi — Simple Steps

**Can I use Cursor on the Pi?**  
Cursor doesn’t run on Raspberry Pi. Edit the project on your **Windows PC in Cursor**, then copy the folder to the Pi (USB stick, git clone, or SCP). On the Pi, use the **terminal** and **nano** (or any text editor) if you need to change the config.

---

## 1. Copy the project to the Pi

Put the **OPENBCICOMMUNICATION** folder on the Pi (e.g. in `/home/pi/`). Use git, a USB stick, or copy from your PC.

---

## 2. Install and set the port

In a terminal on the Pi:

```bash
cd /home/pi/OPENBCICOMMUNICATION
pip3 install -r requirements.txt
ls /dev/ttyUSB* /dev/ttyACM*
```

Note the port (e.g. `/dev/ttyUSB0`). If you get “Permission denied” when running the script later:

```bash
sudo usermod -aG dialout $USER
```

Then log out and back in (or reboot).

---

## 3. Edit the config (only the port if the rest is already set)

```bash
nano config/pipeline_config.py
```

Change **`CYTON_SERIAL_PORT`** to your port, e.g. `"/dev/ttyUSB0"`.  
Save: Ctrl+O, Enter. Exit: Ctrl+X.

(If you haven’t already set EMG/EEG and channel indices on your PC, set them here too.)

---

## 4. Run it

Plug in the Cyton dongle and turn on the board, then:

```bash
python3 stream_openbci.py
```

You should see “Streaming from Cyton...” and feature lines. Ctrl+C to stop.

To test commands (no robot):

```bash
python3 bci_to_robot.py --ssvep
```

---

## 5. (Later) Use the robot with ROS

After ROS is installed and the robot is set up:

```bash
source /opt/ros/noetic/setup.bash
python3 bci_to_robot.py --ssvep --robot ros
```

---

**Summary:** Copy project → `pip3 install -r requirements.txt` → set USB port in config → run `python3 stream_openbci.py` or `python3 bci_to_robot.py --ssvep`. Edit code in Cursor on your PC, then copy to the Pi again if you change anything.
