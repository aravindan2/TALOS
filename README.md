## Framework Overview
This framework provides an integrated solution for data ingestion, processing, and analytics through a suite of containerized components orchestrated via Docker.

## Core Components

### Minio
- **Type**: Object Storage
- **Description**: Self-hosted alternative to AWS S3 with similar capabilities
- **Features**:
  - Scalable cloud-native storage
  - Data versioning and lifecycle management
  - Access control and encryption

### Kafka
- **Type**: Distributed Event Streaming Platform
- **Functionality**:
  - Acts as a high-throughput message queue
  - Producers serialize data to brokers
  - Consumers deserialize and process streams
- **Scalability**:
  - Supports multiple brokers for load distribution
  - Horizontal scaling capabilities

### Spark
- **Type**: Batch Processing Engine
- **Primary Use**: ETL (Extract, Transform, Load) workloads
- **Capabilities**:
  - Distributed computing framework
  - Large-scale data processing
  - Integration with multiple data sources

### MLflow
- **Type**: Machine Learning Lifecycle Platform
- **Features**:
  - Experiment tracking
  - Model versioning
  - Model registry
- **Deployment**: Hosted locally within the framework

### Streamlit
- **Type**: Analytics Frontend
- **Advantages**:
  - Rapid dashboard development
  - Interactive data visualization
  - Python-native development

## System Architecture

### Container Orchestration
- **Docker Compose**:
  - Manages multi-container deployments
  - Single-command startup/shutdown
  - Network configuration:
    - Default shared network
    - Optional custom networks for isolation
  - Startup command specification

# Steps to Follow 

## Step 1
Clone the repository and then navigate to the repository , and execute the command 
- [Docker compose up -d]
This will start the containers 

## Step 2
Open docker desktop , here u should be able to see all the containers 
here click on the ports for mlflow dash board and precfect dashboard 
-  MLflow: [http://localhost:5000](http://localhost:5000/)
    
- Prefect: [http://localhost:4200](http://localhost:4200/)

- Streamlit: [http://localhost:8501/](http://localhost:8501)

## Step 3
open the spark  container exec in docker desktop , here change the directory to shared 
- cd shared
Here run 
- pip install seaborn
- pip install minio
Then we run the python python file 
- spark-submit ecg.py or python ecg.py 
you will be able to see the progress in the prefect dashboard ( Runs ) [http://localhost:4200/]

## Step 4 
- Check the streamLit  dashboard at [Streamlit] [[http://localhost:8501/]]
Open the Dashboard container in Docker desktop 
- run "[Pip install seaborn plotly]"
- restart the container 
## Step 5 
open the dashboard code , dashboard,py , change the run_id of the models for xgboost and snapshot ensemble , you can find this at mlflow [http://localhost:5000/] , navigate to FinalXGB_vs_SnapshotEnsemble_CV. 

-  Fine the runid , after clicking the Run Name ( Final_Snapshot_Ensemble_Eval and Final_XGBoost_Eval )

Now all the framwork has been setup , resolving most issues , all that is left is to send data to kafka 

Navigate to the terminal where the repository was cloned , here open the producer.py python code , check the name of the CSV_PATH is should be "test_dataset.csv"

in the terminal run python producer.py 
- you might have a few errors , these are package related , 
	- These will fix any possible issues with this file [pip install kafka-python pandas ]



