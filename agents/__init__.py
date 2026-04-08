import re, json, logging

logger = logging.getLogger(__name__)


def parse_json_response(text: str) -> dict:
    """Parsea JSON de respuesta de Claude, tolerando markdown fences y texto extra."""
    text = text.strip()

    # 1. Remover markdown fences si existen
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text.strip())

    # 2. Intento directo
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # 3. Fallback: extraer el primer bloque JSON {...} balanceado del texto
    match = re.search(r"\{", text)
    if match:
        start = match.start()
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        result = json.loads(candidate)
                        logger.info("parse_json_response: usado fallback de extracción de JSON")
                        return result
                    except json.JSONDecodeError:
                        break

    # 4. Si nada funciona, lanzar error
    raise json.JSONDecodeError("No se pudo extraer JSON válido", text[:200], 0)
