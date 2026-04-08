"""
Agente 3: Pattern Finder
Responsabilidad: Comparar todos los canales analizados y encontrar
patrones comunes en los más exitosos del nicho.
"""

import json
import logging
import anthropic
from agents import parse_json_response

logger = logging.getLogger(__name__)


def encontrar_patrones(client: anthropic.Anthropic, analisis_canales: list, nicho: str) -> dict:
    """
    Recibe el análisis de todos los canales y extrae patrones
    comunes: qué hacen los mejores, qué tienen en común.
    """
    # Filtrar canales con error
    canales_validos = [c for c in analisis_canales if "error" not in c]

    if not canales_validos:
        return {"error": "No se pudieron analizar los canales"}

    if len(canales_validos) < 2:
        return {
            "error": "Se necesitan al menos 2 canales válidos para encontrar patrones",
            "nicho": nicho,
            "total_canales_analizados": len(canales_validos),
        }

    # Ordenar por suscriptores para identificar los top
    canales_ordenados = sorted(canales_validos, key=lambda x: x.get("suscriptores", 0), reverse=True)

    resumen = ""
    for c in canales_ordenados:
        resumen += f"""
Canal: {c['nombre']} ({c['handle']})
- Suscriptores: {c.get('suscriptores', 0):,}
- Engagement promedio: {c.get('engagement_promedio', 0):,} vistas/short
- Frecuencia: {c.get('frecuencia_estimada', 'N/A')}
- Temas exitosos: {', '.join(c.get('temas_exitosos', []))}
- Patrón de títulos: {c.get('titulo_patron', 'N/A')}
- Potencial: {c.get('potencial_crecimiento', 'N/A')}
- Fortaleza: {c.get('fortaleza_principal', 'N/A')}
"""

    prompt = f"""Eres un experto en estrategia de contenido para YouTube Shorts.
Analiza estos {len(canales_validos)} canales del nicho "{nicho}" y encuentra los patrones de éxito.

{resumen}

EJEMPLO de formato correcto para top_3_canales:
{{"nombre": "NombreCanal", "razon": "Lidera por su consistencia de 7 videos/semana y engagement del 8%"}}

Responde SOLO con un JSON válido con esta estructura:
{{
  "nicho": "{nicho}",
  "total_canales_analizados": {len(canales_validos)},
  "canal_lider": "<nombre del canal con más suscriptores>",
  "frecuencia_ideal": "<frecuencia que más se repite en los exitosos>",
  "duracion_ideal": "<duración recomendada de Shorts en este nicho>",
  "temas_que_funcionan": ["tema1", "tema2", "tema3", "tema4", "tema5"],
  "patron_titulos": "<cómo estructuran los títulos los canales exitosos>",
  "elementos_clave": ["elemento1", "elemento2", "elemento3"],
  "oportunidad_detectada": "<gap o oportunidad que no están aprovechando>",
  "top_3_canales": [
    {{"nombre": "", "razon": ""}},
    {{"nombre": "", "razon": ""}},
    {{"nombre": "", "razon": ""}}
  ]
}}"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system="Responde EXCLUSIVAMENTE con un JSON válido. Sin texto adicional, sin explicaciones, sin markdown.",
            messages=[{"role": "user", "content": prompt}]
        )
    except anthropic.APIError as e:
        logger.error(f"Claude API error en pattern_finder | nicho={nicho} | {e}")
        return {"error": f"Error de API: {str(e)}", "nicho": nicho}

    logger.info(
        f"pattern_finder | nicho={nicho} | canales={len(canales_validos)} | "
        f"input_tokens={message.usage.input_tokens} | "
        f"output_tokens={message.usage.output_tokens}"
    )

    try:
        return parse_json_response(message.content[0].text)
    except json.JSONDecodeError as e:
        raw = message.content[0].text[:500]
        logger.error(f"JSON inválido en pattern_finder | raw={raw!r} | {e}")
        return {"error": "Respuesta JSON inválida", "nicho": nicho}
