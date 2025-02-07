Mini-Amazon
===
This is the final project for duke ECE 568.
   
Docker Configurations: 
---
### 1. UPS and World hostname
To change the hostname of UPS and world, modify the docker-compose.yml file, change the HOST_UPS under server -> build -> args. Docker should pass this argument into the server container, the Dockerfile under ./server/ will make this argument an environment variable, visible from inside the run.sh.<br>
![Untitled](https://user-images.githubusercontent.com/49318361/164995413-2ea68d15-3080-49d1-9389-ab0cc8bebc5d.png)

### 2. Deleting docker containers and images after each run
In order for the database to be consistent, we need to drop the previous database before running docker each time. Run these commands before build:
 <br>
$ sudo docker kill $(sudo docker ps -q) # stop all containers <br>
$ sudo docker rm $(sudo docker ps -a -q) # remove all containers  <br>
$ sudo docker rmi $(sudo docker images -q) # remove all images <br>
$ sudo docker network prune # remove all networks <br>
$ sudo docker volume prune # remove all volumes  <br>
 <br>
 $ sudo docker-compose down <br>
When running without docker, try python3 manage.py flush under the web_app directory.

### 3. sudo docker-compose build before sudo docker-compose up !!!

### 4. Runtime settings
3.1 Initialize product amount: In server -> server.cpp, change the PRODUCT_INITIAL_AMOUNT to be the desired initial amount for every product<br>
3.2 Run without UPS: In server -> server.cpp, change the withUPS value in server constructor to be false, the server will send an AConnect command to world to initialize a world first, and will run without UPS<br>

### 5. Change permission
4.1 Before running docker-compose up --build, run chmod -R +x server/run.sh

### 6. If meet with problem: Failed to bind tcp 0.0.0.0:5432 address already in use
Refer to https://stackoverflow.com/questions/38249434/docker-postgres-failed-to-bind-tcp-0-0-0-05432-address-already-in-use
sudo service postgresql stop

### 7. Modifications in hostnames when running in docker
2.1 In web_app -> mysite -> settings.py, change the 'host' under DATABASES to be 'db'<br>
2.2 In web_app -> mysite -> settings.py, add 'web' to ALLOWED_HOSTS<br>
2.3 In web_app -> amazon -> views.py, in function send_signal, change the HOST to be "server"<br>
![Untitled](https://user-images.githubusercontent.com/49318361/164996218-32bc3728-e6fa-4485-b15f-99719e42814d.png) <br>
2.4 In server -> server.cpp -> Server::connectDB, change the hostname of db to be 'db'

### 8. Environment variables
To run without docker, need to run the following commands <br> LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/{username}/Mini_amazon/server/Poco/lib:/home/{username}/Mini_amazon/server/protobuf/lib
