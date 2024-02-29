#! /bin/bash
echo "" && echo "@@@@@@@@@@@@@@@ Step 1 : Install Docker"

sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "" && echo "@@@@@@@@@@@@@@@ Step 2 : Fetch docker compose file"

#curl -L -o docker-compose.yaml https://raw.githubusercontent.com/Valkea/Omdena_UN_GDC/main/05_pre_processing_build/docker-compose.yaml
curl -L -o docker-compose.yaml ${docker_compose_path}
ls

echo "" && echo "@@@@@@@@@@@@@@@ Step 3 : Perenize PREFECT environment variables"

echo "PREFECT_API_URL = ${PREFECT_API_URL}" >> .env
echo "PREFECT_API_KEY = ${PREFECT_API_KEY}" >> .env

echo "" && echo "@@@@@@@@@@@@@@@ Step 4 : Run a docker images"

# sudo docker run -d -p 5000:5000 --pull=always --restart=always --privileged "${docker_image}"
sudo docker compose up -d

echo "" && echo "@@@@@@@@@@@@@@@ Step 5 : Check the running images"

sudo docker ps -a
