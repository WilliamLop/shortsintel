"""
Agente 4: Strategist
Responsabilidad: Generar una estrategia concreta y accionable
para el canal del usuario basada en los patrones encontrados.
"""

import json
import logging
import anthropic
from agents import parse_json_response

logger = logging.getLogger(__name__)


def generar_estrategia(client: anthropic.Anthropic, patrones: dict, nicho: str, descripcion_canal: str) -> dict:
    """
    Toma los patrones del nicho y genera un plan de acción
    concreto: qué publicar, cuándo, cómo, con qué herramientas IA.
    """
    frecuencia_ideal = patrones.get("frecuencia_ideal", "4-5 videos/semana")

    # Enviar solo los campos que el strategist realmente necesita (ahorro de tokens)
    patrones_compacto = {
        "canal_lider": patrones.get("canal_lider", "N/A"),
        "frecuencia_ideal": frecuencia_ideal,
        "duracion_ideal": patrones.get("duracion_ideal", "N/A"),
        "temas_que_funcionan": patrones.get("temas_que_funcionan", []),
        "patron_titulos": patrones.get("patron_titulos", "N/A"),
        "elementos_clave": patrones.get("elementos_clave", []),
        "oportunidad_detectada": patrones.get("oportunidad_detectada", "N/A"),
    }

    prompt = f"""Eres un estratega experto en canales de YouTube Shorts con IA (sin cámaras, sin actores).

NICHO: {nicho}
CANAL DEL USUARIO: {descripcion_canal}

PATRONES DEL NICHO:
{json.dumps(patrones_compacto, ensure_ascii=False)}

PRINCIPIOS DE OPTIMIZACIÓN:
- Hook: primeros 3 seg = conflicto o promesa, sin logos ni intros
- CTR: títulos para superar 8% usando curiosidad, números o promesa extrema
- Miniaturas: alto contraste, sujeto claro, máx 3 palabras, legible en móvil
- Retención: 50%+ viewers a los 15 seg, contenido valioso en medio
- Frecuencia: consistencia > calidad — mejor 5 buenos que 2 perfectos
- CTA: cada Short termina llevando al siguiente video (no "gracias por ver")

Genera estrategia CONCRETA. El usuario crea 100% con IA (animaciones, voces IA).

Responde SOLO con JSON válido:
{{
  "nombre_sugerido_canal": "<nombre atractivo>",
  "propuesta_valor": "<diferenciador del canal>",
  "plan_semanal": "<basado en {frecuencia_ideal}, días óptimos con tipo de video — formato: {{'dia': 'tipo'}}>",
  "primeros_7_videos": [
    "<idea 1>", "<idea 2>", "<idea 3>", "<idea 4>",
    "<idea 5>", "<idea 6>", "<idea 7>"
  ],
  "herramientas_ia_recomendadas": [
    {{"herramienta": "", "uso": "", "precio_aprox": ""}},
    {{"herramienta": "", "uso": "", "precio_aprox": ""}},
    {{"herramienta": "", "uso": "", "precio_aprox": ""}}
  ],
  "estructura_video": "<cómo estructurar cada Short: hook, desarrollo, cierre>",
  "hook_estructura": "<primeros 3 segundos para este nicho>",
  "concepto_miniatura": "<elemento visual, texto máx 3 palabras, paleta>",
  "formula_titulo": "<fórmula con trigger psicológico para este nicho>",
  "ctr_objetivo": "<% objetivo y cómo lograrlo>",
  "clave_para_crecer": "<factor más importante>",
  "meta_3_meses": "<qué lograr en 3 meses>",
  "meta_suscriptores_3_meses": <número>,
  "meta_6_meses": "<qué lograr en 6 meses>",
  "meta_suscriptores_6_meses": <número>
}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system="Eres un generador de estrategias en formato JSON. Responde EXCLUSIVAMENTE con un JSON válido, sin texto adicional, sin explicaciones, sin markdown. Solo el objeto JSON.",
            messages=[{"role": "user", "content": prompt}]
        )
    except anthropic.APIError as e:
        logger.error(f"Claude API error en strategist | nicho={nicho} | {e}")
        return {"error": f"Error de API: {str(e)}"}

    logger.info(
        f"strategist | nicho={nicho} | "
        f"input_tokens={message.usage.input_tokens} | "
        f"output_tokens={message.usage.output_tokens}"
    )

    try:
        return parse_json_response(message.content[0].text)
    except json.JSONDecodeError as e:
        raw = message.content[0].text[:500]
        logger.error(f"JSON inválido en strategist | raw={raw!r} | {e}")
        return {"error": "Respuesta JSON inválida"}
