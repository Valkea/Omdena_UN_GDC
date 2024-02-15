# Omdena_UN_GDC


## 06_full_build

> Note: one needs to replace `valkea` with its own docker-hub profile.

### 01 - Get .PEM files
One needs to get .PEM files to allow Terraform to access the AWS account

### 02 - Setup PREFECT
Register the PREFECT blocks and deployment into the PREFECT Cloud

```code
>>> make setup
```

### 03 - Build the `PREFECT Flows` container and push it.
```code
>>> docker build -t ungdc_prefect_flows . -f Dockerfile.flows
>>> docker tag ungdc_prefect_flows:latest valkea/ungdc_prefect_flows:latest
>>> docker push valkea/ungdc_prefect_flows:latest
```

### 04 - Build the `PREFECT Agent` container and push it. 
```code
>>> docker build -t ungdc_prefect_agent . -f Dockerfile.agent
>>> docker tag ungdc_prefect_agent:latest valkea/ungdc_prefect_agent:latest
>>> docker push valkea/ungdc_prefect_flows:latest
```

## 06_full_deploy

### 01 - Credentials
One needs to create an `.env` file with the following keys:
- AWS_ACCESS_KEY
- AWS_SECRET_KEY
- PREFECT_API_URL
- PREFECT_API_KEY

One also needs to get .PEM files to allow Terraform to upload the script that will be executed to install and run the initial docker image.

### 02 - Setup PREFECT
Register the PREFECT blocks and deployment into the PREFECT Cloud

Edit `setup_prefect.py` and

```code
>>> make setup
```

### 03 - Populate the AWS infrastructure
At first this will setup and run the requested infrastures then it will pull and run the `PREFECT Agent`docker which will in turn pull and run the `PREFECT Flows` container whenever requested through the PREFECT Cloud interface (or via command lines).

```code
>>> terraform plan
>>> terraform apply
```
(From inside the terraform folder)

### 04 - Destroy the AWS infrastructure
To shut down the deployment, one can use the following command:

```code
>>> terraform destroy
```
(From inside the terraform folder)
