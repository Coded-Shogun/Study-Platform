# CompTIA Cloud+ Study Platform

A comprehensive, interactive study platform designed to help you prepare for the CompTIA Cloud+ (CV0-003) certification exam. This platform combines theoretical knowledge with practical hands-on labs, progress tracking, and analytics.

## Features

### 🎯 Interactive Quiz System
- 30+ practice questions covering all CompTIA Cloud+ domains
- Real-time feedback and explanations
- Domain-specific filtering
- Progress tracking across quiz sessions
- Score calculation and history

### 🧪 Docker-Based Practice Labs
- Hands-on lab environments using Docker
- Labs covering key cloud concepts:
  - Cloud Architecture Basics
  - High Availability Setup
  - Security Implementation
  - Auto-Scaling Configuration
  - Disaster Recovery
- Automated environment provisioning
- Progress tracking for lab completion

### 📊 Progress Analytics
- Performance tracking by domain
- Weekly activity charts
- Study streak monitoring
- Achievement system
- Personalized study recommendations
- Visual performance dashboards

### 🎓 Study Domains Covered
1. **Cloud Architecture & Design** (15 questions)
2. **Security** (12 questions)
3. **Deployment** (10 questions)
4. **Operations & Support** (13 questions)
5. **Troubleshooting** (10 questions)

## Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and building
- **TailwindCSS** for styling
- **Tanstack Query** for server state management
- **Recharts** for data visualization
- **Radix UI** for accessible components
- **Lucide React** for icons

### Backend
- **FastAPI** for high-performance API
- **SQLAlchemy** with SQLite (development) / PostgreSQL (production)
- **Pydantic** for data validation
- **Uvicorn** as ASGI server

### DevOps
- **Docker & Docker Compose** for containerization
- **Git** for version control

## Project Structure

```
cloudplus-study-platform/
├── frontend/                 # React + Vite frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── data/            # Quiz questions and data
│   │   ├── hooks/           # Custom React hooks
│   │   └── utils/           # Utility functions
│   ├── public/              # Static assets
│   └── package.json         # Frontend dependencies
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend container
├── docker/                 # Docker configurations
│   ├── docker-compose.yml # Multi-container setup
│   └── configs/           # Lab configurations
└── docs/                  # Documentation
```

## Getting Started

### Prerequisites
- **Node.js** 18+ and npm
- **Python** 3.11+
- **Docker** and Docker Compose (for labs)
- **Git**

### Installation

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd Study-Platform
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
```

#### 3. Backend Setup
```bash
cd ../backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 4. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running the Application

#### Option 1: Development Mode (Recommended for Development)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

The application will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

#### Option 2: Docker Compose (Full Stack)

```bash
cd docker
docker-compose up --build
```

#### Option 3: With Lab Environments

```bash
cd docker
docker-compose --profile labs up --build
```

## Usage Guide

### 1. Dashboard
- View your overall study statistics
- See progress across all domains
- Access quick action buttons for quizzes and labs

### 2. Quiz Section
- Select domains or take mixed quizzes
- Answer questions with immediate feedback
- View detailed explanations for each answer
- Track your score in real-time

### 3. Practice Labs
- Browse available labs by difficulty
- Start lab environments with one click
- Follow step-by-step instructions
- Complete verification tasks

### 4. Progress Tracking
- Monitor your study streak
- View weekly activity charts
- Analyze performance by domain
- Earn achievements
- Get personalized recommendations

## API Endpoints

### Quiz Endpoints
- `GET /api/quiz/questions` - Get quiz questions
- `GET /api/quiz/questions/{id}` - Get specific question
- `POST /api/quiz/sessions` - Create quiz session
- `POST /api/quiz/submit-answer` - Submit an answer
- `GET /api/quiz/domains` - Get all domains

### Progress Endpoints
- `GET /api/progress/summary` - Get progress summary
- `GET /api/progress/domains` - Get domain progress
- `GET /api/progress/sessions` - Get study sessions
- `GET /api/progress/analytics/weekly` - Get weekly analytics
- `GET /api/progress/achievements` - Get achievements

### Lab Endpoints
- `GET /api/labs/` - Get all labs
- `GET /api/labs/{id}` - Get specific lab
- `POST /api/labs/{id}/start` - Start lab environment
- `POST /api/labs/{id}/stop` - Stop lab environment
- `GET /api/labs/{id}/status` - Get lab status

### Auth Endpoints
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

## Development

### Frontend Development
```bash
cd frontend
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Lint code
```

### Backend Development
```bash
cd backend
uvicorn app.main:app --reload  # Start with hot reload
pytest                          # Run tests
```

### Database Management
The application uses SQLite by default for development. The database file is created automatically at `backend/cloudplus_study.db`.

To use PostgreSQL in production:
1. Update `DATABASE_URL` in `.env`
2. Uncomment PostgreSQL service in `docker-compose.yml`
3. Run migrations (if using Alembic)

## Adding New Questions

Edit `frontend/src/data/quizData.ts` and add new questions following this format:

```typescript
{
  id: 'unique-id',
  domain: 'Domain Name',
  question: 'Your question here?',
  options: [
    'Option A',
    'Option B',
    'Option C',
    'Option D'
  ],
  correctAnswer: 'Option B',
  explanation: 'Detailed explanation of why this is correct...'
}
```

## Customization

### Changing Theme Colors
Edit `frontend/tailwind.config.js` to customize the color scheme:

```javascript
colors: {
  'cloudplus': {
    500: '#your-color',
    600: '#your-darker-color',
    // ... more shades
  }
}
```

### Adding New Lab Environments
1. Define lab in `backend/app/api/labs.py`
2. Create Docker configuration in `docker/`
3. Add lab scripts in `docker/lab-scripts/`

## Testing

### Frontend Testing
```bash
cd frontend
npm run test
```

### Backend Testing
```bash
cd backend
pytest
pytest --cov=app  # With coverage
```

## Deployment

### Production Considerations
1. **Security:**
   - Change `SECRET_KEY` in `.env`
   - Enable HTTPS
   - Implement proper JWT authentication
   - Hash passwords with bcrypt

2. **Database:**
   - Use PostgreSQL instead of SQLite
   - Set up regular backups
   - Enable connection pooling

3. **Performance:**
   - Enable Redis for caching
   - Use CDN for static assets
   - Configure proper logging

4. **Monitoring:**
   - Set up application monitoring
   - Configure error tracking
   - Enable performance metrics

### Docker Deployment
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

**Database Lock Error:**
```bash
# Remove database and restart
rm backend/cloudplus_study.db
```

**Module Not Found:**
```bash
# Reinstall dependencies
cd frontend && npm install
cd backend && pip install -r requirements.txt
```

**Docker Issues:**
```bash
# Clean up containers and rebuild
docker-compose down -v
docker-compose up --build
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap

- [ ] Advanced authentication with JWT
- [ ] User profiles and customization
- [ ] Performance-based question simulator
- [ ] Mobile-responsive enhancements
- [ ] Study schedule management with calendar
- [ ] Export capabilities for progress reports
- [ ] Community features (forums, shared notes)
- [ ] AI-powered study recommendations
- [ ] Practice exam mode with timer
- [ ] Flashcard system
- [ ] Video tutorial integration

## License

This project is for educational purposes. CompTIA and Cloud+ are trademarks of CompTIA, Inc.

## Acknowledgments

- CompTIA for the Cloud+ certification program
- React and FastAPI communities
- All contributors to this project

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the documentation in `/docs`
- Review API documentation at `/docs` endpoint

---

**Good luck with your CompTIA Cloud+ certification!** 🚀☁️
