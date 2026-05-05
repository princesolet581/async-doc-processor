# Async Document Processing Workflow System

## Architecture Overview

This project is a Full Stack application built to handle document processing asynchronously.
- **Frontend**: Next.js (App Router) using React and Vanilla CSS (no Tailwind). Real-time progress updates are handled via Server-Sent Events (SSE).
- **Backend**: FastAPI (Python) for handling RESTful endpoints and managing the job lifecycle.
- **Database**: PostgreSQL for persistent storage of document metadata, job status, and extracted results.
- **Background Workers**: Celery workers process the document parsing and extraction asynchronously.
- **Message Broker & Pub/Sub**: Redis acts as the message broker for Celery and facilitates the Pub/Sub system to stream live progress updates back to the FastAPI server and subsequently to the client.

## Run Steps

1. Make sure you have Docker and Docker Compose installed on your system.
2. Ensure Docker Desktop is running (if on Windows/Mac).
3. Open a terminal in this directory.
4. Run the following command:
   ```bash
   docker compose up --build
   ```
5. Wait for all containers to start. The initial build might take a few minutes.
6. Open your browser and navigate to:
   - Frontend Dashboard: `http://localhost:3000`
   - Backend API Docs (Swagger): `http://localhost:8000/docs`

## Setup Instructions (Local without Docker)

If you wish to run the components locally without Docker:
1. Start a local PostgreSQL instance and a Redis server.
2. In `backend/`, create a virtual environment, activate it, and run `pip install -r requirements.txt`.
3. Start the backend: `uvicorn main:app --reload`.
4. Start the Celery worker: `celery -A celery_app.celery worker --loglevel=info`.
5. In `frontend/`, run `npm install` followed by `npm run dev`.

## Assumptions
- The parsing and extraction stages are simulated using `time.sleep` and randomized data to represent real processing time and structured output generation.
- Real-time updates using Server-Sent Events (SSE) assume the client will remain on the detail page to view live updates; otherwise, the status is fetched directly from the database on page load.
- File storage is not fully abstracted to AWS S3 or a local persistent directory; for the scope of this assignment, the `UploadFile` content is only read to generate jobs, but the actual binary file isn't stored permanently.

## Tradeoffs
- **SSE vs WebSockets**: SSE was chosen for simplicity and because the server only needs to push progress events to the client. Full-duplex communication (WebSockets) wasn't strictly necessary.
- **Simulated Logic**: To focus on the async workflow, OCR and advanced AI extraction were stubbed out. This trade-off allows the core architectural requirements (Celery, Redis Pub/Sub) to be heavily tested.
- **Vanilla CSS vs Tailwind**: Built using Vanilla CSS to demonstrate custom styling without relying on utility frameworks, resulting in a slightly larger CSS file but fewer dependencies.

## Limitations
- Actual file processing (like PDF parsing) is not implemented.
- Authentication is not included in this iteration.
- The PostgreSQL database is rebuilt every time the docker container restarts because data volumes might not be completely persistent if the named volume is pruned.

## Development Note
**Note:** AI Assistant tools (Google Deepmind's Gemini model) were used to scaffold the architecture, generate boilerplate code for Next.js and FastAPI, and write the application logic during development.
