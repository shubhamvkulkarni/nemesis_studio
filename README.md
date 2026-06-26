# 🪐 NEMESIS Studio

**NEMESIS** (Non-linear optimal Estimator for MultivariatE spectral analySIS) is a highly versatile and robust planetary atmospheric radiative transfer and retrieval code. Originally developed for analyzing planetary spectra, it is widely used by researchers to model atmospheric properties, retrieve temperature profiles, and determine gas and aerosol abundances across various planetary bodies. 
[Original NEMESIS Repository](https://github.com/nemesiscode/radtrancode)

**NEMESIS Studio** is a web-based graphical user interface (GUI) designed to simplify the process of running and managing simulations using the NEMESIS code. By providing an intuitive visual frontend, it makes powerful atmospheric retrieval and modeling accessible to users without needing to interact directly with the command line.

## Architecture

This project is split into a frontend UI and a backend REST API server:

* **Backend (`server.py`)**: Built with **FastAPI** and served using **Uvicorn**. It exposes REST endpoints to manage and run the NEMESIS engine.
* **Frontend (`frontend.py`)**: Built with **Panel**, a high-level app and dashboarding framework. It communicates with the backend via REST requests and renders the application in a standalone desktop window using **pywebview**.

---

## Installation

1. Clone this repository.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure you have Docker installed and running, as NEMESIS simulations are run via the `patrickirwinoxford/docker_nemesis` image.

---

## Running the Application

Right now, NEMESIS Studio can be simply run using the provided shell script:

```bash
./frontend.sh
```

This script will automatically start the required services and open the NEMESIS Studio application window.

---

## Workspaces

NEMESIS Studio is organized into three distinct workspaces, tailored to different levels of expertise:

### 1. Outreach
Designed for a general audience or educational purposes. It provides a pre-configured, easy-to-use interface to view atmospheric models (such as Pressure/Temperature, Gases, and Aerosols) and run radiative transfer simulations for pre-selected planets like Jupiter and Venus.

### 2. Beginner
Intended for users who want to run their own data but need a guided experience. You can select a local working directory and provide a "runname" to plot atmospheric models and view radiative transfer simulations. 
*(Note: Input configuration options for this workspace are currently under construction.)*

### 3. Advance
A comprehensive workspace that will allow expert configuration of atmospheric profiles, parameter files, and complex retrieval settings. 
*(Note: This workspace is currently under construction.)*
