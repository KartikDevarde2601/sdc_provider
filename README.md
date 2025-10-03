# SDC Medical Device Monitor

A scalable, production-ready medical device monitoring application built with Python, implementing the SDC (Service-Oriented Device Connectivity) standard with a modern web-based GUI.

## 🏗️ Architecture

This application follows **MVC (Model-View-Controller)** pattern with additional **Service Layer** for better separation of concerns and scalability.

### Architecture Layers

```
┌─────────────────────────────────────────┐
│            Views (NiceGUI)              │  ← User Interface
├─────────────────────────────────────────┤
│           Controllers                    │  ← Business Logic
├─────────────────────────────────────────┤
│            Services                      │  ← SDC Operations
├─────────────────────────────────────────┤
│             Models                       │  ← Data Structures
└─────────────────────────────────────────┘
```

### Key Design Patterns

- **MVC Pattern**: Separates UI, logic, and data
- **Service Layer**: Encapsulates SDC-specific operations
- **Observer Pattern**: Real-time metric updates via callbacks
- **Dependency Injection**: Controllers receive services
- **Repository Pattern**: MDIB data management

## 📁 Project Structure

```
sdc_monitor/
├── main.py                    # Application entry point
├── config/
│   └── settings.py           # Centralized configuration
├── models/
│   ├── device.py             # Device & MetricData models
│   └── mdib_manager.py       # MDIB state management
├── services/
│   ├── discovery_service.py  # WS-Discovery implementation
│   ├── connection_service.py # SDC connection management
│   └── metric_service.py     # Metric processing & history
├── controllers/
│   ├── discovery_controller.py  # Device search logic
│   └── device_controller.py     # Device connection logic
├── views/
│   ├── main_view.py          # Device discovery screen
│   ├── device_view.py        # Monitoring screen
│   └── components/
│       ├── vital_display.py  # Vital signs component
│       └── metric_chart.py   # Real-time chart component
└── requirements.txt
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Network access to SDC medical devices
- Basic understanding of the SDC standard

### Installation

1. **Clone or create the project structure**

```bash
mkdir sdc_monitor
cd sdc_monitor
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure settings**

Edit `config/settings.py` to match your network:

```python
DISCOVERY_ADDRESS = "10.19.107.255"  # Your broadcast address
BASE_UUID = uuid.UUID('{cc013678-79f6-403c-998f-3cc0cc050230}')
```

### Running the Application

```bash
python main.py
```

The application will start on `http://localhost:8080`

## 📖 Usage Guide

### 1. Discovering Devices

- Click the **"Search Network"** button
- Wait for discovery to complete (default 10 seconds)
- Discovered devices appear as cards with:
  - Device name and EPR
  - IP address (if available)
  - Connection status
  - Connect button

### 2. Connecting to a Device

- Click **"Connect"** on any discovered device
- Wait for connection establishment
- Automatically redirects to monitoring screen

### 3. Monitoring Vitals

The monitoring screen shows:
- **Left Panel**: Current vital signs (large numbers)
  - Heart Rate (HR)
  - Blood Oxygen (SpO₂)
  - Temperature
  
- **Right Panel**: Real-time trend charts
  - Scrolling line graphs
  - Last 50 data points
  - Auto-updating every second

### 4. Disconnecting

- Click the **back arrow** button
- Returns to device discovery screen
- Device connection is automatically closed

## 🔧 Configuration

### Network Settings

```python
# config/settings.py
DISCOVERY_ADDRESS = "10.19.107.255"  # Broadcast address
DISCOVERY_TIMEOUT = 10  # Discovery timeout in seconds
```

### Display Settings

```python
CHART_MAX_POINTS = 100  # Maximum points in charts
UPDATE_INTERVAL = 1.0   # Update frequency (seconds)
```

### Customizing Metrics

Add new metrics in `config/settings.py`:

```python
METRIC_NAMES = {
    'metric.hr': 'Heart Rate',
    'metric.spo2': 'SpO₂',
    'metric.temp': 'Temperature',
    'metric.nibp.sys': 'Blood Pressure (Systolic)',  # New metric
}

CHART_COLORS = {
    'hr': '#ef4444',
    'spo2': '#3b82f6',
    'temp': '#10b981',
    'nibp.sys': '#f59e0b',  # New color
}
```

## 🎯 Extending the Application

### Adding a New Metric Display

1. **Update the model** (if needed in `models/metric.py`)

2. **Add to settings**:
```python
# config/settings.py
METRIC_NAMES['metric.resp'] = 'Respiration Rate'
```

3. **Add to device view**:
```python
# views/device_view.py
self.vital_displays['metric.resp'] = VitalDisplay(
    name='Respiration Rate',
    unit='rpm',
    icon='