from fastapi import FastAPI, Query
import uvicorn
from client.rq_client import queue
from rq.job import JobStatus

app = FastAPI()

@app.get('/')
def root():
    return {'status': 'Server is up and running'}

@app.post('/chat')
def chat(query:str = Query(..., description='Query for the user')):
    job = queue.enqueue("queues.worker.process_query", query)
    print(job)
    return {'status': 'Queued', "job_id": job.id}

@app.get('/job-status')
def get_response(jobid:str = Query(..., description='job_id for that query')):
    job = queue.fetch_job(jobid)
    if job is None:
        return {'status': 'not_found', 'result': None}

    status = job.get_status(refresh=True)

    if status == JobStatus.FINISHED:
        return {'status': 'finished', 'result': job.result}

    if status == JobStatus.FAILED:
        return {'status': 'failed', 'error': job.exc_info}

    return {'status': str(status), 'result': None}


uvicorn.run(app, port=8000, host='0.0.0.0')