# Indoor/Outdoor Weather Monitor with Cloud Dashboard

![Weather Monitor Banner](https://via.placeholder.com/800x200?text=Weather+Monitor+System)

## 📋 Project Overview

This project implements a comprehensive indoor/outdoor weather monitoring system using M5stack IoT devices with environmental sensors, integrated with Google Cloud Platform and OpenWeatherMap API. The system captures, analyzes, and visualizes both indoor measurements (temperature, humidity, air quality) and outdoor weather data in real-time.

### Key Features:

- **Dual Interface System**: M5stack on-device dashboard and cloud-based Streamlit web interface
- **Indoor Environmental Monitoring**: Temperature, humidity, and air quality tracking
- **Outdoor Weather Integration**: Real-time weather data and forecasts via OpenWeatherMap API
- **Cloud Storage**: Historical data storage using Google BigQuery
- **Smart Notifications**: Motion-activated voice alerts for weather conditions and warnings
- **Data Visualization**: Historical data trends and analysis on both interfaces

## 🛠️ Technology Stack

- **Hardware**: M5stack Core2, ENVIII sensor, Air Quality sensor, Motion sensor
- **Cloud Platform**: Google Cloud Platform (BigQuery, Text-to-Speech)
- **External Data**: OpenWeatherMap API
- **Frontend**: Streamlit dashboard
- **Backend**: Python Flask middleware
- **IoT Programming**: MicroPython for M5stack

## 📁 Repository Structure

- `/streamlit`: Cloud-based web dashboard implementation
  - `frontend.py`: Streamlit application code
  - `Dockerfile`: Container configuration for Streamlit app
  - `requirements.txt`: Python dependencies for the dashboard

- `/web_app`: Backend services and M5stack code
  - `main.py`: Core application logic and API endpoints
  - `m5stack_code.py`: Code deployed to the M5stack device
  - `walkthrough.py`: Implementation helper functions
  - `WalkThrough.ipynb`: Jupyter notebook with comprehensive implementation guide
  - `Dockerfile`: Container configuration for backend services
  - `requirements.txt`: Python dependencies for the backend
  - `test.py`: Testing utilities

## 🚀 Installation & Setup

### Prerequisites

1. Google Cloud Platform account with BigQuery and Text-to-Speech API enabled
2. OpenWeatherMap API key
3. Python 3.7+
4. M5stack Core2 with ENVIII, Air Quality and Motion sensors
5. Docker (optional, for containerized deployment)

### Cloud Service Setup

1. Create a BigQuery dataset and tables for your weather data
2. Set up a Google Cloud project and enable required APIs
3. Create service account credentials

### Configuration

1. Clone this repository:
   ```
   git clone https://github.com/AndreaMonnerat14/CAA-IoT_Project.git
   cd CAA-IoT_Project
   ```

2. Install backend dependencies:
   ```
   cd web_app
   pip install -r requirements.txt
   ```

3. Install Streamlit dashboard dependencies:
   ```
   cd ../streamlit
   pip install -r requirements.txt
   ```

4. Configure environment variables (create a `.env` file with the following):
   ```
   # Google Cloud credentials
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
   BIGQUERY_DATASET=your_dataset_name
   BIGQUERY_TABLE=your_table_name
   
   # OpenWeatherMap API
   OPENWEATHERMAP_API_KEY=your_api_key
   DEFAULT_LOCATION=your_default_city
   
   # Other configurations
   TTS_ENABLED=true
   ```

### M5stack Setup

1. Flash the M5stack device with the MicroPython firmware
2. Upload the `m5stack_code.py` to your device
3. Configure WiFi credentials in the device interface

## 🖥️ Running the Application

### Running the Backend Service

```
cd web_app
python main.py
```

### Running the Streamlit Dashboard

```
cd streamlit
streamlit run frontend.py
```

### Docker Deployment (Optional)

```
# Build and run backend
cd web_app
docker build -t weather-monitor-backend .
docker run -p 5000:5000 weather-monitor-backend

# Build and run frontend
cd streamlit
docker build -t weather-monitor-dashboard .
docker run -p 8501:8501 weather-monitor-dashboard
```

## 📊 Dashboard Features

The Streamlit dashboard provides:
- Current indoor and outdoor weather conditions
- Historical temperature and humidity trends
- Air quality analysis over time
- Weather forecast visualization
- Data export capabilities

## 🎮 M5stack Interface

The on-device interface displays:
- Current time and date (NTP synchronized)
- Indoor temperature and humidity
- Indoor air quality index
- Outdoor temperature and conditions
- Weather forecast for upcoming days
- WiFi configuration options

## 📈 Project Architecture

```
┌─────────────┐      ┌───────────────┐     ┌───────────────┐
│  M5stack    │      │  Cloud        │     │  User         │
│  Device     │      │  Services     │     │  Interfaces   │
├─────────────┤      ├───────────────┤     ├───────────────┤
│ Temperature │      │               │     │               │
│ Humidity    │◄────►│  BigQuery     │◄───►│  Streamlit    │
│ Air Quality │      │  Storage      │     │  Dashboard    │
│ Motion      │      │               │     │               │
└─────────────┘      └───────────────┘     └───────────────┘
       ▲                     ▲                     ▲
       │                     │                     │
       └─────────────────────▼─────────────────────┘
                  ┌───────────────────┐
                  │  External APIs    │
                  ├───────────────────┤
                  │  OpenWeatherMap   │
                  │  Google TTS       │
                  └───────────────────┘
```

## 👥 Contributors

- [Andrea Monnerat](https://github.com/AndreaMonnerat14) - Backend, BigQuery integration, M5stack programming, README
- [Tanguy Schwitzguébel] - Streamlit dashboard, frontend design, data visualization, M5stack testing and dashboard

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎬 Demo Video
