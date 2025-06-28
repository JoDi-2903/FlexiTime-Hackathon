# Building and Running the Docker Container

## Build Docker Image
```bash
sudo docker build -t frontend .
```

## Start Container
```bash
sudo docker run -d -p 443:80 --name frontend-container frontend
```
This command runs the container in detached mode (-d) and maps port 443 of the host to port 80 of the container.

## Check Container Status
```bash
sudo docker ps
```
This command lists all running containers with their details.

## Stop Container
```bash
sudo docker stop frontend-container
```
This command stops the running container gracefully.

## Remove Container
```bash
sudo docker rm frontend-container
```
This command removes the stopped container. You must stop a container before removing it.
