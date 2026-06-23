# 🪐 NEMESIS Studio

NEMESIS Studio is a web-based graphical user interface (GUI) designed for running and managing simulations using the **NEMESIS** code.

## Architecture

This project is split into a frontend UI and a backend REST API server:

* **Backend (`server.py`)**: Built with **FastAPI** and served using **Uvicorn**. It exposes REST endpoints to manage and run the NEMESIS engine.
* **Frontend (`frontend.py`)**: Built with **Panel**, a high-level app and dashboarding framework. It communicates with the backend via REST requests.

---

## Installation

1. Clone this repository.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Application

To run the application, you must start the backend API server and the frontend UI in separate terminal windows.

### 1. Start the Backend API
Run the FastAPI server on port 8000:
```bash
python server.py
```
The interactive API documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 2. Start the Frontend UI
Run the Panel dashboard server:
```bash
panel serve frontend.py --show
```
This will automatically open the UI in your web browser (typically at [http://127.0.0.1:5006/frontend](http://127.0.0.1:5006/frontend)).
