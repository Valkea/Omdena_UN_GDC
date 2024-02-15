# Omdena_UN_GDC

This Git repository purposely have folder for the various steps of the project (so we can more easily explore them individually). Hence some steps might reuse content from previous steps... The final step contains all the pieces tied up together.

## lab/01_scrapping

In this folder we can find the PREFECT pipeline with the various pre-processing scripts/flows.

Start by using the `Makefile` to configure/register the PREFECT pipeline in the cloud.
```code
>>> make setup
>>> make start_agent
```

Then the PREFECT pipeline can by run directly using the PREFECT Cloud interface or one of the following commands:

```code
>>> python flows/etl_main.py -m 1
```

```code
>>> prefect deployment run etl-main-flow/etl_eco2mix -a
```

One needs to start the Weaviate local server using `docker compose up`.

## lab/02_terraform

In this folder we can find the various Terraform approaches explored. By running the Terraform commands, the AWS infrastructures will be automatically created and started.

From inside the terraform folder use the following commands 
-- `terraform plan` to see what will be changed
-- `terraform apply` to apply the changes
-- `terraform destroy` to destroy the ressources
-- `terraform -help` to get more commands

Once created the EC2 instance will automatically pull and start a demo Docker hosted on https://hub.docker.com/u/valkea. In the final step, this will pull a Docker image containing the PREFECT pipeline.

## lab/03_inference

In this folder we can find a very simple demo on how to make retrieval from the Weaviate DB filled in step 01. One needs to start the Weaviate local server using `docker compose up`. This simple demo is intented to help the `inference team` start working on the Inference pipeline, nothing more.

## lab/04_prefect_dockers_agent_flows

In this folder we can find the files needed to prepare the 2 PREFECT Dockers.

On one side, we can build a container that will run the PREFECT Flows (in this case a very small script collecting some infos from a Github repo, so we can easily experiment and witness our deployement)

```code
>>> docker build -t ungdc_prefect_flows . -f Dockerfile.flows
>>> docker tag ungdc_prefect_flows:latest valkea/ungdc_prefect_flows:latest
>>> docker push valkea/ungdc_prefect_flows:latest
```

Then on the other side, we can build a container that will run the PREFECT Agent (which in turn will pull and run the Docker.flows whenver needed). This is the Docker we will need to deploy on out EC2 (so this is the Docker that will be automatically pulled when populating the infrastructures with Terraform).

```code
>>> docker build -t ungdc_prefect_agent . -f Dockerfile.agent
>>> docker tag ungdc_prefect_agent:latest valkea/ungdc_prefect_agent:latest
>>> docker push valkea/ungdc_prefect_flows:latest
```

> Note: strangely enough, the current version doesn't automatically refresh the Docker.flows even if we update it on the docker-hub... so to enforce the update, we need to run a `make setup`. This needs to be fixed.
