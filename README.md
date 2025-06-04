(sem tempo pra escrever um bom README nesse momento, fiquem com a versão gerada por IA:)

# Como rodar localmente
This project is a Flask application.

## Running with Docker Compose

To run this application using Docker Compose, follow these steps:

1.  **Ensure you have Docker and Docker Compose installed.**
    *   [Install Docker](https://docs.docker.com/get-docker/)
    *   [Install Docker Compose](https://docs.docker.com/compose/install/)

2.  **Clone the repository (if you haven't already):**
    ```bash
    git clone https://github.com/andreyduarte/AutoAnaliseFuncional
    cd AutoAnaliseFuncional
    ```

    Create a copy of the `.env-example` file and rename it to `.env`. Put your GEMINI API Key in the `.env` file. 

3.  **Run the application:**
    From the project root directory (where `docker-compose.yml` is located), execute the following command:
    ```bash
    docker-compose up -d --build
    ```
    This command will build the Docker image (if it's the first time or if changes were made to the Dockerfile/application) and start the container.

4.  **Access the application:**
    Open your web browser and navigate to:
    [http://localhost:5000](http://localhost:5000)

## Development

The `docker-compose.yml` is configured to mount the current directory into the container. This means that changes made to the source code on your host machine will be reflected live in the running container, and Flask's development server will automatically reload.

## Stopping the application

To stop the application, press `Ctrl+C` in the terminal where `docker-compose up` is running.
To stop and remove the containers, you can run:
```bash
docker-compose down
```

## Data Persistence and Analysis Storage

This application now uses an SQLite database (`analysis_database.db`) to store all generated analyses, replacing the previous mechanism of saving to a single `output.json` file.

**Key Features:**

*   **Database Initialization:** The SQLite database and necessary tables are automatically created or verified when the Flask application starts. This is handled by the `init_db()` function in `db.py`, which is called from `app.py`. You can also manually initialize the database by running `python db.py` from the command line.
*   **Unique Analysis IDs:** Each analysis performed is saved as a new record in the database and assigned a unique UUID.
*   **Viewing Analyses:**
    *   The main page (`/`) now lists all saved analyses from the database.
    *   Each analysis in the list links to a dedicated viewing page using a URL structure like `/analysis/view/<analysis_uuid>`, where `<analysis_uuid>` is the unique ID of the analysis.
*   **Downloading Analyses:** From an individual analysis viewing page, you can download the complete analysis data in JSON format using the "Baixar Análise (JSON)" button.
*   **Database Interaction Module:** All database operations (initialization, insertion, querying) are managed by functions within the `db.py` module.

This database-driven approach allows for persistent storage of multiple analyses, easy access to individual results, and a more robust way to manage the application's data.
