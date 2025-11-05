import { TrendingUp, Target, Clock, Award } from 'lucide-react'

export default function Dashboard() {
  const stats = [
    { label: 'Questions Completed', value: '0', icon: Target, color: 'bg-blue-500' },
    { label: 'Average Score', value: '0%', icon: Award, color: 'bg-green-500' },
    { label: 'Study Time', value: '0h', icon: Clock, color: 'bg-purple-500' },
    { label: 'Progress', value: '0%', icon: TrendingUp, color: 'bg-orange-500' },
  ]

  const domains = [
    { name: 'Cloud Architecture & Design', progress: 0, total: 15 },
    { name: 'Security', progress: 0, total: 12 },
    { name: 'Deployment', progress: 0, total: 10 },
    { name: 'Operations & Support', progress: 0, total: 13 },
    { name: 'Troubleshooting', progress: 0, total: 10 },
  ]

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Welcome to Your Study Dashboard</h2>
        <p className="text-gray-600">Track your progress and master CompTIA Cloud+ concepts</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.label} className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm font-medium">{stat.label}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">{stat.value}</p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Domain Progress */}
      <div className="card">
        <h3 className="text-xl font-bold text-gray-900 mb-6">Study Progress by Domain</h3>
        <div className="space-y-4">
          {domains.map((domain) => (
            <div key={domain.name}>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">{domain.name}</span>
                <span className="text-sm text-gray-500">
                  {domain.progress}/{domain.total} questions
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-cloudplus-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(domain.progress / domain.total) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card bg-gradient-to-br from-cloudplus-50 to-cloudplus-100 border-cloudplus-200">
          <h4 className="font-bold text-cloudplus-900 mb-2">Start Quiz</h4>
          <p className="text-sm text-cloudplus-700 mb-4">Test your knowledge with practice questions</p>
          <button className="btn-primary w-full">Begin Quiz</button>
        </div>

        <div className="card bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <h4 className="font-bold text-green-900 mb-2">Practice Labs</h4>
          <p className="text-sm text-green-700 mb-4">Hands-on experience with Docker environments</p>
          <button className="btn-primary w-full bg-green-600 hover:bg-green-700">Launch Lab</button>
        </div>

        <div className="card bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <h4 className="font-bold text-purple-900 mb-2">View Analytics</h4>
          <p className="text-sm text-purple-700 mb-4">Detailed insights into your performance</p>
          <button className="btn-primary w-full bg-purple-600 hover:bg-purple-700">See Progress</button>
        </div>
      </div>
    </div>
  )
}
