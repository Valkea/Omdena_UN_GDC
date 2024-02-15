Unzip your weaviate_data_*.zip in this folder.

The structure should be the following:
- docker-compose.yaml
- data/weaviate_data

If you want to change the path, you need to edit the docker-compose.yaml


If you need to delete the data/weaviate_data folder:
>>> sudo chown -R valkea data/weaviate_data 

To start the weaviate docker use:
>>> docker compose up
You need to check that the server doesn't output a message regarding the available space, otherwise the weaviate server will be write only
