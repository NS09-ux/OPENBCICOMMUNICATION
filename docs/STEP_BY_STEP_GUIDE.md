# Step-by-Step: OpenBCI Real-Time Stream and SSVEP Commands

Follow these steps in order to stream from your Cyton board and get either **features** or **commands** (e.g. for robot control).

---

## Part 1: Hardware and computer setup

### Step 1.1 – Connect the Cyton

1. Plug the **OpenBCI USB dongle** into your computer.
2. Turn on the **Cyton board** (battery or USB power).
3. Make sure the dongle and board are paired (see OpenBCI docs if you use a separate dongle).

### Step 1.2 – Find the COM port (Windows)

1. Press **Win + X** → **Device Manager**.
2. Expand **Ports (COM & LPT)**.
3. Find the OpenBCI port (e.g. **COM4** or **COM3**). Note the exact name.

On Mac/Linux you’ll see something like `/dev/cu.usbserial-*` (Mac) or `/dev/ttyUSB0` (Linux). Use that path as the “port” below.

### Step 1.3 – Electrode setup

- **For bicep/EMG (features only):**  
  Use your current setup: reference, DRL, and two electrodes on the bicep. The two bicep electrodes go to two EXG inputs on the Cyton (e.g. channels 0 and 1, or 2 and 3—you must know which).

- **For SSVEP (commands like FRONT/LEFT):**  
  You need **occipital** channels (back of the head): e.g. O1, Oz, O2, or any 1–3 EXG channels over the visual cortex. Reference and DRL as usual. Note which EXG channel numbers (0–7) those occipital electrodes use.

---

## Part 2: Software setup

### Step 2.1 – Install Python

1. Install **Python 3.8 or newer** from [python.org](https://www.python.org/downloads/).
2. During install, check **“Add Python to PATH”** (Windows).
3. Open a new terminal and confirm:
   ```bash
   python --version
   ```

### Step 2.2 – Open the project folder

In the terminal:

```bash
cd "c:\Users\cants\OneDrive\Desktop\Hadimani Lab\OPENBCICOMMUNICATION"
```

(Use your actual path if it’s different.)

### Step 2.3 – Install dependencies

```bash
pip install -r requirements.txt
```

This installs `numpy`, `pandas`, `scipy`, `matplotlib`, and **brainflow**.

### Step 2.4 – Set the COM port

1. Open **`config/pipeline_config.py`** in an editor.
2. Find the line:
   ```python
   CYTON_SERIAL_PORT = "COM4"
   ```
3. Change **`"COM4"`** to the port you found in Step 1.2 (e.g. `"COM3"`).
4. Save the file.

### Step 2.5 – Set which channels to use

1. In **`config/pipeline_config.py`**, find:
   ```python
   BICEP_CHANNEL_INDICES = [0, 1]
   ```
2. Set this to the **EXG channel indices** you’re actually using:
   - **Bicep:** e.g. `[0, 1]` or `[2, 3]` if your two bicep electrodes are on EXG 0 and 1 (or 2 and 3).
   - **SSVEP (occipital):** e.g. `[2, 3, 4]` if O1, Oz, O2 are on channels 2, 3, 4.
3. Save the file.

---

## Part 3: Run the stream

### Step 3.1 – Close other programs using the board

- Don’t run the **OpenBCI GUI** (or any other app) on the same COM port at the same time. Close it if it’s open.

### Step 3.2 – Stream and get features (default)

1. In the project folder, run:
   ```bash
   python stream_openbci.py
   ```
2. You should see a line like:
   ```text
   Streaming from Cyton (BrainFlow, port=COM4, 2 channels). Ctrl+C to stop.
   ```
3. Then, about once per second, lines like:
   ```text
   features: ch0_rms=12.3456 ch0_mean_abs=9.8765 ch1_rms=11.2345 ch1_mean_abs=8.7654 time_center_s=...
   ```
4. To stop: press **Ctrl+C**.

If you get an error about the port or connection, double-check Step 1.2 and Step 2.4.

### Step 3.3 – Stream and get SSVEP commands (FRONT / LEFT / etc.)

1. Make sure **`BICEP_CHANNEL_INDICES`** is set to your **occipital** channels (Step 2.5).
2. Run:
   ```bash
   python stream_openbci.py --ssvep
   ```
3. You should see the same “Streaming from Cyton…” line, then about once per second:
   ```text
   command=LEFT frequency_hz=15.0 power=0.1234
   ```
   (The command and frequency will change depending on which flicker the user is looking at.)
4. Stop with **Ctrl+C**.

### Step 3.4 – Optional: use a different port once

```bash
python stream_openbci.py --port COM3
```

Or with SSVEP:

```bash
python stream_openbci.py --port COM3 --ssvep
```

### Step 3.5 – Optional: no console output

```bash
python stream_openbci.py --quiet
```

Data is still streamed and processed; only the printed lines are turned off. You can use an `on_features` callback in code to handle the results (see docs).

---

## Part 4: Use the output

- **Features (default):**  
  Each line is one time window. Use the numbers (`ch0_rms`, `ch1_rms`, etc.) for your own logic (e.g. thresholds, or training a classifier). In code you can pass a function to `run_stream(..., on_features=your_callback)` and receive these values in a dict.

- **Commands (`--ssvep`):**  
  Each line is one command (FRONT, BACK, LEFT, RIGHT, STARTSTOP). In code you can pass `on_features=your_callback` and read `feats["command"]` (and `feats["frequency_hz"]`, `feats["power"]`) to send to ROS or the robot.

---

## Quick reference

| Goal                         | Command                                      |
|-----------------------------|----------------------------------------------|
| Features every ~1 s        | `python stream_openbci.py`                   |
| Commands every ~1 s (SSVEP) | `python stream_openbci.py --ssvep`           |
| Different port             | `python stream_openbci.py --port COM3`       |
| Stop streaming             | **Ctrl+C**                                   |

| Config file                 | What to set                                  |
|----------------------------|----------------------------------------------|
| `config/pipeline_config.py`| `CYTON_SERIAL_PORT`, `BICEP_CHANNEL_INDICES` |

If something fails, check: COM port, no other app using the board, correct channel indices, and that `pip install -r requirements.txt` completed without errors.
