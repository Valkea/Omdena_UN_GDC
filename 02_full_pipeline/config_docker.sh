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

echo "" && echo "@@@@@@@@@@@@@@@ Step 2 : Run a docker image"

sudo docker run -d -p 5000:5000 --pull=always --privileged valkea/deploy_lab:latest

echo "" && echo "@@@@@@@@@@@@@@@ Step 3 : Check the running images"

sudo docker ps -a
