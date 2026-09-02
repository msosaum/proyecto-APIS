"""
Agente mínimo — Entrega 1
Circuito: prompt -> modelo -> herramienta

La tool hace el cómputo determinista (pandas). El LLM decide:
  - qué parámetros pasarle a la tool según la pregunta del usuario
  - cómo interpretar y combinar el resultado para responder en lenguaje natural
"""

import os
import pandas as pd
from datetime import date

try:
    from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
    from langchain_core.tools import tool
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    HuggingFaceEndpoint = None
    ChatHuggingFace = None
    HumanMessage = SystemMessage = None

    def tool(func=None, **_kwargs):
        def decorator(function):
            return function

        if func is not None:
            return func
        return decorator

MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
HF_TOKEN = os.environ.get("HF_TOKEN")
CSV_PATH = "gastos_viaje.csv"

# ---------------------------------------------------------------------------
# 1) Capa determinista: la tool NO usa LLM, solo pandas.
# ---------------------------------------------------------------------------

@tool
def consultar_gastos(categoria: str = None, solo_pendientes: bool = False) -> dict:
    """
    Consulta los gastos del viaje desde la planilla.

    Args:
        categoria: filtra por categoría exacta (ej: 'alojamiento', 'comida',
                   'transporte', 'excursion'). Si es None, no filtra por categoría.
        solo_pendientes: si es True, devuelve solo los gastos con pagado == 'no'
                         (es decir, montos que todavía faltan pagar).

    Returns:
        dict con el total filtrado, la cantidad de gastos que entraron en el
        filtro, y el detalle fila por fila.
    """
    df = pd.read_csv(CSV_PATH)

    if categoria:
        df = df[df["categoria"] == categoria]
    if solo_pendientes:
        df = df[df["pagado"] == "no"]

    return {
        "total": float(df["monto"].sum()),
        "cantidad_items": int(len(df)),
        "detalle": df.to_dict(orient="records"),
    }


# ---------------------------------------------------------------------------
# 2) Capa agéntica: prompt inicial + modelo con acceso a la tool.
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = f"""Sos un asistente de viaje para un grupo que está viajando junto.
Tenés acceso a una herramienta llamada consultar_gastos que te permite obtener
totales y detalles de gastos reales del viaje, filtrando por categoría y/o por
si están pendientes de pago.

Reglas:
- Nunca inventes montos: si necesitás un número, llamá a la herramienta.
- Si la pregunta requiere combinar más de un filtro (por ejemplo, gastos ya
  pagados más gastos pendientes), llamá a la herramienta las veces que haga falta.
- Respondé siempre en español, de forma breve y concreta, mostrando los montos
  que usaste para llegar a la respuesta.
- La fecha de hoy es {date.today().isoformat()}.
"""

hf_endpoint = None
llm = None
llm_con_tools = None

if HF_TOKEN and HuggingFaceEndpoint is not None and ChatHuggingFace is not None:
    hf_endpoint = HuggingFaceEndpoint(
        repo_id=MODEL_ID,
        task="conversational",
        huggingfacehub_api_token=HF_TOKEN,
        temperature=0.3,
        max_new_tokens=512,
    )
    llm = ChatHuggingFace(llm=hf_endpoint)
    llm_con_tools = llm.bind_tools([consultar_gastos])

TOOLS_POR_NOMBRE = {"consultar_gastos": consultar_gastos}


def _respuesta_fallback(pregunta: str) -> str:
    """Respuesta determinista cuando no hay token ni acceso a modelo."""
    df = pd.read_csv(CSV_PATH)
    total = float(df["monto"].sum())
    pagado = float(df[df["pagado"] == "si"]["monto"].sum())
    pendiente = float(df[df["pagado"] == "no"]["monto"].sum())

    pregunta = pregunta.lower()
    if "pendiente" in pregunta or "falta pagar" in pregunta or "falta" in pregunta:
        return (
            f"Hasta ahora llevamos gastado ${total:,.0f} en total. "
            f"De ese total, ya está pagado ${pagado:,.0f} y aún falta pagar ${pendiente:,.0f}."
        )

    if "pagado" in pregunta or "ya gast" in pregunta or "total" in pregunta:
        return (
            f"Llevamos gastado ${total:,.0f} en total; "
            f"${pagado:,.0f} ya están pagados y falta pagar ${pendiente:,.0f}."
        )

    return (
        f"Llevamos gastado ${total:,.0f} en total. "
        f"Actualmente falta pagar ${pendiente:,.0f}."
    )


def ejecutar_agente(pregunta: str, max_iteraciones: int = 4) -> str:
    """Loop simple de tool-calling; si no hay modelo disponible, responde con
    cálculo determinista sobre la planilla."""
    if llm_con_tools is None or HumanMessage is None or SystemMessage is None:
        return _respuesta_fallback(pregunta)

    mensajes = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=pregunta)]

    for _ in range(max_iteraciones):
        respuesta = llm_con_tools.invoke(mensajes)
        mensajes.append(respuesta)

        if not respuesta.tool_calls:
            return respuesta.content

        for llamada in respuesta.tool_calls:
            tool_fn = TOOLS_POR_NOMBRE[llamada["name"]]
            resultado = tool_fn.invoke(llamada["args"])
            mensajes.append({
                "role": "tool",
                "content": str(resultado),
                "tool_call_id": llamada["id"],
            })

    return "No se pudo resolver la consulta en el número de pasos permitido."


if __name__ == "__main__":
    # La pregunta contraejemplo que justificamos en docs/E1.md
    pregunta = (
        "Ya hicimos la excursion a las Salinas Grandes. "
        "Todavia nos falta pagar el hostel de Purmamarca y la excursion "
        "al Cerro de los Siete Colores. Cuanto llevamos gastado en total "
        "y cuanto nos falta pagar?"
    )
    print("Pregunta:", pregunta)
    print("\nRespuesta del agente:\n")
    print(ejecutar_agente(pregunta))
