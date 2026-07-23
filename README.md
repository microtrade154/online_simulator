# MicroTrade ATZ2000 Online Simulator

A cloud-ready 6-Transformer Energy Meter Simulator supporting Modbus-TCP protocol and a web-based real-time control interface.

## 🚀 Features
- **6 Transformers Telemetry:** Simulates Voltage, Current, Active Power, Power Factor, and Frequency.
- **Modbus-TCP Protocol:** Exposes Modbus-TCP registers on ports 5021 to 5026.
- **Live Control Panel:** Adjust transformer parameters dynamically via `/control`.
- **JSON Stream API:** Live JSON output available at `/api/stream` for easy dashboard integration.

## 🛠️ Tech Stack
- **FastAPI** (Web Framework & REST API)
- **PyModbus** (Modbus-TCP Server)
- **Uvicorn** (ASGI Server)

## 💻 Local Quick Start
```bash
pip install -r requirements.txt
uvicorn online_simulator:app --host 0.0.0.0 --port 10000
