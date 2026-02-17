# Connecting OpenBCI to Your ML Pipeline

You don’t use a traditional “API” (like a REST server) to get data from the OpenBCI board into your ML code. The link is either **direct hardware streaming** or **reading saved files**.

## Option 1: Load saved recordings (simplest)

- You record in the OpenBCI GUI (or another app) and save to **CSV**.
- Your ML pipeline runs in Python and **loads that CSV** with `pandas` or `mne`.
- No API, no network: just `pd.read_csv("your_recording.csv")`.

Use this when you’re building and testing the pipeline offline.

---

## Option 2: Real-time stream via serial (no API)

- The Cyton board is connected by **USB (serial)**. It sends binary packets at 250 Hz (or your set rate).
- In Python you use a **serial driver** that:
  - Opens the COM port (e.g. `COM3` on Windows).
  - Reads the packet protocol (start byte, channel samples, checksum).
  - Converts to microvolts and yields samples in a loop.

Libraries that do this:

- **BrainFlow** (e.g. `pip install brainflow`) – **recommended by OpenBCI**. Open the port, call `start_stream()`, then poll `get_board_data()` in a loop; data is in µV. Same API works across many boards.
- **pyOpenBCI** – older; OpenBCI now recommends BrainFlow for new projects.

So “communication” is: **Python talks to the board over serial; the library gives you a stream of samples; your ML code consumes that stream.** There is no HTTP server or “OpenBCI API” in the middle.

**In this repo:** Use **`stream_openbci.py`** for real-time streaming. It uses **BrainFlow** (OpenBCI’s recommended library; pyOpenBCI is outdated) to read from the Cyton over USB, buffers samples, and runs the same preprocess + feature extraction as the CSV pipeline every window step. Set your COM port in `config/pipeline_config.py` (`CYTON_SERIAL_PORT`, e.g. `"COM4"`), then run:
```bash
pip install brainflow
python stream_openbci.py
```
Optional: `python stream_openbci.py --port COM3` to override the port. Press **Ctrl+C** to stop.

---

## Option 3: Real-time stream via Lab Streaming Layer (LSL)

- The **OpenBCI GUI** (or a separate app) can stream data over the network using **Lab Streaming Layer (LSL)**.
- Your ML code uses **PyLSL** in Python to create an “inlet” and **pull samples** from that stream.
- Again, no REST API: LSL is a streaming protocol (UDP/multicast). Your script runs `inlet.pull_sample()` in a loop and feeds those samples into your pipeline.

Use this when you want to keep using the GUI for acquisition but run your own Python processing in real time.

---

## Summary

| Method        | How data gets to ML code              | “API”? |
|---------------|----------------------------------------|--------|
| **Saved CSV** | Read file with pandas/mne              | No – file I/O |
| **Serial**    | pyOpenBCI (or similar) reads COM port  | No – serial driver |
| **LSL**       | PyLSL inlet pulls stream from GUI/app  | No – LSL stream |

So: **you do not use an API in the sense of calling a web service.** You either load a file, or you stream from the board (serial) or from the GUI (LSL), and your ML pipeline runs on that data. If you later want a small “bridge” (e.g. a script that reads serial and writes to a socket or queue), that’s just a local data pipe, not the OpenBCI board exposing an API.
