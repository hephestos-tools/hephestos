## About
hephestos is a suite of tools/apps created in Django for Shopify ecosystem.
#### Current apps
CrossSell(External): Lets a merchant define workflow for marketing product B if they sold product A
<br>Core(Internal): Engine for executing workflows
<br>Shopify(Internal): App for logic pertaining to Shopify APIs and data

## hephestos dev setup MacOS
We are using docker to manage setup.
(TODO: Add setup commands for Windows OS)

### Clone Project
#### SSH remote repository
```sh
git clone git@github.com:hephestos-tools/hephestos.git
cd hephestos
```

#### Install Docker (ignore if already installed)
https://docs.docker.com/desktop/install/mac-install/

### Build the app
This command will pull official image of postgres:16 and build a new image of hephestos. Install python and project dependencies.
```commandline
docker-compose build
```

### Run the app
This step will:
1. Startup the postgres db image
2. Run db migrations (if any migration files are added in the project)
3. Start google pub-sub subscriber
4. Start the webserver on [0.0.0.0:8000]() 
```commandline
docker-compose up
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

### Test if app started up okay
In your browser open http://127.0.0.1:8000/cross-sell/ and you should see something like this if your setup is successful:
![img.png](img.png)


### Access DB image
This command will open the Postgres DB server using bash where you can run psql commands
```commandline
docker exec -it hephestos-db-1 bash
```
PSQL Command to access DB<br/>

- Logs in using default postgres user
```commandline
psql -U postgres -d hephestos
```

#### Some common psql commands
- Run these after logging into psql command line
```psql
\dt  -- List all tables in the current database
\d table_name  -- Describe table structure
\x -- for expanded output format when data is wide
```
- To do manual transactions for testing.
```sql
BEGIN;  -- Start a transaction
UPDATE users SET email = 'new@example.com' WHERE name = 'Alice';
ROLLBACK;  -- Undo the transaction
COMMIT;  -- Save the transaction
```

### Creating and Running DB migrations using Django
Your project should be running.
<br/>**Note**: Always specify which app you are running the migration for
1. If you need to add/edit/drop a column in one of the tables, 
then you just need to edit the corresponding model defined in e.g. `<app>/models.py`, then run:<br/>
    ```
    docker exec -it hephestos-web-1 python manage.py makemigrations <app>
    ```
    This will create a new file under `<app>/migrations` directory<br/><br/>
2. Manually run the migration command
    ```
   docker exec -it hephestos-web-1 python manage.py migrate <app>
   ```
3. or, restart your server - this will run any new migrations, check logs for any failures, if you find any bugs, you can delete the migration file created in Step 1 and regenerate a new one.
    ```commandline
    docker compose restart
    ```



### Setting Up Google Cloud Credentials

1. Create a new service account in Google Cloud Console:
   - Go to IAM & Admin > Service Accounts
   - Create new service account with minimal required permissions
   - Generate and download JSON key

2. Set up credentials:
   ```bash
   # Create secrets directory
   mkdir -p config/secrets
   
   # Copy your credentials file
   cp /path/to/your/credentials.json config/secrets/
   
   # Verify permissions
   chmod 600 config/secrets/credentials.json
   ```

3. Update environment:
   - Copy `.env.example` to `.env`
   - Update credential paths in `.env` if needed

4. For Docker:
   - The credentials will be automatically mounted as a secret
   - No additional configuration needed

### Generating Secure Secrets

1. Django Secret Key:
   ```bash
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

2. Shopify Shared Secret:
   - Generate in Shopify Admin > Apps > Your App > App Settings
   - Copy to .env file

3. Google Cloud Credentials:
   - Follow the steps in "Setting Up Google Cloud Credentials" section
   - Ensure minimal required permissions

### Environment Setup

1. Copy example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update .env with your secrets:
   - Replace placeholder values with actual secrets
   - Never commit .env to version control
   - Keep a backup of your secrets in a secure location

## Debugging Unit Tests with Cursor (Docker Attach)

When running the application stack via Docker Compose, you can debug the Django unit tests running inside the `web` container using Cursor's debugging features by attaching to the test process.

**Prerequisites:**

1.  **`debugpy` Installation:** Ensure `debugpy` is listed in your `requirements.txt` and installed in your `web` container image (rebuild the image if you just added it: `docker compose build web`).
2.  **Port Exposure:** Make sure port `5678` (the default debug port) is mapped in the `web` service definition within your `docker-compose.yml`:
    ```yaml
    services:
      web:
        # ... other settings
        ports:
          - "8000:8000" # Example existing port
          - "5678:5678" # Debug port mapping
    ```
    Restart your containers if you added this mapping: `docker compose up -d --force-recreate`.
3.  **Launch Configuration:** You need an "attach" configuration in your `.vscode/launch.json`. Create or open the file and add an entry like this:
    ```json
    // .vscode/launch.json
    {
        "version": "0.2.0",
        "configurations": [
            // ... other configurations ...
            {
                "name": "Attach to Django Tests (Docker)",
                "type": "debugpy",
                "request": "attach",
                "connect": {
                    "host": "localhost", // Connect to the port exposed on your host
                    "port": 5678        // The debug port
                },
                "pathMappings": [
                    {
                        "localRoot": "${workspaceFolder}", // Your project folder locally
                        "remoteRoot": "/app"              // IMPORTANT: Change to the workdir in your container (e.g., /app, /code)
                    }
                ],
                "django": true,
                "justMyCode": true
            }
        ]
    }
    ```
    *   **Critical:** Replace `/app` in `remoteRoot` with the correct path where your code exists *inside* the `web` container (check your `Dockerfile`'s `WORKDIR` or `COPY` commands).

**Debugging Steps:**

1.  **Set Breakpoints:** Open the test file (e.g., `cross_sell/tests.py`) or the application code file in Cursor and click in the gutter to the left of the line number to set breakpoints (red dots).
2.  **Run Test Command:** Open a terminal (you can use Cursor's integrated terminal: `Terminal` > `New Terminal`) and run the `manage.py test` command within the `web` container, telling `debugpy` to listen for a connection:
    ```bash
    docker compose exec web python -m debugpy --listen 0.0.0.0:5678 --wait-for-client manage.py test <test_target>
    ```
    *   Replace `<test_target>` with the specific test(s) you want to debug:
        *   `cross_sell` (whole app)
        *   `cross_sell.tests` (specific module)
        *   `cross_sell.tests.ClassName` (specific class)
        *   `cross_sell.tests.ClassName.test_method_name` (specific test method)
    *   Your terminal will pause and display `Waiting for debugger attach...`.
3.  **Start Debugger:** Go to the "Run and Debug" view in Cursor (icon on the left sidebar).
4.  **Select Configuration:** Choose the "Attach to Django Tests (Docker)" configuration from the dropdown menu at the top.
5.  **Attach:** Click the green "Start Debugging" play button (or press F5).
6.  **Debug:** The debugger should attach, the "Waiting..." message in the terminal will disappear, and the test execution will begin. Execution will pause at the first breakpoint encountered. Use the debug controls (step over, step into, continue, etc.) to inspect variables and control flow.

