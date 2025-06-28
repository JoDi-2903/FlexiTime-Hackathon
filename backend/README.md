# Building and Running the Docker Container

## Build Docker Image
```bash
sudo docker build -t medical-api .
```

## Start Container
```bash
sudo docker run -d -p 80:5000 --name medical-api-container medical-api
```
This command runs the container in detached mode (-d) and maps port 80 of the host to port 5000 of the container.

## Check Container Status
```bash
sudo docker ps
```
This command lists all running containers with their details.
