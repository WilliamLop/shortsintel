"""
Agente 2: Analyzer
Responsabilidad: Analizar los datos de un canal con Claude.
Entiende patrones de engagement, frecuencia, temas que funcionan.
"""

import json
import logging
import anthropic
from agents import parse_json_response

logger = logging.getLogger(__name__)


def analizar_canal(client: anthropic.Anthropic, datos_canal: dict) -> dict:
    """
    Recibe los datos crudos de un canal y usa Claude para extraer
    insights: qué funciona, frecuencia, engagement promedio, etc.
    """
    if "error" in datos_canal:
        return {"error": datos_canal["error"]}

    if not datos_canal.get("shorts_recientes"):
        return {
            "error": "Sin shorts disponibles para analizar",
            "handle": datos_canal.get("handle", ""),
            "nombre": datos_canal.get("nombre", ""),
            "suscriptores": datos_canal.get("suscriptores", 0),
        }

    # Preparar resumen de los shorts para Claude
    shorts_texto = ""
    for i, v in enumerate(datos_canal["shorts_recientes"][:10], 1):
        shorts_texto += f"{i}. '{v['titulo']}' | {v['vistas']:,} vistas | {v['likes']:,} likes | {v['fecha']}\n"

    prompt = f"""Analiza este canal de YouTube Shorts y extrae insights clave.

EJEMPLO DE RESPUESTA CORRECTA:
{{"engagement_promedio": 45000, "frecuencia_estimada": "5-6 videos/semana", "temas_exitosos": ["humor absurdo", "situaciones cotidianas", "personajes animados"], "titulo_patron": "Frases cortas en mayúsculas con emoji al final", "mejor_short": "Cuando tu mamá...", "mejor_short_vistas": 980000, "fortaleza_principal": "Humor relatable con personajes expresivos", "nivel_canal": "mediano", "potencial_crecimiento": "alto", "razon_potencial": "Nicho en crecimiento con baja saturación"}}

AHORA ANALIZA ESTE CANAL:
DATOS DEL CANAL:
- Nombre: {datos_canal['nombre']}
- Suscriptores: {datos_canal['suscriptores']:,}
- Total vistas: {datos_canal['total_vistas']:,}
- Total videos: {datos_canal['total_videos']}
- País: {datos_canal['pais']}
- Creado: {datos_canal['fecha_creacion']}

ÚLTIMOS SHORTS:
{shorts_texto}

Responde SOLO con un JSON válido con esta estructura exacta:
{{
  "engagement_promedio": <vistas promedio por short>,
  "frecuencia_estimada": "<ej: 3-4 videos/semana>",
  "temas_exitosos": ["tema1", "tema2", "tema3"],
  "titulo_patron": "<patrón que repiten en los títulos>",
  "mejor_short": "<título del short con más vistas>",
  "mejor_short_vistas": <número>,
  "fortaleza_principal": "<qué hace bien este canal>",
  "nivel_canal": "<pequeño/mediano/grande>",
  "potencial_crecimiento": "<alto/medio/bajo>",
  "razon_potencial": "<por qué tiene ese potencial>"
}}"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
    except anthropic.APIError as e:
        logger.error(f"Claude API error en analyzer | handle={datos_canal.get('handle')} | {e}")
        return {"error": f"Error de API: {str(e)}", "handle": datos_canal.get("handle", "")}

    logger.info(
        f"analyzer | handle={datos_canal.get('handle')} | "
        f"input_tokens={message.usage.input_tokens} | "
        f"output_tokens={message.usage.output_tokens}"
    )

    try:
        analisis = parse_json_response(message.content[0].text)
    except json.JSONDecodeError as e:
        raw = message.content[0].text[:500]
        logger.error(f"JSON inválido en analyzer | handle={datos_canal.get('handle')} | raw={raw!r} | {e}")
        return {"error": "Respuesta JSON inválida", "handle": datos_canal.get("handle", "")}

    analisis["handle"] = datos_canal["handle"]
    analisis["nombre"] = datos_canal["nombre"]
    analisis["suscriptores"] = datos_canal["suscriptores"]

    return analisis
