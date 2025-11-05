import { Server, Play, Square, RefreshCw, CheckCircle } from 'lucide-react'
import { useState } from 'react'

interface Lab {
  id: string
  title: string
  description: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  duration: string
  status: 'not-started' | 'in-progress' | 'completed'
  topics: string[]
}

export default function LabsPage() {
  const [labs] = useState<Lab[]>([
    {
      id: '1',
      title: 'Cloud Architecture Basics',
      description: 'Learn fundamental cloud architecture concepts with hands-on Docker container deployment',
      difficulty: 'beginner',
      duration: '30 min',
      status: 'not-started',
      topics: ['Docker', 'Containers', 'Networking']
    },
    {
      id: '2',
      title: 'High Availability Setup',
      description: 'Configure load balancers and implement failover mechanisms',
      difficulty: 'intermediate',
      duration: '45 min',
      status: 'not-started',
      topics: ['Load Balancing', 'Redundancy', 'Failover']
    },
    {
      id: '3',
      title: 'Security Implementation',
      description: 'Implement security groups, firewalls, and access controls',
      difficulty: 'intermediate',
      duration: '60 min',
      status: 'not-started',
      topics: ['Security', 'Firewalls', 'IAM']
    },
    {
      id: '4',
      title: 'Auto-Scaling Configuration',
      description: 'Set up auto-scaling policies and test scaling scenarios',
      difficulty: 'advanced',
      duration: '90 min',
      status: 'not-started',
      topics: ['Auto-scaling', 'Monitoring', 'Performance']
    },
    {
      id: '5',
      title: 'Disaster Recovery',
      description: 'Implement backup strategies and practice disaster recovery procedures',
      difficulty: 'advanced',
      duration: '75 min',
      status: 'not-started',
      topics: ['Backup', 'Recovery', 'Business Continuity']
    }
  ])

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return 'bg-green-100 text-green-800'
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800'
      case 'advanced':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'in-progress':
        return <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />
      default:
        return <Play className="w-5 h-5 text-gray-400" />
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Practice Labs</h2>
        <p className="text-gray-600">Hands-on experience with real-world cloud scenarios</p>
      </div>

      {/* Lab Environment Status */}
      <div className="card bg-gradient-to-r from-cloudplus-50 to-blue-50 border-cloudplus-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="bg-cloudplus-500 p-3 rounded-lg">
              <Server className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-gray-900">Lab Environment</h3>
              <p className="text-sm text-gray-600">Docker environment ready</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium text-green-700">Online</span>
          </div>
        </div>
      </div>

      {/* Labs Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {labs.map((lab) => (
          <div key={lab.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-2">
                {getStatusIcon(lab.status)}
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${getDifficultyColor(lab.difficulty)}`}>
                  {lab.difficulty.charAt(0).toUpperCase() + lab.difficulty.slice(1)}
                </span>
              </div>
              <span className="text-sm text-gray-500">{lab.duration}</span>
            </div>

            <h3 className="text-xl font-bold text-gray-900 mb-2">{lab.title}</h3>
            <p className="text-gray-600 text-sm mb-4">{lab.description}</p>

            <div className="flex flex-wrap gap-2 mb-4">
              {lab.topics.map((topic, index) => (
                <span key={index} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                  {topic}
                </span>
              ))}
            </div>

            <div className="flex gap-2">
              {lab.status === 'not-started' && (
                <button className="btn-primary flex-1 inline-flex items-center justify-center gap-2">
                  <Play className="w-4 h-4" />
                  Start Lab
                </button>
              )}
              {lab.status === 'in-progress' && (
                <>
                  <button className="btn-primary flex-1 inline-flex items-center justify-center gap-2">
                    Continue Lab
                  </button>
                  <button className="btn-secondary inline-flex items-center gap-2">
                    <Square className="w-4 h-4" />
                    Stop
                  </button>
                </>
              )}
              {lab.status === 'completed' && (
                <button className="btn-secondary flex-1 inline-flex items-center justify-center gap-2">
                  <RefreshCw className="w-4 h-4" />
                  Restart Lab
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Lab Instructions */}
      <div className="card bg-blue-50 border-blue-200">
        <h3 className="font-bold text-gray-900 mb-3">How Labs Work</h3>
        <ul className="space-y-2 text-sm text-gray-700">
          <li className="flex items-start gap-2">
            <span className="text-cloudplus-600 font-bold">1.</span>
            <span>Click "Start Lab" to provision a Docker-based environment</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-cloudplus-600 font-bold">2.</span>
            <span>Follow step-by-step instructions to complete tasks</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-cloudplus-600 font-bold">3.</span>
            <span>Your progress is automatically saved</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-cloudplus-600 font-bold">4.</span>
            <span>Complete verification steps to earn credit</span>
          </li>
        </ul>
      </div>
    </div>
  )
}
