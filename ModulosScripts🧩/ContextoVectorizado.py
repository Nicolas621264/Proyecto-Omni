import warnings
warnings.filterwarnings('ignore')
import nest_asyncio
nest_asyncio.apply()
import os
import logging
import pyperclip
import asyncio
import openai
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración del modelo de embeddings
embeddings_model = 'all-MiniLM-L6-v2'
embeddings = HuggingFaceEmbeddings(model_name=embeddings_model)

# Configuración de OpenAI
openai.api_key = "OPENAI_API_KEY"
model_engine = "gpt-4o-mini"

# Ruta específica de la base de datos vectorial
VECTOR_DB_PATH = r"C:\Users\54115\Desktop\Omni\BaseDeDatos📁\Vectorizado"

# Prompt específico para la generación de contexto
CONTEXT_PROMPT = """
Por favor, genera un contexto coherente y detallado basado en:
1. La pregunta/contenido original del usuario
2. Los fragmentos relevantes encontrados en la base de datos

Tu tarea es:
- Analizar los fragmentos proporcionados
- Relacionarlos con la pregunta/contenido original
- Generar una respuesta que integre la información de manera natural y útil
- Mantener la relevancia con respecto a la consulta original

Responde de manera clara y concisa, asegurándote de que la información sea precisa y relevante.
"""

async def generate_context(fragments, query_text):
    """
    Genera un contexto utilizando la API de OpenAI basado en los fragmentos y la consulta.
    """
    try:
        # Construir el mensaje completo
        full_message = f"""
Contenido original del usuario:
{query_text}

Fragmentos relevantes encontrados:
{fragments}
"""
        # Imprimir lo que se enviará a la API
        print("\n=== CONTENIDO QUE SE ENVIARÁ A LA API ===")
        print("\n--- PROMPT DEL SISTEMA ---")
        print(CONTEXT_PROMPT)
        print("\n--- CONTENIDO DEL USUARIO ---")
        print(full_message)
        print("=====================================\n")

        response = await openai.ChatCompletion.acreate(
            model=model_engine,
            messages=[
                {"role": "system", "content": CONTEXT_PROMPT},
                {"role": "user", "content": full_message}
            ],
            max_tokens=1500,
        )
        
        generated_content = response.choices[0].message['content']
        print("\n=== RESPUESTA GENERADA POR LA API ===")
        print(generated_content)
        print("=====================================\n")
        
        return generated_content
    except Exception as e:
        logger.error(f"Error al generar contexto con OpenAI: {str(e)}")
        return None

async def search_fragments():
    try:
        # Obtener texto del portapapeles
        query_text = pyperclip.paste()
        if not query_text.strip():
            print("No hay texto en el portapapeles. Por favor, copia algún texto antes de ejecutar el script.")
            return
        
        print("\n=== CONTENIDO DEL PORTAPAPELES ===")
        print(query_text)
        print("===================================\n")
        
        print("Buscando fragmentos similares...")
        
        # Cargar la base de datos vectorial
        db = Chroma(
            persist_directory=VECTOR_DB_PATH,
            embedding_function=embeddings
        )
        
        # Buscar los 10 fragmentos más similares
        fragments = db.similarity_search_with_score(query_text, k=10)
        
        # Formatear resultados
        results = []
        for i, (doc, score) in enumerate(fragments, 1):
            results.append(f"Fragmento {i} (Similitud: {score:.4f}):\n{doc.page_content}\n")
        
        # Unir resultados
        fragments_text = "\n".join(results)
        
        print("\n=== FRAGMENTOS ENCONTRADOS ===")
        print(fragments_text)
        print("==============================\n")
        
        # Generar contexto con OpenAI
        print("Generando contexto con OpenAI...")
        context = await generate_context(fragments_text, query_text)
        
        if context:
            # Copiar el contexto generado al portapapeles
            pyperclip.copy(context)
            print("\n¡Listo! El contexto generado ha sido copiado al portapapeles.")
        else:
            print("Error al generar el contexto. Copiando solo los fragmentos...")
            pyperclip.copy(fragments_text)
        
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    """Función principal para ejecutar el proceso"""
    try:
        await search_fragments()
        print("Proceso completado")
    except Exception as e:
        print(f"Error en el proceso principal: {e}")

if __name__ == '__main__':
    asyncio.run(main())