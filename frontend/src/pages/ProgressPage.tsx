import { Calendar, TrendingUp, Award, BookOpen } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'

export default function ProgressPage() {
  const weeklyProgress = [
    { day: 'Mon', questions: 5, time: 30 },
    { day: 'Tue', questions: 8, time: 45 },
    { day: 'Wed', questions: 6, time: 35 },
    { day: 'Thu', questions: 10, time: 60 },
    { day: 'Fri', questions: 7, time: 40 },
    { day: 'Sat', questions: 12, time: 75 },
    { day: 'Sun', questions: 9, time: 50 },
  ]

  const domainScores = [
    { domain: 'Architecture', score: 75 },
    { domain: 'Security', score: 85 },
    { domain: 'Deployment', score: 70 },
    { domain: 'Operations', score: 80 },
    { domain: 'Troubleshooting', score: 65 },
  ]

  const achievements = [
    { title: 'First Steps', description: 'Complete your first quiz', earned: true, icon: '🎯' },
    { title: 'Week Warrior', description: 'Study 7 days in a row', earned: false, icon: '🔥' },
    { title: 'Lab Master', description: 'Complete 5 practice labs', earned: false, icon: '🧪' },
    { title: 'Perfect Score', description: 'Get 100% on any quiz', earned: false, icon: '💯' },
    { title: 'Dedicated Learner', description: 'Study for 10 hours total', earned: false, icon: '📚' },
    { title: 'Domain Expert', description: 'Master all questions in one domain', earned: false, icon: '👑' },
  ]

  const studyStreak = 3
  const totalStudyTime = 285 // minutes
  const questionsAnswered = 57
  const averageScore = 78

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Your Progress</h2>
        <p className="text-gray-600">Track your learning journey and achievements</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <div className="bg-orange-500 p-2 rounded-lg">
              <Calendar className="w-5 h-5 text-white" />
            </div>
            <span className="text-gray-600 text-sm font-medium">Study Streak</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{studyStreak} days</p>
          <p className="text-sm text-gray-500 mt-1">Keep it up!</p>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <div className="bg-blue-500 p-2 rounded-lg">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <span className="text-gray-600 text-sm font-medium">Questions</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{questionsAnswered}</p>
          <p className="text-sm text-gray-500 mt-1">Answered</p>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <div className="bg-green-500 p-2 rounded-lg">
              <Award className="w-5 h-5 text-white" />
            </div>
            <span className="text-gray-600 text-sm font-medium">Average Score</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{averageScore}%</p>
          <p className="text-sm text-gray-500 mt-1">Great progress!</p>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <div className="bg-purple-500 p-2 rounded-lg">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <span className="text-gray-600 text-sm font-medium">Study Time</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{Math.floor(totalStudyTime / 60)}h {totalStudyTime % 60}m</p>
          <p className="text-sm text-gray-500 mt-1">Total time</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weekly Activity */}
        <div className="card">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Weekly Activity</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={weeklyProgress}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="questions" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Domain Performance */}
        <div className="card">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Performance by Domain</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={domainScores}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="domain" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="score" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Achievements */}
      <div className="card">
        <h3 className="text-lg font-bold text-gray-900 mb-6">Achievements</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {achievements.map((achievement, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border-2 transition-all ${
                achievement.earned
                  ? 'border-yellow-400 bg-yellow-50'
                  : 'border-gray-200 bg-gray-50 opacity-60'
              }`}
            >
              <div className="text-3xl mb-2">{achievement.icon}</div>
              <h4 className="font-bold text-gray-900 mb-1">{achievement.title}</h4>
              <p className="text-sm text-gray-600">{achievement.description}</p>
              {achievement.earned && (
                <div className="mt-2">
                  <span className="text-xs bg-yellow-200 text-yellow-800 px-2 py-1 rounded-full font-medium">
                    Earned ✓
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Study Recommendations */}
      <div className="card bg-gradient-to-r from-cloudplus-50 to-blue-50 border-cloudplus-200">
        <h3 className="text-lg font-bold text-gray-900 mb-4">📊 Study Recommendations</h3>
        <ul className="space-y-3">
          <li className="flex items-start gap-3">
            <span className="text-cloudplus-600 font-bold">•</span>
            <span className="text-gray-700">
              Focus on <strong>Troubleshooting</strong> domain - your lowest scoring area (65%)
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-cloudplus-600 font-bold">•</span>
            <span className="text-gray-700">
              Great job on <strong>Security</strong>! Keep practicing to maintain your 85% score
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-cloudplus-600 font-bold">•</span>
            <span className="text-gray-700">
              You're on a {studyStreak}-day streak! Study tomorrow to reach 4 days
            </span>
          </li>
        </ul>
      </div>
    </div>
  )
}
