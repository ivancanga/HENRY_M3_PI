# Sistema Multi-Agente RAG con LangGraph

Sistema de routing inteligente para una empresa SaaS que clasifica
automáticamente las consultas entrantes por departamento (RR. HH., Soporte
Técnico, Finanzas) y las deriva a agentes RAG especializados. Un agente
orquestador clasifica la intención de cada consulta y, mediante enrutamiento
condicional con **LangGraph**, delega la respuesta al agente del dominio
correcto, que la fundamenta en la documentación interna de la empresa. Un agente
evaluador puntúa cada respuesta y todo el flujo queda trazado en **Langfuse**
para observabilidad y monitoreo de calidad.

## Arquitectura

```
Usuario pregunta
  → orquestador clasifica la intención (hr / tech / finance / unknown)
  → LangGraph enruta de forma condicional
  → agente RAG especializado recupera contexto de SU dominio (Chroma)
  → el LLM responde usando solo esos documentos (grounded)
  → evaluator puntúa la respuesta (LLM-as-judge)
  → Langfuse traza todo el flujo y registra los scores
```

```mermaid
flowchart LR
    START([START]) --> ORCH[orchestrator]

    ORCH -->|hr| HR[hr]
    ORCH -->|tech| TECH[tech]
    ORCH -->|finance| FIN[finance]
    ORCH -->|unknown| UNK[unknown]

    HR --> EVAL[evaluator]
    TECH --> EVAL
    FIN --> EVAL

    EVAL --> FIN_END([END])
    UNK --> UNK_END([END])

    UNK -.->|sin RAG ni evaluación| UNK_END

    LF[(Langfuse<br/>tracing)]
    ORCH -. traza .-> LF
    EVAL -. traza .-> LF

    classDef start fill:#22c55e,stroke:#15803d,color:#fff;
    classDef node fill:#3b82f6,stroke:#1e40af,color:#fff;
    classDef eval fill:#a855f7,stroke:#7e22ce,color:#fff;
    classDef ending fill:#64748b,stroke:#334155,color:#fff;
    classDef obs fill:#ec4899,stroke:#be185d,color:#fff;

    class START start;
    class ORCH,HR,TECH,FIN,UNK node;
    class EVAL eval;
    class FIN_END,UNK_END ending;
    class LF obs;
```

## Estructura del proyecto

```
HENRY_M3_PI/
├── data/                       # Bases de conocimiento (3 dominios, .md)
│   ├── hr_docs/                # ~86 chunks
│   ├── tech_docs/              # ~89 chunks
│   └── finance_docs/           # ~90 chunks
├── src/
│   ├── config.py               # configuración central (claves, rutas, parámetros)
│   ├── rag.py                  # RAG: load → chunk → embeddings → Chroma → retriever
│   ├── agents.py               # router (orquestador) + nodos especialistas
│   ├── evaluator.py            # nodo evaluator (LLM-as-judge)
│   ├── langfuse_setup.py       # observability (callback + scores)
│   ├── graph.py                # grafo LangGraph + ruteo condicional
│   └── main.py                 # CLI (--query, --validate, interactivo)
├── test_queries.json           # 12 consultas de prueba con intención esperada
├── requirements.txt            # dependencias
├── .env.example                # plantilla de variables de entorno
└── README.md
```

## Instalación

### Opción A — con uv (recomendado)

```bash
git clone <repo-url>
cd HENRY_M3_PI
uv sync                 # crea el entorno e instala las dependencias
```

### Opción B — con pip

```bash
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configurar las API keys

Copiá la plantilla y completá tus claves:

```bash
cp .env.example .env
```

Editá `.env`:

```env
OPENAI_API_KEY=sk-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com   # o https://us.cloud.langfuse.com
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

- `OPENAI_API_KEY` es necesaria para embeddings, respuestas y evaluación.
- Las claves de Langfuse son opcionales: sin ellas el sistema corre igual, solo
  que no trazea (degradación elegante).

## Cómo ejecutar

Con uv anteponé `uv run`; con pip activá el entorno y usá `python`.

```bash
# Validar el proyecto (cuenta chunks por dominio y chequea el ruteo, sin Chroma)
uv run python -m src.main --validate

# Ejecutar una consulta
uv run python -m src.main --query "¿Cuántos días de vacaciones tengo con 5 años?"

# Modo interactivo (loop hasta escribir 'salir')
uv run python -m src.main
```

> La primera consulta construye las colecciones Chroma (hace embeddings de los
> documentos) y las persiste en `chroma_db/`. Las siguientes corridas las reusan.

### Ejemplos de uso

Tres consultas reales, cada una clasificada y enrutada al agente especialista correcto:

---

#### 🔧 IT / Soporte Técnico

**❓ Pregunta:** *Necesito cambiar mi contraseña del correo corporativo*
**🎯 Intent:** `tech`

**💬 Respuesta:**
> Para cambiar la contraseña de tu correo corporativo:
> 1. Ingresá al portal de identidad corporativa con tu usuario y contraseña actual.
> 2. Entrá a **Seguridad → Cambiar contraseña**.
> 3. Escribí la contraseña actual y la nueva (mínimo 12 caracteres: letras, números y símbolos).
> 4. Confirmá con el segundo factor (MFA) y guardá los cambios.
>
> El cambio aplica de inmediato a todos los sistemas conectados por SSO, incluido el correo.

**📄 Fuentes:** `seguridad_contrasenas.md` · **⭐ Calidad:** `overall 10` (relevance 10 · completeness 10 · accuracy 10 · clarity 10)

---

#### 👥 Recursos Humanos

**❓ Pregunta:** *¿Cuántos días de vacaciones tengo con 6 años de antigüedad?*
**🎯 Intent:** `hr`

**💬 Respuesta:**
> Tenés 28 días hábiles de vacaciones por año con 6 años de antigüedad.

**📄 Fuentes:** `politica_vacaciones_pto.md` · **⭐ Calidad:** `overall 10` (relevance 10 · completeness 10 · accuracy 10 · clarity 10)

---

#### 💰 Finanzas

**❓ Pregunta:** *¿Cuándo se acredita un reembolso de gastos aprobado?*
**🎯 Intent:** `finance`

**💬 Respuesta:**
> El reembolso se acredita junto con el salario: si se aprueba antes del día 20 del mes, en ese mes; si no, en el siguiente.

**📄 Fuentes:** `reembolsos.md`, `reportes_gastos.md` · **⭐ Calidad:** `overall 10` (relevance 10 · completeness 10 · accuracy 10 · clarity 10)

---

## Decisiones técnicas

- **Orquestación con enrutamiento condicional.** Separo *decidir a qué
  especialista mandar la consulta* de *responderla*: un orquestador clasifica y
  el grafo enruta condicionalmente al agente correcto. Elegí LangGraph sobre una
  cadena lineal porque deja el ruteo explícito y permite sumar un dominio nuevo
  agregando un nodo, sin reescribir el flujo.
- **Clasificación con salida estructurada.** El orquestador no devuelve texto
  libre: fuerza al modelo a producir una decisión validada (una intención de un
  conjunto cerrado). Esto hace el ruteo confiable y predecible, e incluye una
  categoría `unknown` para no responder consultas ambiguas o fuera de dominio
  (mejor decir "no es mi área" que contestar mal).
- **Conocimiento aislado por dominio.** Cada agente tiene su propia base de
  conocimiento y solo busca ahí. Es la decisión central del proyecto: evita que
  el agente de RR. HH. responda con un documento de Finanzas y ataca directamente
  el problema de las consultas mal enrutadas.
- **Respuestas fundamentadas (grounding).** Los agentes responden únicamente con
  los fragmentos recuperados de la documentación; si la información no está, lo
  dicen en vez de inventar. Reduce alucinaciones y asegura que las respuestas
  reflejen las políticas reales de la empresa.
- **Búsqueda semántica persistente.** Las consultas se resuelven por *significado*
  (embeddings), no por coincidencia exacta de palabras. Elegí Chroma sobre FAISS
  porque persiste en disco y maneja una colección por dominio sin código extra; a
  esta escala el rendimiento es equivalente, así que prioricé la simplicidad.
- **Control de calidad automático (LLM-as-judge).** Un segundo modelo evalúa cada
  respuesta antes de que llegue al cliente y detecta cuándo el agente se desvía
  del contexto. Convierte la calidad en algo medible, no en una impresión.
- **Observabilidad de extremo a extremo.** Todo el recorrido de cada consulta
  queda trazado en Langfuse, lo que permite depurar una mala clasificación o un
  retrieval fallido inspeccionando el flujo completo, en lugar de adivinar.

## Notas de configuración

- Parámetros de RAG (`chunk_size`, `chunk_overlap`, `retriever_k`) y modelos se
  ajustan en un único lugar: `src/config.py`.
- Para reconstruir las colecciones desde cero, borrá la carpeta `chroma_db/`.
- Langfuse 4.x: las credenciales se configuran vía el cliente `Langfuse(...)`; el
  `CallbackHandler` ya no recibe `secret_key`/`host` (los toma del entorno).

## Limitaciones conocidas

- El sistema responde en 3 dominios (HR, Tech, Finance); cualquier otra consulta
  cae en `unknown`.
- Las respuestas dependen de la calidad y cobertura de los documentos en `data/`;
  si la información no está, el agente responde que no la tiene.
- El evaluador es un LLM-as-judge: es una guía de calidad, no un juicio infalible.
- Requiere conexión a internet y una API key de OpenAI con saldo para funcionar
  con RAG real.
```
