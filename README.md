# 👥 Contributors

- [Andrea Monnerat](https://github.com/AndreaMonnerat14) - Backend structure, BigQuery integration, M5stack programming, README, Streamlit Dashboard enhancement, OpenAI API Integration
- [Tanguy Schwitzguébel](https://github.com/Yeucht) - Backend, Streamlit dashboard, Text to speech, Data Visualization, M5stack programming, Testing and Optimizing the Backend

## 🎬 Demo Video

- Upcoming in the next few days :/

# Indoor/Outdoor Weather Monitor with Cloud Dashboard
<img width="1679" alt="Capture d’écran 2025-05-19 à 11 01 37 PM" src="https://github.com/user-attachments/assets/9773bbbf-4366-4ca1-9d24-40e53f01d22d" />

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
- **Cloud Platform**: Google Cloud Platform (Cloud Run, BigQuery, Text-to-Speech)
- **External Data**: OpenWeatherMap API, OpenAI API
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
  - `M5Code.py`: Code deployed to the M5stack device
  - `Dockerfile`: Container configuration for backend services
  - `requirements.txt`: Python dependencies for the backend
  - `test.py`: Testing utilities

## 🚀 Installation & Setup

### Prerequisites

1. Google Cloud Platform account with BigQuery and Text-to-Speech API enabled
2. OpenWeatherMap API key
3. OpenAI API key 
4. Python 3.7+
5. M5stack Core2 with ENVIII, Air Quality and Motion sensors
6. Docker (optional, for containerized deployment)

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
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
   OPENWEATHERMAP_API_KEY=your_api_key
   OPENAI_API_KEY=your_api_key
   
   ```

## 🔧 M5Stack Configuration Guide

To connect your **M5Stack** to your computer, burn the firmware (load the code permanently), or modify the code, follow these steps:

### ✅ Initial Setup

Before anything, make sure you have:
1. ENVIII temp/hum sensor (port A)
2. TVOC air quality sensor (port C)
3. PIR movement sensor (port B)

Connected to your device. Then, you can start the following instructions:

1. **Power on the M5Stack.**

2. On boot, it will try to connect to a known Wi-Fi network:
   - ✅ **If it connects** to one you also have access to, skip to step 3.
   - ❌ **If it doesn't connect**, reboot the device and enter the **Settings** menu.
     - Select **"Start"** and follow the on-screen instructions to connect the M5Stack to your own Wi-Fi.
     - ⚠️ **Important:** The M5Stack only supports **2.4 GHz** Wi-Fi networks.

3. Once connected to Wi-Fi:
   - Visit [https://flow.m5stack.com/](https://flow.m5stack.com/)
   - Connect your M5Stack (bottom-left corner of the UI)
   - Open the `</>` **Python** editor
   - Copy and paste the M5Code from this repository into the editor
   - 
![M5](https://github.com/user-attachments/assets/64b9193f-3cc6-4882-95bd-97eb351a3cb2)

---

### 🛠 Configuration

4. To add your Wi-Fi credentials, modify the following section (around lines 23–27):

   ```python
   networks = [
       ('YourSSID', 'yourpassword'),
       ('AnotherSSID', 'anotherpassword'),
       ...
   ]
5. Upload the 5 PNG image files included in the M5 repository

6. In the M5 Web UI, open the file manager (top-left corner)

7. Upload the image files to the device's file system

8. Replace the flask_url variable in the script with your own API endpoint if you're using a local or self-hosted solution.

9. Click "Run" to test that everything is working.

10. If all looks good, click "Download" (bottom-right corner) to burn the script to the M5Stack. Then, on boot, click on "app"

Notes: 
1. If you want to return into dev mode, just reboot and click on UiFlow, then go back on M5Flow Web UI (or redo the whole process with settings if this is not working)
2. Burn doesn't work for now, we'll fix it asap. If you want to burn it still, you can uncomment the 15th line and write your own SSID/credentials

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

<img width="1205" alt="Capture d’écran 2025-05-20 à 5 34 33 PM" src="https://github.com/user-attachments/assets/87fdea54-b937-4b0a-b645-d2d5272cdb7f" />


