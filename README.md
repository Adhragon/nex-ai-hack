# School AirSafe

**Smarter, healthier journeys through air-quality-aware planning.**

School AirSafe is an air-quality awareness and trip-planning platform designed to help users make informed decisions about outdoor activities and travel. It combines air-quality information with scheduling tools to help users identify suitable times for planned activities.

## Features

- **Air Quality Awareness:** View air-quality information to understand environmental conditions at your destination.
- **Trip Scheduler:** Plan trips by selecting start and end dates.
- **Daily AQI Planning:** Review air-quality information for individual days of a multi-day trip.
- **Preferred Time Windows:** Specify preferred start and end times instead of automatically selecting the earliest available period.
- **Activity Planning:** Select a specific trip day and configure the activity duration.
- **Time-Aware Scheduling:** Identify appropriate activity windows based on available air-quality information and scheduling preferences.
- **Interactive Web Interface:** Use a React-based frontend connected to a Python backend.

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | React |
| Build Tool | Vite |
| Backend | Python, FastAPI |
| Languages | JavaScript, JSX, Python |
| Development Tools | Git, GitHub, VS Code |

## Project Structure

```text
nex-ai-hack/
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── App.css
├── backend/
│   └── backend.py
├── README.md
└── ...
```

Note: This is an illustrative structure. Adjust the paths to match the actual repository.

## Getting Started

### Prerequisites

- Node.js and npm
- Python 3.10 or later
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Adhragon/nex-ai-hack.git
cd nex-ai-hack
```

### 2. Set Up the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the local URL provided by Vite, usually `http://localhost:5173`.

### 3. Set Up the Backend

Open a separate terminal from the project root.

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the required dependencies:

```bash
pip install fastapi uvicorn
```

Install any additional dependencies specified in the project's requirements file.

Start the backend using the module path and application variable defined in your code. For example, if the FastAPI application is named `app` in `backend/backend.py`:

```bash
uvicorn backend.backend:app --reload
```

The backend URL and port depend on the project's configuration.

## How It Works

1. **Choose Trip Dates:** Select the beginning and end dates of your trip.
2. **Review Daily Conditions:** Examine air-quality information for each day.
3. **Select an Activity Day:** Choose the specific day you want to plan.
4. **Set Activity Duration:** Specify how long the activity should last.
5. **Choose a Preferred Time Window:** Set the earliest and latest times that fit your schedule.
6. **Review the Schedule:** Use available air-quality information and your preferences to identify an appropriate activity window.

## Project Objective

School AirSafe aims to make air-quality information more actionable by connecting environmental awareness with everyday scheduling. It helps users consider not only where and when to travel, but also the air quality expected during their planned activities.

## Potential Applications

- Planning school outings and educational trips
- Scheduling outdoor sports and recreational activities
- Organizing multi-day travel itineraries
- Considering air quality when choosing outdoor activity times

## Disclaimer

Air-quality measurements and forecasts can change throughout the day. School AirSafe is intended as a planning and awareness aid, not as a substitute for official health guidance or local air-quality advisories. Users should follow applicable public-health recommendations, particularly during periods of poor air quality.

## Contributing

Contributions, bug reports, and feature suggestions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Open a pull request describing the changes.

## License

Refer to the repository's existing license for the applicable terms. Do not change or replace the license without authorization.


Problem statement and solution overview • Architecture diagram and technology stack • Setup and execution instructions ;   • Deployment URL or approved local-demo details • Dataset attribution and licence • Team member details • Link to DEV_LOG.md, if maintained 
