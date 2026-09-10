# Agente mínimo — Asistente de gastos de viaje

Entrega 1: primera versión funcional del circuito **prompt → modelo → herramienta**.
No incluye memoria, recuperación de información ni control de flujo avanzado
(eso se trabaja en E2 y E3).

## Qué hace

El usuario le hace una pregunta en lenguaje natural sobre los gastos del viaje
(por ejemplo, si le alcanza para algo, cuánto lleva gastado, cuánto falta
pagar). El modelo decide si necesita consultar datos y, si es así, llama a la
herramienta `consultar_gastos`, que calcula el resultado real desde una
planilla (sin usar el LLM para el cómputo).

## Archivos

| Archivo | Descripción |
|---|---|
| `agente_viaje.py` | Script principal: prompt, tool y loop de ejecución |
| `gastos_viaje.csv` | Datos de prueba (gastos de un viaje inventado a Salta/Jujuy) |
| `README.md` | Este archivo |

## Requisitos

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Necesitás un token de Hugging Face con acceso a modelos de inferencia. El
agente **no funciona sin este token** (no hay modo offline ni respuesta de
respaldo): si falta o es inválido, `ejecutar_agente` lanza un `RuntimeError`
explicando qué falta.

## Cómo configurar el token

1. Creá una cuenta en [huggingface.co](https://huggingface.co) si no tenés una.
2. Generá un token en
   [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
   (alcanza con permisos de lectura / "Inference").
3. Asegurate de que tu cuenta tenga acceso al modelo usado
   (`Qwen/Qwen3-4B-Instruct-2507`, definido en `MODEL_ID` dentro de
   `agente_viaje.py`) y de que ese modelo tenga el proveedor de inferencia
   habilitado en tu cuenta de Hugging Face.
4. Exportá el token como variable de entorno **en la misma terminal** desde
   donde vas a correr el script:

   ```bash
   export HF_TOKEN="tu_token_aca"
   ```

   Para no repetir este paso en cada sesión, agregá esa línea a tu `~/.bashrc`,
   `~/.zshrc` (o equivalente) y abrí una terminal nueva.

5. Verificá que quedó seteada:

   ```bash
   echo $HF_TOKEN
   ```

   Si no imprime nada, el export no se aplicó (revisá que sea la misma
   terminal/sesión).

## Cómo ejecutarlo

Con el token ya configurado, corré:

```bash
python agente_viaje.py
```

Si ves un `RuntimeError` indicando que no se pudo inicializar el modelo,
repasá los pasos anteriores: normalmente es porque `HF_TOKEN` no está seteado,
el token no tiene permisos de inferencia, o faltan las dependencias
(`pip install langchain-huggingface langchain-core`).

Por defecto corre con la pregunta contraejemplo que justificamos en
`docs/E1.md`: cuánto se gastó y cuánto falta pagar, combinando un gasto ya
hecho, un gasto pendiente de una categoría y otro pendiente de otra.

## Probar con otras preguntas

Editá la variable `pregunta` al final de `agente_viaje.py`, o importá la
función en otro script:

```python
from agente_viaje import ejecutar_agente

print(ejecutar_agente("Cuanto gastamos en comida hasta ahora?"))
print(ejecutar_agente("Que gastos tenemos pendientes de pago?"))
```

## Notas de diseño

- La tool (`consultar_gastos`) es la única que toca los datos reales; usa
  `pandas`, no el LLM. Esto evita alucinaciones en los montos y evita pagar
  costo de inferencia por cálculos triviales.
- El modelo solo decide **qué** consultar y **cómo** presentar el resultado
  combinando una o más llamadas a la tool.
- Si el modelo no necesita datos para responder, responde directo sin llamar
  a la herramienta.
