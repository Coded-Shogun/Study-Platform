# CompTIA Cloud+ Study Platform - Detailed Setup Guide

This guide provides step-by-step instructions for setting up the CompTIA Cloud+ Study Platform on your local machine.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Frontend Setup](#frontend-setup)
4. [Backend Setup](#backend-setup)
5. [Docker Setup](#docker-setup)
6. [Running the Application](#running-the-application)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

#### 1. Node.js and npm
- **Version:** Node.js 18.x or higher
- **Download:** https://nodejs.org/
- **Verify installation:**
  ```bash
  node --version  # Should show v18.x or higher
  npm --version   # Should show 9.x or higher
  ```

#### 2. Python
- **Version:** Python 3.11 or higher
- **Download:** https://www.python.org/downloads/
- **Verify installation:**
  ```bash
  python --version  # or python3 --version
  pip --version     # or pip3 --version
  ```

#### 3. Docker (Optional, for labs)
- **Version:** Docker 20.x or higher
- **Download:** https://www.docker.com/products/docker-desktop
- **Verify installation:**
  ```bash
  docker --version
  docker-compose --version
  ```

#### 4. Git
- **Download:** https://git-scm.com/downloads
- **Verify installation:**
  ```bash
  git --version
  ```

## Initial Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone <your-repository-url>
cd Study-Platform

# Verify you're in the correct directory
ls -la
# You should see: frontend/, backend/, docker/, docs/, README.md
```

### 2. Create Environment File

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your preferred editor
nano .env  # or vim, code, etc.
```

## Frontend Setup

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

```bash
# Install all npm packages
npm install

# This may take a few minutes
# You should see a node_modules/ directory created
```

### 3. Verify Frontend Setup

```bash
# Check that all dependencies are installed
npm list --depth=0

# You should see packages like:
# - react
# - vite
# - tailwindcss
# - @tanstack/react-query
# - etc.
```

### 4. Test Frontend Build

```bash
# Try building the frontend
npm run build

# If successful, you'll see a dist/ directory
```

## Backend Setup

### 1. Navigate to Backend Directory

```bash
cd ../backend
```

### 2. Create Virtual Environment

#### On macOS/Linux:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt should now show (venv)
```

#### On Windows:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Your prompt should now show (venv)
```

### 3. Install Python Dependencies

```bash
# Make sure virtual environment is activated
pip install -r requirements.txt

# This will install:
# - FastAPI
# - Uvicorn
# - SQLAlchemy
# - Pydantic
# - and more...
```

### 4. Verify Backend Setup

```bash
# Check installed packages
pip list

# Test import
python -c "import fastapi; print(fastapi.__version__)"
```

### 5. Initialize Database

The database will be created automatically when you first run the backend server. SQLite is used by default for development.

```bash
# The database file will be created at:
# backend/cloudplus_study.db
```

## Docker Setup (Optional)

### 1. Navigate to Docker Directory

```bash
cd ../docker
```

### 2. Build Docker Images

```bash
# Build all containers
docker-compose build

# This will build:
# - Frontend container
# - Backend container
```

### 3. Verify Docker Setup

```bash
# List built images
docker images | grep cloudplus

# You should see images for frontend and backend
```

## Running the Application

### Method 1: Development Mode (Recommended)

This method runs frontend and backend separately, which is best for development.

#### Terminal 1 - Backend Server:

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment (if not already activated)
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

#### Terminal 2 - Frontend Server:

```bash
# Navigate to frontend directory
cd frontend

# Start the development server
npm run dev

# You should see:
# VITE v5.x.x ready in xxx ms
# ➜ Local: http://localhost:3000/
```

### Method 2: Docker Compose

This method runs everything in containers.

```bash
# Navigate to docker directory
cd docker

# Start all services
docker-compose up

# To run in background:
docker-compose up -d

# To stop:
docker-compose down
```

### Method 3: With Lab Environments

```bash
# Navigate to docker directory
cd docker

# Start with lab profile
docker-compose --profile labs up

# This starts:
# - Frontend
# - Backend
# - Lab containers (nginx, docker-in-docker)
```

## Verification

### 1. Check Backend API

Open your browser or use curl:

```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status":"healthy","service":"cloud-plus-api"}

# API documentation
# Open: http://localhost:8000/docs
```

### 2. Check Frontend

```bash
# Open in browser
# http://localhost:3000

# You should see the study platform dashboard
```

### 3. Test API Connection

In the browser console (F12), you should not see any CORS errors or failed API requests.

### 4. Verify Database

```bash
# Check if database was created
ls -la backend/cloudplus_study.db

# Check database tables
sqlite3 backend/cloudplus_study.db ".tables"

# You should see tables:
# - users
# - questions
# - quiz_sessions
# - user_answers
# - user_progress
# - study_sessions
```

## Troubleshooting

### Issue: Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Find and kill process on port 3000
lsof -ti:3000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :3000   # Windows

# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000   # Windows
```

### Issue: Module Not Found (Frontend)

**Error:** `Cannot find module 'react'` or similar

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Issue: Module Not Found (Backend)

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
cd backend
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue: CORS Errors

**Error:** `Access to fetch blocked by CORS policy`

**Solution:**
1. Check that backend is running on port 8000
2. Verify CORS settings in `backend/app/main.py`
3. Make sure frontend is accessing `http://localhost:8000`

### Issue: Database Lock

**Error:** `database is locked`

**Solution:**
```bash
# Stop backend server
# Delete database and restart
rm backend/cloudplus_study.db
# Start backend server again
```

### Issue: Docker Build Fails

**Error:** Various Docker errors

**Solution:**
```bash
# Clean up Docker
docker-compose down -v
docker system prune -a

# Rebuild
docker-compose build --no-cache
docker-compose up
```

### Issue: Virtual Environment Not Activating

**Error:** `venv: command not found` or activation fails

**Solution:**
```bash
# Make sure Python venv module is installed
python3 -m pip install virtualenv

# Create virtual environment
python3 -m virtualenv venv

# Try activating again
source venv/bin/activate
```

## Next Steps

Once everything is running:

1. **Explore the Dashboard** - Check out the overview of your progress
2. **Take a Quiz** - Try answering some practice questions
3. **View Progress** - See how analytics are tracked
4. **Check Labs** - Browse available practice labs
5. **Review API Docs** - Visit http://localhost:8000/docs

## Additional Resources

- **Main README:** `../README.md`
- **API Documentation:** http://localhost:8000/docs when running
- **Frontend Code:** `../frontend/src/`
- **Backend Code:** `../backend/app/`

## Getting Help

If you encounter issues not covered here:

1. Check the main README.md troubleshooting section
2. Review the error messages carefully
3. Ensure all prerequisites are correctly installed
4. Check that ports 3000 and 8000 are available
5. Verify file permissions if on macOS/Linux

Happy studying for your CompTIA Cloud+ certification! 🚀
