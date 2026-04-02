# What the Program Outputs (and How to Get Commands)

## Current output from the program

When you run **`stream_openbci.py`** (or the CSV pipeline), the program does **not** output robot commands. It outputs **numbers (features)** every window step (e.g. every 1 second):

- **`ch0_rms`**, **`ch0_mean_abs`** – strength of the first channel (e.g. bicep 1)
- **`ch1_rms`**, **`ch1_mean_abs`** – strength of the second channel (e.g. bicep 2)
- **`time_center_s`** – time of that window

Example in the terminal:

```
features: ch0_rms=12.3456 ch0_mean_abs=9.8765 ch1_rms=11.2345 ch1_mean_abs=8.7654 time_center_s=1734567890.12
features: ch0_rms=13.1234 ch0_mean_abs=10.0123 ch1_rms=10.9876 ch1_mean_abs=8.5432 time_center_s=1734567891.15
...
```

So **right now the output is a continuous stream of feature values**, not “FRONT” or “LEFT”. You can use these features in your own code (e.g. `on_features` callback) or for a classifier later.

---

## How to get command output (e.g. SSVEP → "FRONT", "LEFT")

To go from **raw signals** to **one command per window** (e.g. for a robot), you add an **interpretation** step after the features (or after frequency analysis for SSVEP).

### For SSVEP (flicker → command)

1. **Use the right channels**  
   SSVEP comes from the visual cortex, so use **occipital** channels (e.g. O1, Oz, O2) if you have them. In **`config/pipeline_config.py`** set `BICEP_CHANNEL_INDICES` to the EXG indices that are your occipital channels (e.g. `[2, 3, 4]` for three electrodes at the back of the head).

2. **Use the SSVEP interpreter**  
   The repo includes **`ssvep_interpreter/`** (package). It takes a short window of EEG, bandpass-filters it for SSVEP (e.g. 4–60 Hz), computes power at 5, 10, 15, 25, and 50 Hz, and picks the strongest. That frequency is mapped to a command using **`config/ssvep_config.py`** (FRONT, BACK, LEFT, RIGHT, STARTSTOP).

3. **Run the stream with SSVEP**  
   Run:
   ```bash
   python stream_openbci.py --ssvep
   ```
   The program will still compute features, but it will **also** run the SSVEP interpreter and print a **command** each window, for example:
   ```
   command=LEFT frequency_hz=15.0
   ```

4. **Use that command elsewhere**  
   You can pass an **`on_features`** (or equivalent) callback that receives the command and, for example, publishes it to ROS or drives the robot.

So: **same real-time stream; you add interpretation (SSVEP or other) on top, and the output becomes both features and a single command per window.**

### For bicep/EMG (e.g. “flex” vs “rest”)

If you keep using bicep channels, “interpretation” is different: you might threshold **`ch0_rms`** (and maybe `ch1_rms`) to decide “flex” vs “rest”, or train a small classifier (e.g. LDA) on those features and output a label. The **output** would then be something like `"flex"` or `"rest"` instead of SSVEP commands.

---

## Summary

| What you run              | What the output is                                      |
|---------------------------|---------------------------------------------------------|
| **Current (no flag)**     | Features only: `ch0_rms`, `ch1_rms`, etc. every 1 s     |
| **With `--ssvep`**        | Same features **plus** one command per window (e.g. `LEFT`) |
| **Your callback**         | Whatever you do with features or command (e.g. send to ROS) |

So: **the program can output either just features, or features + an interpreted command (e.g. SSVEP), and you use that output (e.g. in a callback) to drive the robot.**
