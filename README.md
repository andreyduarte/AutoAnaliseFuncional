# Project Title (Consider replacing with a more descriptive title)

This project is a Flask application.

## Running with Docker Compose

To run this application using Docker Compose, follow these steps:

1.  **Ensure you have Docker and Docker Compose installed.**
    *   [Install Docker](https://docs.docker.com/get-docker/)
    *   [Install Docker Compose](https://docs.docker.com/compose/install/)

2.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

3.  **Run the application:**
    From the project root directory (where `docker-compose.yml` is located), execute the following command:
    ```bash
    docker-compose up
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
