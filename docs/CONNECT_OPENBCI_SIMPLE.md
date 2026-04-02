# Connect OpenBCI to This Code (Simple)

## 1. Plug in the board

- Connect the **OpenBCI USB dongle** to your computer.
- Turn on the **Cyton** (power it up).
- Make sure the board is paired with the dongle (see OpenBCI docs if needed).

---

## 2. Find the COM port

- **Windows:** Open **Device Manager** → **Ports (COM & LPT)**. Note the port (e.g. **COM4**).
- **Mac:** Usually `/dev/cu.usbserial-*`.
- **Linux:** Usually `/dev/ttyUSB0`.

---

## 3. Set the port in the code

1. Open **`config/pipeline_config.py`**.
2. Find: `CYTON_SERIAL_PORT = "COM4"`.
3. Change **COM4** to your port (e.g. **COM3**).
4. Save the file.

---

## 4. Set which channels you use (10 EMG or 16 EEG)

1. Open **`config/pipeline_config.py`**.
2. **EMG (10 electrodes):** set `EMG_CHANNEL_INDICES` to the 10 EXG indices (0–15) where your EMG electrodes are. Use **Cyton + Daisy** (16 channels).
3. **EEG (16 electrodes):** set `EEG_CHANNEL_INDICES` to `[0,1,...,15]` (or the 16 EXG indices you use). Use **Cyton + Daisy**.
4. Set **`ACTIVE_CHANNELS = "emg"`** or **`"eeg"`** so the pipeline uses the right set.
5. Set **`CYTON_DAISY = True`** when using 10 or 16 channels (Daisy required).
6. Save the file.

---

## 5. Run the code

1. Open a terminal in the project folder.
2. Run:
   ```bash
   pip install -r requirements.txt
   ```
   (Only needed once.)
3. Run:
   ```bash
   python stream_openbci.py
   ```
4. You should see: *"Streaming from Cyton..."* and then lines of features every second.
5. Stop with **Ctrl+C**.

---

## If it doesn’t work

- Close the **OpenBCI GUI** (or any other app using the board).
- Double-check the COM port in Device Manager and in **`config/pipeline_config.py`**.
- Make sure the channel numbers in **`BICEP_CHANNEL_INDICES`** match where your electrodes are plugged in.
