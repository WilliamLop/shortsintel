# Shorts Intel

Analizador de nicho para YouTube Shorts con Flask, YouTube Data API y Claude.

La aplicación recibe una lista de canales competidores, extrae sus datos recientes desde YouTube, analiza sus patrones con IA y genera una estrategia accionable para tu propio canal.

## Qué hace

- Analiza hasta 10 handles de canales de YouTube Shorts.
- Obtiene métricas del canal y sus Shorts recientes con YouTube Data API v3.
- Usa Claude para detectar engagement, frecuencia, temas ganadores y patrones de títulos.
- Compara varios competidores para encontrar patrones del nicho.
- Genera una estrategia concreta para tu canal.
- Guarda cada resultado en `reportes/` como JSON.

## Flujo del sistema

1. `Fetcher`: consulta YouTube Data API y recopila datos del canal y sus videos.
2. `Analyzer`: analiza cada canal individualmente con Claude.
3. `Pattern Finder`: cruza los canales válidos y detecta patrones comunes.
4. `Strategist`: propone un plan de acción para el canal del usuario.

## Requisitos

- Python 3.9 o superior
- Una clave de `YouTube Data API v3`
- Una clave de `Anthropic API`

## Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuración

1. Copia `.env.example` a `.env`.
2. Completa las claves:

```bash
cp .env.example .env
```

Variables requeridas:

- `YOUTUBE_API_KEY`: clave para consultar canales, Shorts y estadísticas.
- `ANTHROPIC_API_KEY`: clave para ejecutar el análisis y la estrategia con Claude.

## Ejecutar la app

```bash
python app.py
```

Luego abre:

```text
http://127.0.0.1:5050
```

## Uso

En la interfaz web:

- Pega un handle por línea, por ejemplo `@MrBeast`.
- Escribe el nicho que quieres investigar.
- Describe brevemente tu canal o idea de canal.
- Ejecuta el análisis y espera el reporte.

La aplicación enviará progreso en tiempo real y al finalizar devolverá el resultado completo.

## Salida

Cada ejecución crea un archivo JSON dentro de `reportes/` con información como:

- canales analizados
- errores por handle
- patrones del nicho
- estrategia sugerida
- duración total del proceso

`reportes/` está ignorado por Git para evitar subir resultados generados.

## Estructura del proyecto

```text
.
├── agents/
│   ├── analyzer.py
│   ├── fetcher.py
│   ├── pattern_finder.py
│   └── strategist.py
├── templates/
│   └── index.html
├── app.py
├── orchestrator.py
├── requirements.txt
└── .env.example
```

## Notas

- El backend limita cada IP a 3 solicitudes por minuto.
- El análisis recorta la lista a un máximo de 10 handles por ejecución.
- Si YouTube o Anthropic fallan para algún canal, el sistema continúa con los demás cuando es posible.
- `venv/`, `.env`, `reportes/` y `.claude/` no se suben al repositorio.

## Próximos pasos sugeridos

- Agregar tests para los agentes y el orquestador.
- Mover la configuración de `debug=True` a variables de entorno.
- Añadir logging estructurado y manejo más fino de cuotas/errores de API.
