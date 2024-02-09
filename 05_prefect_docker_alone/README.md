We need a `.env` file with the PREFECT_API_URL (without /api at the end) and the PREFECT_API_KEY

We need to build 2 Docker images :
- the "Flows" image contains the Prefect flows and will be called by the Docker Prefect Block registered in the cloud (using the Makefile and more specifically the setup_prefect.py)
- the "Agent" image the the one to deploy somewhere (on some EC2 instance etc...) and which will actually use the Docker Prefect Block to download and call the "Flows" docker image (we can also use the docker-compose file because it is easier to pass all the required parameters)
