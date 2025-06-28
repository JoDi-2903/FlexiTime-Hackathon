# Building and Running the Docker Container

## Build Docker Image
```bash
sudo docker build -t call-agent .
```

## Start Container
```bash
sudo docker run -d --name call-agent-container call-agent
```
This command runs the container in detached mode (-d).

## Check Container Status
```bash
sudo docker ps
```
This command lists all running containers with their details.

## Stop Container
```bash
sudo docker stop call-agent-container
```
This command stops the running container gracefully.

## Remove Container
```bash
sudo docker rm call-agent-container
```
This command removes the stopped container. You must stop a container before removing it.
