from dotenv import load_dotenv
import os
from langchain_google_genai import ( #connect langchain to gemini
    ChatGoogleGenerativeAI,
)   
from langchain_qdrant import QdrantVectorStore # search your qudarnt collection
from langchain_huggingface import HuggingFaceEmbeddings

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "course_documents-3"
CHAT_MODEL = 'gemini-3.5-flash-lite'

def process_query(user_query:str):
    load_dotenv()

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise RuntimeError('Add Gemini api key to your .env file')
    
    if not user_query:
        print('Please enter the question')
        return

    embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        ) 
    
    vector_store = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        url='http://localhost:6333'
    )

    matching_chunks = vector_store.similarity_search(query=user_query, k = 8)
    
    if not matching_chunks:
        print("I couldn't find relevant information in ingested documents")
        return
    
    context = []
    source_pages = []

    for doc in matching_chunks:
        printed_page = doc.metadata.get("printed_page") or "unknown"
        pdf_page = doc.metadata.get("pdf_page", "unknown")

        context.append(
            f"[Printed book page {printed_page} | PDF Page {pdf_page}]\n"
            f"{doc.page_content}"
        )
        source_pages.append(
            f"Book page {printed_page} (PDF page {pdf_page})"
        )
    
    
    PROMPT = f'''
    You are an expert AI assistant who takes the user query and relevant information from vector database and reply the user based on that available context retrived from the pdf file along with the page content and page number.
    Do not invent page citations.
    Do not answer if something is not present in context.

    Rule: Cite only printed book page labels shown in the context. Do not invent page numbers.
    Answer only when the retrieved context supports the answer. If it does not,
    say that you could not find relevant information in the ingested documents.
    Cite printed page numbers only when an actual printed page label is present;
    never invent or require a citation.

    Context:
    {context}

    Question:
    {user_query}
    '''

    chatModel = ChatGoogleGenerativeAI(
        model = CHAT_MODEL,
        google_api_key = api_key,
        temperature=0
    )
    response = chatModel.invoke(PROMPT)
    print('\nAnswer:')
    print(response.text)
    print("\nSources:")
    return response.text