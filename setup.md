## hephestos dev setup MacOS
We are using docker to manage setup.

### Clone Project
#### SSH remote repository
```sh
git clone git@github.com:hephestos-tools/hephestos.git
cd hephestos
```

#### Install Docker
https://docs.docker.com/desktop/install/mac-install/

### Build the app
This command will pull official image of postgres:16 and build a new image of hephestos. Install python and project dependencies.
```commandline
docker-compose build
```

### Run the app
This step will:
1. Run the db image 
2. Run db migrations from web app
3. Start google pub-sub subsriber
4. Start the webserver on [0.0.0.0:8000]()
```commandline
docker-compose up [-d]
```
Use `-d` flag when you want to access the terminal and let docker run in background. <br/><br/>
**To stop the server run** `docker-compose down`

##### Check running docker processes
```commandline
docker ps
```
Image Names:<br/>
`hephestos-db-1` (Database)<br/>
`hephestos-web-1`(Web App)
##### Check image logs
```commandline
docker logs <image-name>
```

### Access DB image
This command will open the DB server using bash where you can run psql commands
```commandline
docker exec -it hephestos-db-1 bash
```
PSQL Command to access DB
```commandline
psql -U postgres -d hephestos
```

### Test app
In your browser open http://127.0.0.1:8000/cross-sell/ and you should see something like this if your setup is successful:
![img.png](img.png)
