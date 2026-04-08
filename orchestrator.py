"""
Orquestador principal
Coordina los 4 agentes en secuencia:
Fetcher → Analyzer → Pattern Finder → Strategist
"""

import os
import json
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
import anthropic

from agents.fetcher import obtener_datos_canal
from agents.analyzer import analizar_canal
from agents.pattern_finder import encontrar_patrones
from agents.strategist import generar_estrategia

load_dotenv()

logger = logging.getLogger(__name__)


def ejecutar_analisis(handles: list[str], nicho: str, descripcion_canal: str, callback=None) -> dict:
    """
    Pipeline completo de análisis.

    Args:
        handles: Lista de @handles de canales a analizar
        nicho: Descripción del nicho (ej: "Historias animadas para niños")
        descripcion_canal: Descripción del canal del usuario
        callback: Función opcional para reportar progreso (para la UI)

    Returns:
        Diccionario con el reporte completo
    """
    youtube_key = os.getenv("YOUTUBE_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    # Validar configuración
    if not youtube_key:
        return {"error": "YOUTUBE_API_KEY no configurada", "code": "MISSING_CONFIG"}
    if not anthropic_key:
        return {"error": "ANTHROPIC_API_KEY no configurada", "code": "MISSING_CONFIG"}

    # Validar inputs
    if not handles:
        return {"error": "Lista de handles vacía", "code": "INVALID_INPUT"}
    if not nicho or not nicho.strip():
        return {"error": "Nicho no especificado", "code": "INVALID_INPUT"}

    # Deduplicar handles preservando orden
    handles = list(dict.fromkeys(h.strip() for h in handles if h.strip()))

    client = anthropic.Anthropic(api_key=anthropic_key)
    inicio = time.time()

    reporte = {
        "nicho": nicho,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "canales_analizados": [],
        "patrones": {},
        "estrategia": {},
        "errores": []
    }

    # ─── AGENTE 1: Fetcher + Agente 2: Analyzer (por cada canal) ───
    total = len(handles)
    for i, handle in enumerate(handles, 1):
        if callback:
            callback(f"🔍 [{i}/{total}] Obteniendo datos de {handle}...")

        # Agente 1: obtiene datos de YouTube
        datos = obtener_datos_canal(youtube_key, handle)

        if "error" in datos:
            reporte["errores"].append({"handle": handle, "razon": datos["error"], "etapa": "fetcher"})
            if callback:
                callback(f"⚠️ {handle}: no encontrado, se omite")
            continue

        if callback:
            callback(f"🤖 [{i}/{total}] Claude analizando {datos['nombre']}...")

        # Agente 2: Claude analiza los datos
        analisis = analizar_canal(client, datos)

        if "error" not in analisis:
            reporte["canales_analizados"].append(analisis)
            if callback:
                callback(f"✅ {datos['nombre']} — {analisis.get('suscriptores', 0):,} subs | potencial: {analisis.get('potencial_crecimiento', '?')}")
        else:
            reporte["errores"].append({"handle": handle, "razon": analisis["error"], "etapa": "analyzer"})

    canales_ok = len(reporte["canales_analizados"])
    tasa_exito = canales_ok / len(handles) if handles else 0

    if canales_ok == 0:
        return {"error": "No se pudo analizar ningún canal", "code": "NO_DATA", "errores": reporte["errores"]}

    if canales_ok < 2 and tasa_exito < 0.3:
        return {
            "error": f"Solo {canales_ok} canal(es) analizados con éxito. Verifica los handles.",
            "code": "INSUFFICIENT_DATA",
            "errores": reporte["errores"]
        }

    # ─── AGENTE 3: Pattern Finder ───
    if callback:
        callback("🧠 Buscando patrones en el nicho...")

    try:
        reporte["patrones"] = encontrar_patrones(client, reporte["canales_analizados"], nicho)
    except Exception as e:
        logger.error(f"Pattern finder falló: {e}")
        reporte["patrones"] = {"error": str(e)}
        if callback:
            callback(f"⚠️ Advertencia: no se pudieron encontrar patrones ({e})")

    # ─── AGENTE 4: Strategist ───
    if callback:
        callback("📋 Generando estrategia para tu canal...")

    try:
        reporte["estrategia"] = generar_estrategia(client, reporte["patrones"], nicho, descripcion_canal)
    except Exception as e:
        logger.error(f"Strategist falló: {e}")
        reporte["estrategia"] = {"error": str(e)}
        if callback:
            callback(f"⚠️ Advertencia: no se pudo generar la estrategia ({e})")

    if callback:
        callback("✅ ¡Análisis completo!")

    reporte["_duracion_segundos"] = round(time.time() - inicio, 1)

    # Guardar reporte en disco
    nombre_archivo = f"reportes/reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("reportes", exist_ok=True)
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)

    reporte["archivo_guardado"] = nombre_archivo
    return reporte


if __name__ == "__main__":
    # Prueba rápida desde terminal
    handles = [
        "@graciositto",
        "@risaventuras",
        "@zonadimbo",
        "@GarraGol",
        "@FlickZex",
        "@UnCortito_"
    ]

    resultado = ejecutar_analisis(
        handles=handles,
        nicho="Historias animadas cortas para niños y jóvenes",
        descripcion_canal="Canal de muñecos y personajes animados para niños, creado 100% con IA",
        callback=print
    )

    print("\n" + "="*50)
    print("ESTRATEGIA GENERADA:")
    print(json.dumps(resultado["estrategia"], ensure_ascii=False, indent=2))
