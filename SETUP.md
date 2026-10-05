# RAG Queue Setup

This project serves questions through FastAPI, queues them with RQ using
Valkey, retrieves relevant document chunks from Qdrant, and asks Gemini to
generate an answer. This repository handles retrieval and answering; ingest
the documents first using the sibling `RAG` project.

## Step 1: Fork the projects

1. Fork both repositories: [RAG](https://github.com/pk170970/RAG), which
   handles ingestion, and this `RAG-queue` repository, which contains the
   retrieval API and worker.
2. Keep both project folders side by side on your computer.

   The resulting layout should look like:

   ```text
   <parent-folder>\
   ├── RAG\
   └── RAG-queue\
   ```

3. Make sure Docker Desktop is running and that the PDF exists at
   `RAG\materials\ncc_book.pdf`.

The commands below assume you open a PowerShell terminal in the indicated
project folder. If your folders are elsewhere, open the terminal at
their actual locations.

## Step 2: Prepare the ingestion project

Open PowerShell in the `RAG` folder.

Activate the virtual environment for this project and install its dependencies.
The `RAG\requirements.txt` includes `sentence-transformers`, which is used to
create document embeddings. If this project does not already have a `.venv`,
create one before activating it:

```powershell
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) { python -m venv .venv }
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a `.env` file in the `RAG` folder and add your key:

```env
GEMINI_API_KEY=your_actual_key
```

Do not commit or share the real key. The current ingestion script checks for
this key even though it creates embeddings using the local Hugging Face
sentence-transformers model.

## Step 3: Start Qdrant

Still in the `RAG` folder, start the vector database:

```powershell
docker compose up -d
```

This starts Qdrant at `http://localhost:6333`. The Qdrant data is persisted in
the `qdrant_storage` Docker volume.

## Step 4: Ingest the PDF into Qdrant

With Qdrant running and the `RAG` virtual environment active, run:

```powershell
python ingest.py
```

The script reads `materials\ncc_book.pdf`, splits its pages into chunks,
creates embeddings with `sentence-transformers/all-MiniLM-L6-v2`, and writes
the chunks and page metadata to the Qdrant collection
`course_documents-3`. Wait for the command to finish before moving on.

You need to repeat ingestion when you want to add or refresh the source
documents. The query API does not perform ingestion.

## Step 5: Prepare the retrieval/API project

Open another PowerShell terminal in the `RAG-queue` folder.

Activate this project's virtual environment and install its dependencies. If
this project does not already have a `.venv`, create one first:

```powershell
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) { python -m venv .venv }
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a `.env` file in the `RAG-queue` folder with the same Gemini key:

```env
GEMINI_API_KEY=your_actual_key
```

The retrieval worker reads this key to call Gemini. Keep both `.env` files
private; do not commit or share the real key.

## Step 6: Start Valkey

In the `RAG-queue` folder, start Valkey:

```powershell
docker compose up -d
```

This starts Valkey at `localhost:6379`. RQ uses Valkey to store queued jobs,
job status, and completed results. Qdrant and Valkey are separate services:
Qdrant stores document vectors, while Valkey stores queue/job data.

## Step 7: Start the FastAPI server

In a terminal at `RAG-queue`, with its virtual environment active:

```powershell
python server.py
```

The API listens on port `8000`. Keep this terminal running.

## Step 8: Start RQ worker(s)

In a second terminal at `RAG-queue`, activate the same virtual environment and
run:

```powershell
rq worker --worker-class rq.worker.SimpleWorker --path . default
```

On Windows, use `SimpleWorker` because RQ's default worker uses `os.fork()`,
which Windows does not provide. `--path .` makes the project folder importable
so the worker can load `queues.worker.process_query`.

Each worker processes one job at a time. To run additional workers, open more
terminals at `RAG-queue`, activate the same virtual environment, and run the
same command. They all listen to the `default` queue and each job is handled
by one available worker. The useful number of workers depends on your
computer's resources.

## Step 9: Submit a query and retrieve its result

Open FastAPI's interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

1. Expand **POST `/chat`**, select **Try it out**, enter the query, and select
   **Execute**.
2. Copy the `job_id` from the response. The endpoint queues the job and
   returns before the answer is ready.
3. Expand **GET `/job-status`**, select **Try it out**, enter the copied ID in
   the `jobid` field, and select **Execute**.
4. If the status is `queued` or `started`, check again after a short wait.
   When it is `finished`, the response contains the answer in `result`. If it
   is `failed`, inspect the error in the response and the worker terminal.

The root health endpoint is `http://127.0.0.1:8000/`.

## Startup checklist

Before submitting a query, make sure:

- Qdrant is running from the `RAG` project.
- `python ingest.py` completed and populated `course_documents-3`.
- Valkey is running from the `RAG-queue` project.
- The FastAPI server is running.
- At least one RQ worker is listening on the `default` queue.
