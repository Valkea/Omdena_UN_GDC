# Using the Weaviate database for inferencing


You will find in the section below, all the instructions required to run the Weaviate DB on your own computer and make retrieval.
 
## 1. Setting up the Weaviate database

### First, 
you need to install `Docker` to run dockers and docker-compose.

### Secondly,
unzip the weaviate_data_*.zip into the data folder.

The expected structure is the following:
- docker-compose.yaml
- data/weaviate_data

### Thirdly,
let's start the Weaviate local instance. Go to the folder with the `docker-compose.yaml` and run the following command:

```bash
>>> docker compose up -d
```

Note: you can remove the `-d` if you want to see the logs.

## 2. Querying the weaviate database

### First,
let's create a virtual environment and install the required Python libraries.
Open a new terminal in the same folder and run the following:

(Linux or Mac)
```bash
>>> python3 -m venv venvUNGDC
>>> source venvUNGDC/bin/activate
>>> pip install -r requirements.txt
```

(Windows):
```bash
>>> py -m venv v
>>> .\venvUNGDC\Scripts\activate
>>> py -m pip install -r requirements.txt
```

### Secondly,
let's run the inference_demo_py script

```bash
(venvUNGDC) >>> python inference_demo.py query="MY QUERY TEXT"
```

## 3. Cleaning
Once the tests are over, you can stop the Weaviate database docker.

If you used the `-d` (detached mode) argument, use:
```bash
>>> docker compose down
```

And if you ran it without the detached mode, you can stop it with: `CTRL+C`

