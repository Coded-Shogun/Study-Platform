import { useState } from 'react'
import { Settings, BookOpen, FolderTree, ListChecks, BarChart } from 'lucide-react'
import SubjectManagement from '../components/admin/SubjectManagement'
import CategoryManagement from '../components/admin/CategoryManagement'
import QuestionManagement from '../components/admin/QuestionManagement'
import AdminStatistics from '../components/admin/AdminStatistics'

type AdminTabType = 'statistics' | 'subjects' | 'categories' | 'questions'

function AdminPage() {
  const [activeTab, setActiveTab] = useState<AdminTabType>('statistics')

  const tabs = [
    { id: 'statistics', label: 'Statistics', icon: BarChart },
    { id: 'subjects', label: 'Subjects', icon: BookOpen },
    { id: 'categories', label: 'Categories', icon: FolderTree },
    { id: 'questions', label: 'Questions', icon: ListChecks },
  ]

  return (
    <div className="space-y-6">
      {/* Admin Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center gap-3">
          <Settings className="w-8 h-8 text-cloudplus-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Admin Dashboard</h2>
            <p className="text-gray-600">Manage courses, subjects, and question banks</p>
          </div>
        </div>
      </div>

      {/* Sub Navigation */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex space-x-2">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as AdminTabType)}
                className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-cloudplus-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg shadow-md p-6">
        {activeTab === 'statistics' && <AdminStatistics />}
        {activeTab === 'subjects' && <SubjectManagement />}
        {activeTab === 'categories' && <CategoryManagement />}
        {activeTab === 'questions' && <QuestionManagement />}
      </div>
    </div>
  )
}

export default AdminPage
