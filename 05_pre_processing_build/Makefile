
PROJECT_ID = "omdena-un-gdc"

setup_prefect_blocks:
	@echo "Initialize prefect blocks"
	python setup_prefect.py ${PROJECT_ID}

setup_prefect_deployment:
	@echo "Initialize prefect deployment"
	prefect deployment build flows/etl_main.py:omdena_ungdc_etl_main_flow --name omdena_un_gdc_docker  -sb s3-bucket/omdena-un-gdc-bucket/docker -ib docker-container/omdena-un-gdc-docker -o omdena_ungdc_etl_main_flow-docker_deployment.yaml --cron "0 0 * * *" -a
	
start_agent:
	@echo "Start prefect agent"
	prefect agent start --work-queue "default"

setup: setup_prefect_blocks setup_prefect_deployment
