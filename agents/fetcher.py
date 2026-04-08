"""
Agente 1: Fetcher
Responsabilidad: Obtener datos de YouTube API para cada canal.
Herramientas: YouTube Data API v3
"""

import time
import logging
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


def _fetch_with_retry(fetch_fn, max_retries=3, backoff_base=2.0):
    """Ejecuta fetch_fn con reintentos y exponential backoff."""
    for attempt in range(max_retries):
        try:
            return fetch_fn()
        except Exception as e:
            wait = backoff_base ** attempt
            logger.warning(f"Intento {attempt + 1} fallido: {e}. Reintentando en {wait}s")
            time.sleep(wait)
    logger.error("Todos los reintentos agotados")
    return None


def _validate_canal_schema(response) -> bool:
    """Verifica que la respuesta de la API tenga los campos requeridos."""
    if not response or not response.get("items"):
        return False
    item = response["items"][0]
    return all(k in item for k in ("id", "statistics", "snippet"))


def obtener_datos_canal(api_key: str, handle: str) -> dict:
    """
    Dado el handle de un canal (ej: @graciositto),
    retorna sus estadísticas y sus últimos 30 Shorts.
    """
    youtube = build("youtube", "v3", developerKey=api_key)

    # 1. Buscar el canal por handle
    response = _fetch_with_retry(
        lambda: youtube.channels().list(
            forHandle=handle.lstrip("@"),
            part="snippet,statistics,contentDetails"
        ).execute()
    )

    if response is None:
        return {"error": f"No se pudo conectar con YouTube API para {handle}"}

    if not _validate_canal_schema(response):
        return {"error": f"Canal {handle} no encontrado"}

    canal = response["items"][0]
    canal_id = canal["id"]
    stats = canal.get("statistics", {})
    snippet = canal.get("snippet", {})

    # 2. Obtener los Shorts recientes del canal
    shorts_response = _fetch_with_retry(
        lambda: youtube.search().list(
            channelId=canal_id,
            type="video",
            videoDuration="short",  # menos de 4 min (incluye Shorts)
            part="snippet",
            maxResults=30,
            order="date"
        ).execute()
    )

    if shorts_response is None:
        logger.warning(f"No se pudieron obtener Shorts de {handle}, continuando sin videos")
        shorts_response = {"items": []}

    video_ids = [
        item["id"]["videoId"]
        for item in shorts_response.get("items", [])
        if "videoId" in item.get("id", {})
    ]

    # 3. Obtener detalles de cada video
    videos = []
    if video_ids:
        detalles_response = _fetch_with_retry(
            lambda: youtube.videos().list(
                id=",".join(video_ids),
                part="snippet,statistics,contentDetails"
            ).execute()
        )

        if detalles_response:
            for video in detalles_response.get("items", []):
                stats_v = video.get("statistics", {})
                videos.append({
                    "titulo": video.get("snippet", {}).get("title", ""),
                    "fecha": video.get("snippet", {}).get("publishedAt", "")[:10],
                    "vistas": int(stats_v.get("viewCount", 0) or 0),
                    "likes": int(stats_v.get("likeCount", 0) or 0),
                    "comentarios": int(stats_v.get("commentCount", 0) or 0),
                    "duracion": video.get("contentDetails", {}).get("duration", ""),
                })

    logger.info(f"fetcher | handle={handle} | videos_obtenidos={len(videos)}")

    return {
        "handle": handle,
        "nombre": snippet.get("title", handle),
        "descripcion": snippet.get("description", "")[:200],
        "suscriptores": int(stats.get("subscriberCount", 0) or 0),
        "total_videos": int(stats.get("videoCount", 0) or 0),
        "total_vistas": int(stats.get("viewCount", 0) or 0),
        "pais": snippet.get("country", "N/A"),
        "fecha_creacion": snippet.get("publishedAt", "")[:10],
        "shorts_recientes": videos,
    }
