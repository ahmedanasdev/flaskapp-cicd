Flask Application Documentation 
________________________________________
Overview
This is the first part of the CI/CD demo project. The application is a Flask-based web API that supports basic data storage and retrieval. It can work with either:
•	In-memory storage (default for local testing).
•	Redis as an external storage backend.
The app provides three main endpoints:
•	POST /data — Add a new value.
•	GET /data — Retrieve all stored values.
•	GET /health — Health check to ensure the service and storage are working.
•	GET / — HTML form for submitting values and viewing stored data.
________________________________________
Installation & Setup
1. Create Virtual Environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
2. Run Application (In-Memory Mode)
export USE_MEMORY_DB=1
python app.py
This will start the Flask app on http://localhost:8080 using an in-memory list for storage.
3. Run Application (With Redis)
export REDIS_URL=redis://localhost:6379/0
unset USE_MEMORY_DB
python app.py
This will connect the app to a running Redis instance.
________________________________________
API Usage
Add Data (POST /data)
curl -X POST -H "Content-Type: application/json" \
     -d '{"value":"hello"}' http://localhost:8080/data
Response:
{"value": "hello"}
Retrieve Data (GET /data)
curl http://localhost:8080/data
Response:
[{"value": "hello"}]
Health Check (GET /health)
curl http://localhost:8080/health
Response:
{"status": "ok"}
HTML Interface (GET /)
Visit http://localhost:8080 to use the HTML form for adding values and viewing stored data.
________________________________________
Notes
•	When USE_MEMORY_DB=1, data is stored in-memory and will reset every time the app restarts.
•	When REDIS_URL is set, data persists in Redis and is accessible across app restarts.
•	Default port is 8080, configurable via the PORT environment variable.
________________________________________
Next Steps
•	Create Dockerfile with multi-stage build.
•	Define docker-compose.yml for multi-container setup (Flask + Redis).
•	Add unit tests & integrate with CI/CD pipeline.
•	Deploy to AWS (EC2 or ECS).
________________________________________
🐳 Dockerization (Dev Setup)
🎯 Objective
Containerize the Flask app with Redis as a backend using multi-container setup.
We will use:
•	Dockerfile.dev → lightweight image for development (hot-reload, easy debugging).
•	docker-compose.yml → manage multi-containers (app + Redis).
________________________________________
📂 Files
1. Dockerfile.dev
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1
CMD ["python", "app.py"]
2. docker-compose.yml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8080:8080"
    volumes:
      - .:/app
    environment:
      - USE_MEMORY=false
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - PYTHONPATH=/app
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
      
________________________________________
🚀 Run the Project
docker-compose up --build
________________________________________
🧪 Test with Curl
# Add data
curl -X POST -H "Content-Type: application/json" -d '{"value":"hello"}' http://localhost:8080/data

# Get all data
curl http://localhost:8080/data

# Health check
curl http://localhost:8080/health
✅ Expected Output
{"value":"hello"}
[{"value":"hello"}]
{"status":"ok"}









📄 Documentation – Production Stage of Dockerfile
# Production stage
FROM python:3.10-slim
•	Uses a lightweight Python 3.10 slim image as the base for production.
•	Smaller size compared to full Python images, reducing attack surface and improving deployment speed.
WORKDIR /app
•	Sets the working directory inside the container to /app.
•	All subsequent commands (COPY, RUN, CMD, etc.) are executed relative to this path.
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn
•	Copies only the installed dependencies from the builder stage into the production image.
•	Ensures production image doesn’t contain build tools, making it smaller and more secure.
•	Specifically:
o	site-packages: all Python dependencies.
o	gunicorn: the WSGI server binary for running Flask.
COPY . .
•	Copies the entire application source code from the local machine into /app inside the container.
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
•	Creates a non-root user appuser for better security.
•	Changes ownership of /app to that user.
•	Switches to running the container as appuser (not root).
EXPOSE 8080
•	Informs Docker (and humans) that the application inside the container listens on port 8080.
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV USE_MEMORY_DB=0
•	Defines environment variables for production behavior:
o	FLASK_ENV=production: disables Flask debug mode.
o	PYTHONUNBUFFERED=1: forces stdout/stderr to be unbuffered (better logging).
o	USE_MEMORY_DB=0: ensures app uses external DB instead of in-memory fallback.
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:create_app()"]
•	Default command to start the app using Gunicorn.
•	-w 4: runs with 4 worker processes (parallel request handling).
•	-b 0.0.0.0:8080: binds the server to all interfaces on port 8080.
•	app:create_app(): entrypoint for the Flask app (factory pattern).
________________________________________
🚀 Build and Test Phase
Build the Production Image
docker build -t flaskapp-prod .
•	Builds the Docker image and tags it as flaskapp-prod.
•	Uses the Dockerfile in the current directory (.).
Run and Test the Container
docker run -p 8080:8080 -e USE_MEMORY_DB=1 flaskapp-prod
•	Runs the container from the flaskapp-prod image.
•	Maps container port 8080 to host port 8080.
•	Overrides the environment variable USE_MEMORY_DB to 1, forcing the app to use an in-memory DB for testing purposes.
•	Useful for local verification before deploying to production.










FlaskApp CI/CD Pipeline Documentation
Overview
This documentation explains the CI/CD pipeline setup for deploying a Flask application using GitHub Actions, Docker, and AWS Elastic Beanstalk. The pipeline automates build, test, and deployment processes to ensure consistent delivery.
________________________________________
Workflow: .github/workflows/ci.yml
Trigger Conditions
•	The workflow runs on:
o	Push events to the main branch.
o	Pull requests targeting the main branch.
Job: build-and-test-and-deploy
Runs on an Ubuntu-based GitHub Actions runner.
Steps:
1.	Checkout code
2.	uses: actions/checkout@v3
Fetches the source code from the repository for the workflow to use.
3.	Set up Docker Buildx
4.	uses: docker/setup-buildx-action@v2
Enables advanced Docker build capabilities, useful for multi-platform builds and caching.
5.	Login to Docker Hub
6.	uses: docker/login-action@v2
Authenticates to Docker Hub using credentials stored in GitHub Secrets (DOCKERHUB_USERNAME, DOCKERHUB_TOKEN).
7.	Build and Push Docker Image
8.	docker build -t ahmedanas04/flaskapp-prod:latest .
9.	docker push ahmedanas04/flaskapp-prod:latest
Builds the production image and pushes it to Docker Hub.
10.	Run Local Build for Testing
11.	docker build -t flaskapp-prod .
Builds a local image for testing before deployment.
12.	Run Tests
13.	docker run --rm -e USE_MEMORY_DB=1 -e PYTHONPATH=/app flaskapp-prod sh -c "pip install pytest==7.4.0 && export PATH=$PATH:/home/appuser/.local/bin && pytest tests/test_app.py"
Executes the test suite inside a container using pytest, ensuring application functionality.
14.	Deploy to AWS Elastic Beanstalk
15.	uses: einaregilsson/beanstalk-deploy@v21
Deploys the new Docker image to AWS Elastic Beanstalk.
Parameters:
o	application_name: flaskapp
o	environment_name: flaskapp-env
o	version_label: ${{ github.sha }} (unique identifier for each deployment)
o	region: us-east-1
o	deployment_package: Dockerrun.aws.json
________________________________________
Dockerrun.aws.json
Defines how Elastic Beanstalk should run the Docker container.
{
  "AWSEBDockerrunVersion": "1",
  "Image": {
    "Name": "ahmedanas04/flaskapp-prod:latest",
    "Update": "true"
  },
  "Ports": [
    {
      "ContainerPort": 8080,
      "HostPort": 80
    }
  ],
  "Environment": [
    {
      "Name": "FLASK_ENV",
      "Value": "production"
    },
    {
      "Name": "USE_MEMORY_DB",
      "Value": "1"
    }
  ],
  "Logging": "/var/log/gunicorn"
}
Explanation:
•	AWSEBDockerrunVersion: Defines the format version.
•	Image: Points to the Docker image on Docker Hub.
•	Ports: Maps container port 8080 to host port 80.
•	Environment: Defines app-level environment variables.
•	Logging: Specifies container log directory.
________________________________________
AWS Elastic Beanstalk Configuration
Environment Variables
Set within Elastic Beanstalk Console under Configuration → Software → Environment properties:
•	REDIS_ENDPOINT: Primary endpoint of AWS Redis OSS.
•	REDIS_PORT: Redis port number.
 <img width="975" height="108" alt="image" src="https://github.com/user-attachments/assets/a88fa181-136c-4d2f-a1b1-99d4f198470d" />

Networking
•	Ensure security groups allow inbound/outbound access for:
o	Port 8080 (app container)
o	Port 6379 (Redis)

 <img width="975" height="463" alt="image" src="https://github.com/user-attachments/assets/980f1eb7-6baf-4fb4-a32f-3442eb760d2d" />


________________________________________
Redis OSS Integration
•	AWS ElastiCache (Redis OSS) is used as the in-memory data store.
•	The Flask app connects to Redis using the endpoint and port defined in the environment variables.
 <img width="975" height="478" alt="image" src="https://github.com/user-attachments/assets/39e6b167-5066-410b-bbe1-467fa9221365" />

________________________________________
Summary
✅ The pipeline automates:
1.	Fetching source code
2.	Building and testing the Docker image
3.	Pushing the image to Docker Hub
4.	Deploying it to AWS Elastic Beanstalk
Redis OSS enhances performance by caching frequently used data.
________________________________________

<img width="975" height="206" alt="image" src="https://github.com/user-attachments/assets/b2eb9f3d-e2ee-4ec4-ae6f-53bdb4636f9b" />
<img width="975" height="118" alt="image" src="https://github.com/user-attachments/assets/71be8f84-bace-45c7-bdfb-80d99e355501" />
<img width="534" height="397" alt="image" src="https://github.com/user-attachments/assets/b3f34e21-5c6e-4471-a5a2-8576d0fcbb80" />



 

 

 

