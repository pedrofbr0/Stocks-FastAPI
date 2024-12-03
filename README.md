# Stocks-FastAPI

A FastAPI application to retrieve stock data, including open/close values, performance, and competitor information, with data persistence in a PostgreSQL database. You can check it at https://stocks-fastapi-api.onrender.com/docs

## Table of Contents
- [Description](#description)
- [Technologies Used](#technologies-used)
- [Features](#features)
- [Requirements](#requirements)
- [Local Setup](#localsetup)
  * [Installation](#installation)
  * [Running the Application](#running-the-application)
  * [Running Tests Locally](#running-tests-locally)
- [Docker Compose Setup](#docker-compose-setup)
  * [Docker Installation](#docker-installation)
  * [Execution with Docker Compose](#execution-with-docker-and-docker-compose)
- [API Endpoints](#api-endpoints)
- [Motivation and Technological Choices](#motivation-and-technological-choices)
- [Next Steps](#next-steps)
- [Contribution](#contribution)
- [License](#license)

## Description

This application allows users to retrieve detailed information about company stocks, including:

- Open and close values for a specific day.
- Performance data across different periods (5 days, 1 month, 3 months, YTD, 1 year).
- Competitor information, including market capitalization.

The data is sourced through integrations with:

- **Polygon.io API**: Provides stock market data.
- **MarketWatch**: Additional information retrieved via web scraping.

The application also enables users to update the amount of purchased stocks, persisting this information in a PostgreSQL database.

## Technologies Used

- **Python 3.10**
- **FastAPI**: Web framework for building APIs.
- **SQLAlchemy**: ORM for database interactions.
- **PostgreSQL**: Relational database.
- **HTTPX**: Asynchronous HTTP client for external API calls.
- **BeautifulSoup4**: For web scraping.
- **Docker & Docker Compose**: For containerization and orchestration.
- **Pytest**: Testing framework.

## Features

- **Stock Data Retrieval**: Get detailed stock information using the company symbol.
- **Stock Quantity Update**: Record and update purchased stock amounts.
- **Integration with External APIs**: Access up-to-date data from reliable sources.
- **Data Caching**: Improves performance with caching.
- **Data Persistence**: Stores information in a PostgreSQL database.

## Requirements

- **Python 3.10** or higher
- **Docker and Docker Compose** (optional for containerized execution)
- **Polygon.io API Key** (required for API calls)

## Local Setup

Follow these steps to set up and run the application locally.
 
### 1. Clone the Repository

```bash
git clone https://github.com/your-username/stocks-fastapi.git
cd stocks-fastapi
```

### 2. Create a Virtual Environment

It's recommended to use a virtual environment to manage dependencies.
```bash
python -m venv .venv
```

### 3. Activate the Virtual Environment
- On Windows:
```bash
.venv\Scripts\activate
```
- On Unix or MacOS:
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Set Up Environment Variables

Create a **.env** file in the project root with the following content:
```dotenv
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=stocks_db
DB_USER=postgres
DB_PASSWORD=your_database_password

# Polygon API
POLYGON_BASE_URL=https://api.polygon.io/v1/open-close
POLYGON_API_KEY=your_polygon_api_key

# MarketWatch
MARKETWATCH_BASE_URL=https://www.marketwatch.com/investing/stock
```
Replace **your_database_password** and **your_polygon_api_key** with appropriate values.

## Running the Application
Ensure PostgreSQL is installed and running on your machine.

## Run the Application
1. Start the FastAPI Server
```bash
uvicorn app.main:app --reload
```
The application will be available at http://localhost:8000.

2. Access the API Documentation
- Access http://localhost:8000/docs for interactive documentation (Swagger UI).

## Running Tests Locally
To run the test suite locally, follow these steps:
1. Ensure the Virtual Environment is Activated
If not already activated, activate your virtual environment.
2. Run the Tests
3. ```bash
   pytest tests/
   ```

## Docker-Compose Setup

### 1. Set Up Environment Variables
Create a **.env.docker** file in the project root with the following content:

```dotenv
# Database
DB_HOST=db
DB_PORT=5432
DB_NAME=stocks_db
DB_USER=postgres
DB_PASSWORD=your_database_password

# Polygon API
POLYGON_BASE_URL=https://api.polygon.io/v1/open-close
POLYGON_API_KEY=your_polygon_api_key

# MarketWatch
MARKETWATCH_BASE_URL=https://www.marketwatch.com/investing/stock
```
Note: **DB_HOST** is set to **db** for Docker Compose.

### 2. Build and Start Containers
```bash
docker compose up --build
```
This will start the **web** and **db** services defined in **docker-compose.yaml** (This command builds the images, if not already built, and starts the containers.)

### 3. Access the Application
The application will be available at http://localhost:8000.

### 4. View Logs
To view logs from the containers:
```bash
docker-compose logs -f
```

## API Endpoints

### 1. Retrieve Stock Data
- GET **/stock/{stock_symbol}**
- Description: Returns detailed stock information for the specified symbol.
- Example: **/stock/AAPL**

### 2. Update Stock Quantity
- POST **/stock/{stock_symbol}**
- Description: Updates the purchased stock quantity.
- Request Body:
```json
{
  "amount": 5.33
}
```

### 3. Retrieve Open/Close Data
GET **/stock/open_close/{stock_symbol}/{date}**
- Description: Returns open/close values for the specified stock on a given date.
- Example: **/stock/open_close/AAPL/2023-01-01**

## 4. Retrieve MarketWatch Data
GET **/stock/marketwatch/{stock_symbol}**
- Description: Returns additional stock data via web scraping from MarketWatch.
- Example: **/stock/marketwatch/AAPL**

## Motivation and Technological Choices
- FastAPI: Chosen for its efficiency, asynchronous support, and automatic documentation generation.
- SQLAlchemy: Provides a robust and flexible object-relational mapping.
- HTTPX: Asynchronous HTTP client simplifies external API calls.
- BeautifulSoup4: Powerful library for web scraping.
- Docker & Docker Compose: Simplifies deployment and ensures environment consistency.
- Pytest: Testing framework for writing simple and efficient tests.

## Next Steps
## Data Persistence of stock model (with SQLAlchemy) and database migration with Alembic.

## Contribution
Contributions are welcome! Feel free to open issues and pull requests.

## License
This project is licensed under the MIT License.
