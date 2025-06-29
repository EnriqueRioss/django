import os
from django.conf import settings
from django.core.management.base import BaseCommand

# Importaciones de LangChain que acabamos de instalar
from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# --- CONFIGURACIÓN DE RUTAS ---
# Define la ruta a tus documentos de ayuda.
# Esto busca una carpeta 'chatbot_docs' dentro de tu app 'myapp'.
DOCS_DIR = os.path.join(settings.BASE_DIR, 'myapp', 'chatbot_docs')

# Define dónde se guardará la base de datos vectorial.
# Esto creará una carpeta 'chroma_db' en la raíz de tu proyecto.
CHROMA_DB_DIR = os.path.join(settings.BASE_DIR, 'chroma_db')

class Command(BaseCommand):
    """
    Comando de gestión de Django para construir o reconstruir la base de datos vectorial.
    Se ejecuta con: python manage.py build_vector_db
    """
    help = 'Construye la base de datos vectorial a partir de los documentos .md de la aplicación.'

    def handle(self, *args, **kwargs):
        # 1. Verificar que la API Key de Google esté disponible
        if not os.getenv("GOOGLE_API_KEY"):
            self.stdout.write(self.style.ERROR(
                "La variable de entorno GOOGLE_API_KEY no está configurada. "
                "Asegúrate de tener un archivo .env en la raíz del proyecto."
            ))
            return

        self.stdout.write(self.style.SUCCESS("Iniciando la construcción de la base de datos vectorial..."))

        # 2. Cargar los documentos Markdown
        self.stdout.write(f"Cargando documentos desde el directorio: {DOCS_DIR}")
        
        # Usamos DirectoryLoader para cargar todos los archivos .md de la carpeta.
        loader = DirectoryLoader(
            DOCS_DIR,
            glob="**/*.md",  # Patrón para encontrar archivos .md en subdirectorios también
            loader_cls=UnstructuredMarkdownLoader, # Especificamos cómo leer los .md
            show_progress=True,
            use_multithreading=True
        )
        documents = loader.load()

        if not documents:
            self.stdout.write(self.style.WARNING(
                "No se encontraron documentos .md para procesar. "
                "Asegúrate de que la carpeta 'myapp/chatbot_docs' exista y contenga archivos .md."
            ))
            return
            
        self.stdout.write(f"Se cargaron {len(documents)} documentos.")

        # 3. Dividir los documentos en trozos (chunks)
        # Esto es crucial para que el modelo pueda manejar textos largos y encontrar
        # fragmentos específicos.
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = text_splitter.split_documents(documents)
        self.stdout.write(f"Los documentos se han dividido en {len(chunks)} trozos (chunks).")

        # 4. Crear los embeddings y almacenarlos en ChromaDB
        self.stdout.write("Generando 'embeddings' (vectores numéricos) y guardándolos en ChromaDB... (esto puede tardar un momento)")
        
        # Seleccionamos el modelo de embeddings de Google. 'embedding-001' es eficiente y efectivo.
        embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        # Esta es la línea mágica:
        # - Toma los 'chunks' de texto.
        # - Usa 'embeddings_model' para convertirlos en vectores.
        # - Los guarda en el directorio especificado en 'persist_directory'.
        # Si la base de datos ya existe, la sobrescribirá con la nueva información.
        Chroma.from_documents(
            chunks, 
            embeddings_model, 
            persist_directory=CHROMA_DB_DIR
        )

        self.stdout.write(self.style.SUCCESS(
            f"¡Éxito! La base de datos vectorial ha sido creada/actualizada en la carpeta: {CHROMA_DB_DIR}"
        ))