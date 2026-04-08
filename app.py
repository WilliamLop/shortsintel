"""
App web con Flask
Interfaz simple para correr el análisis desde el navegador.
"""

import json
import queue
import time
import threading
from collections import defaultdict
from flask import Flask, render_template, request, Response, stream_with_context
from orchestrator import ejecutar_analisis

app = Flask(__name__)

MAX_HANDLES = 10
RATE_LIMIT_PER_MINUTE = 3
_rate_limits: dict = defaultdict(list)


def _check_rate_limit(ip: str) -> bool:
    now = time.time()
    calls = [c for c in _rate_limits[ip] if now - c < 60]
    _rate_limits[ip] = calls
    if len(calls) >= RATE_LIMIT_PER_MINUTE:
        return False
    _rate_limits[ip].append(now)
    return True


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analizar", methods=["POST"])
def analizar():
    if not _check_rate_limit(request.remote_addr):
        return {"error": "Demasiadas solicitudes. Espera 1 minuto.", "code": "RATE_LIMITED"}, 429

    handles_raw = request.form.get("handles", "")
    nicho = request.form.get("nicho", "").strip()[:200]
    descripcion = request.form.get("descripcion", "").strip()[:500]

    handles = [h.strip() for h in handles_raw.split("\n") if h.strip()]
    handles = handles[:MAX_HANDLES]

    if not handles or not nicho:
        return {"error": "Faltan datos"}, 400

    cola: queue.Queue = queue.Queue()

    def correr_analisis():
        try:
            def cb(msg):
                cola.put({"tipo": "progreso", "mensaje": msg})
            resultado = ejecutar_analisis(handles, nicho, descripcion, callback=cb)
            cola.put({"tipo": "resultado", "data": resultado})
        except Exception as e:
            cola.put({"tipo": "resultado", "data": {"error": str(e), "code": "INTERNAL_ERROR"}})

    hilo = threading.Thread(target=correr_analisis, daemon=True)
    hilo.start()

    def generar():
        deadline = time.time() + 300  # 5 minutos máximo
        while True:
            try:
                remaining = max(1, deadline - time.time())
                item = cola.get(timeout=remaining)
            except queue.Empty:
                timeout_msg = {"tipo": "resultado", "data": {"error": "Tiempo de espera agotado", "code": "TIMEOUT"}}
                yield f"data: {json.dumps(timeout_msg, ensure_ascii=False)}\n\n"
                break
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
            if item["tipo"] == "resultado":
                break

    return Response(
        stream_with_context(generar()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.errorhandler(Exception)
def handle_exception(e):
    return {"error": "Error interno del servidor", "code": type(e).__name__}, 500


if __name__ == "__main__":
    app.run(debug=True, port=5050)
