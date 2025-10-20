# MongoDB Setup Guide for Zendesk AI Integration

This guide provides detailed information about the MongoDB setup options for the Zendesk AI Integration application.

## MongoDB Setup Options

The Zendesk AI Integration now supports multiple MongoDB setup options:

1. **Docker-based MongoDB** (Recommended)
2. **Native MongoDB Installation**
3. **MongoDB Atlas (Cloud)**
4. **Existing MongoDB Instance**

## Option 1: Docker-based MongoDB (Recommended)

### Prerequisites
- Docker installed and running
- Docker Compose installed (included with Docker Desktop on Windows and macOS)

### How It Works
When you choose the Docker option during installation, the system will:

1. Create a `mongodb` directory in your project folder
2. Generate a `docker-compose.yml` file with MongoDB configuration
3. Create initialization scripts for authentication setup
4. Start the MongoDB container
5. Configure your application to connect to this MongoDB instance

### Management
The installation also creates OS-specific management scripts:

**Windows:** `mongodb.bat`
```
mongodb.bat start    - Start the MongoDB container
mongodb.bat stop     - Stop the MongoDB container
mongodb.bat restart  - Restart the MongoDB container
mongodb.bat status   - Check the MongoDB container status
```

**macOS/Linux:** `mongodb.sh`
```
./mongodb.sh start    - Start the MongoDB container
./mongodb.sh stop     - Stop the MongoDB container
./mongodb.sh restart  - Restart the MongoDB container
./mongodb.sh status   - Check the MongoDB container status
```

### Data Persistence
The Docker setup uses a named volume (`mongodb_data`) to ensure your data persists even when the container is stopped or removed.

## Option 2: Native MongoDB Installation

This option installs MongoDB directly on your host system.

### Windows Installation
1. The script downloads the MongoDB MSI installer
2. Installs MongoDB as a Windows service
3. Creates necessary directories and configuration
4. Starts the MongoDB service

### macOS Installation
1. Uses Homebrew to install MongoDB
2. Sets up the MongoDB service
3. Starts the service

### Linux Installation
1. Adds MongoDB repository based on your distribution
2. Installs MongoDB packages
3. Starts and enables the MongoDB service

## Option 3: MongoDB Atlas (Cloud)

MongoDB Atlas is a fully-managed cloud database service provided by MongoDB.

### Setup Process
1. Create a MongoDB Atlas account
2. Create a free tier cluster
3. Set up database access (username and password)
4. Configure network access (IP whitelist)
5. Get your connection string

### Advantages
- No local installation required
- Available from anywhere
- Managed backups and scaling
- Free tier available for development

## Option 4: Existing MongoDB Installation

If you already have MongoDB installed, you can use your existing installation.

### Configuration Options
- Use default connection (localhost:27017)
- Specify custom connection string
- Configure authentication if needed

## Standalone MongoDB Configuration

You can reconfigure MongoDB at any time using the standalone configuration script:

```
python configure_mongodb.py
```

This script will:
1. Present all MongoDB setup options
2. Guide you through the selected setup process
3. Update your `.env` file with the new configuration
4. Verify the MongoDB connection

## Troubleshooting

### Docker Issues
- Ensure Docker is running
- Check container status with `docker ps` or the provided scripts
- View logs with `docker logs zendesk_ai_mongodb`

### Native Installation Issues
- Check if MongoDB service is running on your system
- Verify MongoDB logs for errors
- Ensure you have proper permissions

### MongoDB Atlas Issues
- Verify your IP is allowed in Network Access settings
- Confirm database user credentials
- Test connection string directly

### Connection String Format
- Local without authentication: `mongodb://localhost:27017/<database_name>`
- Local with authentication: `mongodb://<username>:<password>@localhost:27017/<database_name>?authSource=admin`
- Atlas: `mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database_name>?retryWrites=true&w=majority`

**Note:** Replace `<username>`, `<password>`, `<cluster>`, and `<database_name>` with your actual values.

## Advanced Configuration

For advanced MongoDB configuration:

- **Docker**: Edit the `mongodb/docker-compose.yml` file
- **Native**: Edit your MongoDB configuration file
  - Windows: `C:\Program Files\MongoDB\Server\X.Y\bin\mongod.cfg`
  - macOS/Linux: `/etc/mongod.conf`
- **Atlas**: Use the MongoDB Atlas dashboard

## Data Migration

To migrate data between MongoDB setups:

1. Export data from your source MongoDB:
   ```
   mongodump --uri="your_connection_string" --out=backup
   ```

2. Import data to your destination MongoDB:
   ```
   mongorestore --uri="your_new_connection_string" backup
   ```

For more information, refer to the [MongoDB documentation](https://docs.mongodb.com/).
