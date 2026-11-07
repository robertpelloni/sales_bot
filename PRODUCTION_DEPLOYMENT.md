# Project Sirens - Production Deployment Guide

## 1. Hardware Requirements & Assembly
- **Compute Unit:** Raspberry Pi 5 (8GB) with active cooling.
- **Vision:** Sony IMX500 AI Camera (or any generic V4L2 USB Webcam).
- **Audio I/O:** Directional active speakers (ultrasonic preferred) + Beamforming USB Microphone Array (e.g. Anker PowerConf S3).

**Physical Assembly:**
1. Connect the camera via the CSI/PCIe ribbon cable.
2. Connect the Audio I/O via USB 3.0.
3. Boot the system on Raspberry Pi OS (Bookworm 64-bit).

## 2. Base OS Configuration
Update repositories and install docker.
Install hardware video dependencies for GStreamer/libcamera acceleration.

## 3. Cloning and Setup
Clone the repository using `--recursive`. Set up environment variables securely in a `.env` file (OPENAI_API_KEY and NODE_ID).

## 4. Run as a Systemd Service (Autostart on Boot)
Create a new service file (`/etc/systemd/system/sirens.service`) to ensure Docker spins up Project Sirens automatically on hardware restart utilizing `docker compose up -d --build`.

## 5. Security & Maintenance
- **API Keys:** Never commit `.env` to git.
- **Log Management:** Use `docker logs -f sirens_kiosk_1` to monitor LLM conversions.
- **OTA Updates:** To update the software, SSH into the Pi and run a `git pull origin main` and `git submodule update`. Then rebuild docker compose.
