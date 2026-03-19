# GGUF Server Runner (v1.6)

A specialized Python-based graphical interface designed to manage and deploy `llama.cpp` servers. This tool pivots from pure benchmarking to a "Service-First" approach, allowing users to inspect model VRAM requirements before launching a persistent local or network-accessible inference server.

## 🚀 Key Features

* **Dual-Mode Operation**:
* **Inspect/Benchmark**: Uses `llama-cli.exe` to perform a 100-token dry run. This captures precise VRAM breakdown (Weights, KV Cache, Compute) and hardware speed (t/s).
* **Run Server**: Transitions to `llama-server.exe` to host a persistent OpenAI-compatible API and web-chat interface.


* **Smart Auto-Launch**: Monitors server logs in real-time and automatically opens your default web browser to `127.0.0.1:[Port]` only after the server confirms it is successfully listening.
* **Multimodal & Reasoning Ready**:
* Dedicated picker for `--mmproj` (CLIP/Vision) models.
* Full support for `--reasoning-budget` (-1 to 8192) for "thinking" models like DeepSeek-R1.


* **Network Flexibility**: Toggle "Share on Local Network" to bind the server to `0.0.0.0`, making your models accessible to other devices on your Wi-Fi/LAN.
* **One-Click Command Export**: A "Copy Command" button that captures the exact CLI string being used, including all active parameters, for manual terminal testing.

## 🛠️ Performance & Optimization

* **Mandatory MMAP**: The `--mmap` flag is hardcoded for all operations to ensure the most efficient memory management provided by the OS.
* **Embedding Support**: Includes a toggle to enable the `--embedding` flag, essential for Nomic, BERT, or other vector-based models.
* **Unified Batching**: Streamlined throughput control using the `-b` (Batch Size) flag.

## 📊 VRAM Visualization

The integrated RAM Bar provides a real-time safety check:

* **Grey**: Memory currently consumed by the OS and background apps.
* **Blue**: Projected model footprint (Weights + KV Cache + Compute Buffer).
* **Green**: Remaining free physical memory.
* **Red Alert**: Visual warning if the combined load exceeds 90% of your total system RAM.

## ⚙️ Requirements

1. **llama.cpp Binaries**: You must place `llama-cli.exe` and `llama-server.exe` in the same directory as the Python script. The app performs a safety check on startup and will not run if these are missing.
2. **Python 3.10+**
3. **Dependencies**:
```bash
pip install psutil

```



## 🖥️ Usage

1. **Browse**: Select your `.gguf` model.
2. **Optional**: Select an `mmproj` file if using a vision model.
3. **Benchmark**: Click "Inspect/Benchmark" to see if the model fits in your RAM and check its speed.
4. **Host**: Adjust your Port and Networking settings, then click "Run Server."
5. **Interact**: Wait for your browser to pop up and start chatting!

---

### 🌐 Connecting External Devices to Your GGUF Server

When you enable the **"Share on Local Network (Bind 0.0.0.0)"** feature, your computer stops acting like an isolated island and starts acting like a hub for other devices on your network. This is particularly useful for using your high-powered PC as a "brain" for mobile apps, tablets, or other laptops.

#### 1. Finding Your Host IP Address

To connect an external device, you cannot use `127.0.0.1` or `localhost`. You need your computer's **Local IPv4 Address**.

* **On Windows**: Open Command Prompt, type `ipconfig`, and look for "IPv4 Address" (usually starts with `192.168.x.x` or `10.0.x.x`).
* **In the App**: Ensure **Share on Local Network** is checked before clicking **Run Server**.

#### 2. Configuring External Apps

Many mobile apps (like **LibreChat**, **Chatbox**, or **PalChat**) support "Custom OpenAI API" endpoints. Use the following settings in those apps:

* **API Base URL**: `http://[YOUR_IP_ADDRESS]:[PORT]/v1` (e.g., `http://192.168.1.50:8080/v1`).
* **API Key**: You can usually leave this blank or enter any random string, as `llama-server` does not require one by default.
* **Model Name**: Enter the name of the model you have loaded.

#### 3. Accessing the Web UI from a Mobile Browser

If you just want to use the built-in `llama.cpp` chat interface on your phone:

1. Connect your phone to the **same Wi-Fi** as your PC.
2. Open your mobile browser (Chrome/Safari).
3. Type `http://[YOUR_IP_ADDRESS]:[PORT]` into the address bar.

#### ⚠️ Troubleshooting Connections

* **Windows Firewall**: If your phone cannot connect, Windows Firewall might be blocking `llama-server.exe`. You may need to add an "Inbound Rule" to allow traffic on your chosen port (e.g., 8080).
* **Network Profile**: Ensure your Windows network is set to **"Private"** rather than "Public," as "Public" settings often block incoming local connections by default.
* **Same Network**: Double-check that both devices are on the same router/subnet.

---


