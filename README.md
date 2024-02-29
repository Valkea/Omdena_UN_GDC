# Omdena_UN_GDC

Check the `lab` folder to explore the various elements of the deployement more easily.

## 1 - Credentials
One needs to create an `.env` file with the following keys:
- AWS_ACCESS_KEY
- AWS_SECRET_KEY
- PREFECT_API_URL (format is https://api.prefect.cloud/api/accounts/{ACCOUNT_ID}/workspaces/{PROJECT_ID})
- PREFECT_API_KEY

> Note: add a copy to both `05_pre_processing_build` (to build the docker images and run the docker-compose locally) and `06_pre_processing_deploy/terraform` (to run the docker compose remotly)

One also needs to get .PEM files to allow Terraform to upload the script that will be executed to install and run the initial docker image.

## 2 - Build `PREFECT Flows` and `PREFECT Agent` images

> Note: one needs to replace `valkea` with its own docker-hub profile.

### 2.1 - Build the `PREFECT Flows` container and push it.
```code
>>> docker build -t ungdc_prefect_flows . -f Dockerfile.flows
>>> docker tag ungdc_prefect_flows:latest valkea/ungdc_prefect_flows:latest
>>> docker push valkea/ungdc_prefect_flows:latest
```

### 2.2 - Build the `PREFECT Agent` container and push it. 
```code
>>> docker build -t ungdc_prefect_agent . -f Dockerfile.agent
>>> docker tag ungdc_prefect_agent:latest valkea/ungdc_prefect_agent:latest
>>> docker push valkea/ungdc_prefect_flows:latest
```

> Note: We could improve this with a GitHub Action or CirlceCI CI/CD to automatically build and push the containers on the docker hub or on the AWS ECS.

## 03 - Setup PREFECT Cloud
In order to be able to control the deployed `PREFECT Agent`, we need to register the PREFECT blocks and pthe deployement on the PREFECT Cloud server.

### 3.1 - Edit the files
Edit `config.cfg` and update the various fields.

### 3.2 - Register the PREFECT blocks and deployment into the PREFECT Cloud
```code
>>> make setup
```

## 4 - (OPTIONAL) Running the pre-processing pipeline locally
In order to test and run the Prefect pre-processing locally, one can use the following commands:

```code
>>> cd {to the directory with the docker-compose.yaml file. Currently 05_pre_processing_build}
>>> docker compose up
```

### 4.1
On the Prefect pipeline is running, you can test it by waiting the the cronjob and by triggering the Deployment on the Prefect Cloud.

- go to your [Prefect Cloud](https://app.prefect.cloud)
- select the right `Deployment` and click `...` 
- initialize a `Custom run` of the deployment with `max_doc` = 1
- check the run in `Flow runs` and explore (the first run might take time, because it needs to download the 5Gb docker image of the Pre-processing pipeline)


## 5 - Deployment
Let's use Terraform the provision the ressources and deploy our `PREFECT Agent`

### 5.1 - Generate AWS .PEM files (from the AWS website)
Generate AWS .PEM files (from the AWS website) and place them (.pem and .pem.pub)  in the terraform folder.

### 5.2 - Edit the files
Edit `terraform/variables.tf` and update the various fields.

### 5.3 - Populate the AWS infrastructure

Use the following commands from inside the terraform folder, to see the plan and apply the plan:

```code
>>> terraform plan
>>> terraform apply
```

Once started, the EC2 instance will execute the `config_docker.sh` file and run the `PREFECT Agent` container which will in turn pull and run the `PREFECT Flows` container whenever requested through the PREFECT Cloud interface (or via command lines).

At this point you can use instructions from 4.1 to test the deployement.

### 5.4 - Destroy the AWS infrastructure
To shut down the deployment, one can use the following command (from inside the terraform folder):

```code
>>> terraform destroy
```
