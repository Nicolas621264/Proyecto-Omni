import logging
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredHTMLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define paths
TEMP_PATH = r"C:\Users\54115\Desktop\Omni\BaseDeDatos📁\Descargas"
VECTOR_PATH = r"C:\Users\54115\Desktop\Omni\BaseDeDatos📁\Vectorizado"

# Initialize embeddings model
embeddings_model = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')

def ensure_directory_exists(directory):
    """Create directory if it doesn't exist"""
    os.makedirs(directory, exist_ok=True)

def get_appropriate_loader(file_path):
    """Return the appropriate document loader based on file extension"""
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.pdf':
        return PyPDFLoader(file_path)
    elif file_extension in ['.html', '.htm']:
        return UnstructuredHTMLLoader(file_path)
    elif file_extension in ['.txt', '.md', '.json']:
        return TextLoader(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {file_extension}")

def vectorize_file(file_path):
    """Vectorize a single file and add it to the vector database"""
    try:
        # Get appropriate loader
        loader = get_appropriate_loader(file_path)
        
        # Load and split the document
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)

        # Initialize Chroma database
        vector_db = Chroma(
            persist_directory=VECTOR_PATH,
            embedding_function=embeddings_model
        )

        # Add documents to the vector database
        vector_db.add_documents(texts)
        vector_db.persist()

        logger.info(f"Successfully vectorized: {file_path}")
        return True

    except Exception as e:
        logger.error(f"Error vectorizing {file_path}: {str(e)}")
        return False

def process_temp_folder():
    """Process all supported files in the temp folder"""
    # Ensure vector database directory exists
    ensure_directory_exists(VECTOR_PATH)
    
    # Supported file extensions
    supported_extensions = {'.txt', '.pdf', '.html', '.htm', '.md', '.json'}
    
    # Process each file in the temp directory
    for filename in os.listdir(TEMP_PATH):
        file_path = os.path.join(TEMP_PATH, filename)
        
        # Skip if not a file
        if not os.path.isfile(file_path):
            continue
            
        # Check if file extension is supported
        file_extension = os.path.splitext(filename)[1].lower()
        if file_extension not in supported_extensions:
            logger.warning(f"Skipping unsupported file: {filename}")
            continue
            
        # Vectorize the file
        logger.info(f"Processing file: {filename}")
        success = vectorize_file(file_path)
        
        if success:
            logger.info(f"Successfully processed: {filename}")
        else:
            logger.error(f"Failed to process: {filename}")

if __name__ == "__main__":
    logger.info("Starting vectorization process...")
    process_temp_folder()
    logger.info("Vectorization process completed.")