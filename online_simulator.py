import asyncio
import struct
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

app = FastAPI()

# 6 Transformers State Storage (سیمولیٹر کا لائیو کنٹرول ڈیٹا)
transformers_data = {
    1: {"v": 6600.0, "a": 132.0, "kw": 845.0, "pf": 0.98, "hz": 50.0},
    2: {"v": 440.0, "a": 185.0, "kw": 178.0, "pf": 0.97, "hz": 50.0},
    3: {"v": 440.0, "a": 106.0, "kw": 195.0, "pf": 0.96, "hz": 50.0},
    4: {"v": 440.0, "a": 246.0, "kw": 986.0, "pf": 0.98, "hz": 50.0},
    5: {"v": 440.0, "a": 106.0, "kw": 195.0, "pf": 0.96, "hz": 50.0},
    6: {"v": 800.0, "a": 6840.0, "kw": 5492.0, "pf": 1.00, "hz": 50.0},
}

def float_to_registers(value):
    packed = struct.pack('>f', float(value))
    return struct.unpack('>HH', packed)

async def update_modbus_context(context, transformer_id):
    """آن لائن پینل سے تبدیل شدہ ڈیٹا کو Modbus Registers (ATZ2000 FC04) میں سنک رکھنا"""
    while True:
        data = transformers_data[transformer_id]
        slave = context[0]
        # ATZ2000 Modbus-TCP Input Registers
        slave.setValues(4, 0, float_to_registers(data["v"]))
        slave.setValues(4, 8, float_to_registers(data["a"]))
        slave.setValues(4, 18, float_to_registers(data["kw"]))
        slave.setValues(4, 42, float_to_registers(data["pf"]))
        slave.setValues(4, 70, float_to_registers(data["hz"]))
        await asyncio.sleep(0.5)

# --- 🎛️ SIMULATOR WEB CONTROL PANEL ---
@app.get("/control", response_class=HTMLResponse)
async def control_panel():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Online ATZ2000 Simulator Controller</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-900 text-white p-6 font-sans">
        <h1 class="text-2xl font-bold text-sky-400 mb-2">MicroTrade Online Meter Simulator</h1>
        <p class="text-sm text-slate-400 mb-6">Controllable Live Output for 6 Transformers (ATZ2000 Modbus TCP Stream)</p>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="controls"></div>

        <script>
            const initialData = """ + str(transformers_data).replace("'", '"') + """;
            
            function renderControls() {
                const container = document.getElementById('controls');
                let html = '';
                for (let i = 1; i <= 6; i++) {
                    const d = initialData[i];
                    html += `
                        <div class="bg-slate-800 p-4 rounded-xl border border-slate-700 space-y-3">
                            <h2 class="font-bold text-lg text-emerald-400 border-b border-slate-700 pb-2">Transformer T${i}</h2>
                            <div>
                                <label class="text-xs text-slate-400">Voltage (V): <span id="v_val_${i}">${d.v}</span></label>
                                <input type="range" min="0" max="10000" step="10" value="${d.v}" class="w-full" oninput="updateVal(${i}, 'v', this.value)">
                            </div>
                            <div>
                                <label class="text-xs text-slate-400">Current (A): <span id="a_val_${i}">${d.a}</span></label>
                                <input type="range" min="0" max="7000" step="1" value="${d.a}" class="w-full" oninput="updateVal(${i}, 'a', this.value)">
                            </div>
                            <div>
                                <label class="text-xs text-slate-400">Active Power (kW): <span id="kw_val_${i}">${d.kw}</span></label>
                                <input type="range" min="0" max="6000" step="5" value="${d.kw}" class="w-full" oninput="updateVal(${i}, 'kw', this.value)">
                            </div>
                            <div>
                                <label class="text-xs text-slate-400">Power Factor (PF): <span id="pf_val_${i}">${d.pf}</span></label>
                                <input type="range" min="0.5" max="1.0" step="0.01" value="${d.pf}" class="w-full" oninput="updateVal(${i}, 'pf', this.value)">
                            </div>
                        </div>
                    `;
                }
                container.innerHTML = html;
            }

            async function updateVal(id, param, val) {
                document.getElementById(`${param}_val_${id}`).innerText = val;
                await fetch('/api/update', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({id: id, param: param, value: parseFloat(val)})
                });
            }

            renderControls();
        </script>
    </body>
    </html>
    """

@app.post("/api/update")
async def update_data(req: Request):
    body = await req.json()
    t_id = body["id"]
    param = body["param"]
    val = body["value"]
    transformers_data[t_id][param] = val
    return {"status": "success"}

# --- 📡 LIVE STREAMING DATA API ---
@app.get("/api/stream")
async def get_stream():
    return JSONResponse(content=transformers_data)

@app.on_event("startup")
async def start_modbus_servers():
    # 6 Modbus TCP Ports (5021 to 5026) Background Tasks
    for i in range(1, 7):
        port = 5020 + i
        store = ModbusSlaveContext(ir=ModbusSequentialDataBlock(0, [0] * 100))
        context = ModbusServerContext(slaves=store, single=True)
        asyncio.create_task(update_modbus_context(context, i))
        asyncio.create_task(StartAsyncTcpServer(context, address=("0.0.0.0", port)))