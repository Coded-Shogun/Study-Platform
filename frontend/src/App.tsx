import { useState } from 'react'
import { BookOpen, Code, BarChart3, Calendar } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import QuizPage from './pages/QuizPage'
import LabsPage from './pages/LabsPage'
import ProgressPage from './pages/ProgressPage'

type TabType = 'dashboard' | 'quiz' | 'labs' | 'progress'

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard')

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'quiz', label: 'Quiz', icon: BookOpen },
    { id: 'labs', label: 'Labs', icon: Code },
    { id: 'progress', label: 'Progress', icon: Calendar },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-cloudplus-700 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">CompTIA Cloud+ Study Platform</h1>
          <p className="text-cloudplus-200 text-sm">Master cloud concepts, practice labs, and track your progress</p>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white shadow-md sticky top-0 z-10">
        <div className="container mx-auto px-4">
          <div className="flex space-x-1">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as TabType)}
                  className={`flex items-center gap-2 px-6 py-4 font-medium transition-colors border-b-2 ${
                    activeTab === tab.id
                      ? 'border-cloudplus-600 text-cloudplus-600'
                      : 'border-transparent text-gray-600 hover:text-cloudplus-600 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {tab.label}
                </button>
              )
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'quiz' && <QuizPage />}
        {activeTab === 'labs' && <LabsPage />}
        {activeTab === 'progress' && <ProgressPage />}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white mt-16">
        <div className="container mx-auto px-4 py-6 text-center">
          <p className="text-sm text-gray-400">
            CompTIA Cloud+ Study Platform © 2024 | Built for certification success
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
