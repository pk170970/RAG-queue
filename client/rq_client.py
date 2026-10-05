from dotenv import load_dotenv
from rq import Queue
from rq.job import JobStatus
from redis import Redis
import time

load_dotenv()

queue = Queue(connection=Redis(
    host='localhost', 
    port=6379
))

# Redis(host="localhost", port=6379) creates a Redis-protocol client pointed at Valkey. Since Docker publishes Valkey on port 6379, localhost:6379 reaches it from your Python process.
# Queue(connection=...) creates an RQ queue, using its default name, default, and tells RQ to use that Valkey connection.

# user_query = input("Enter your question: ").strip()
# if not user_query:
#     raise ValueError("The query cannot be empty.")

# job = queue.enqueue("queues.worker.process_query", user_query)
# print(f"Enqueued query as job {job.id}")

# while True:
#     status = job.get_status(refresh=True)

#     if status == JobStatus.FINISHED:
#         print("Answer:")
#         print(job.result)
#         break

#     if status == JobStatus.FAILED:
#         print("The job failed:")
#         print(job.exc_info)
#         break

#     time.sleep(1)