import { useState, useEffect } from 'react'
import { Users, BookOpen, FolderTree, ListChecks } from 'lucide-react'

interface Statistics {
  total_subjects: number
  total_categories: number
  total_questions: number
  total_users: number
  questions_by_level: {
    primary: number
    high_school: number
    tertiary: number
  }
  users_by_role: {
    admin: number
    teacher: number
    student: number
  }
}

function AdminStatistics() {
  const [stats, setStats] = useState<Statistics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStatistics()
  }, [])

  const fetchStatistics = async () => {
    try {
      // TODO: Replace with actual API call
      const response = await fetch('http://localhost:8000/api/admin/statistics')
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Error fetching statistics:', error)
      // Mock data for development
      setStats({
        total_subjects: 0,
        total_categories: 0,
        total_questions: 0,
        total_users: 0,
        questions_by_level: { primary: 0, high_school: 0, tertiary: 0 },
        users_by_role: { admin: 0, teacher: 0, student: 0 }
      })
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-8">Loading statistics...</div>
  }

  if (!stats) {
    return <div className="text-center py-8 text-red-600">Failed to load statistics</div>
  }

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-800">Platform Statistics</h3>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 rounded-lg p-6">
          <div className="flex items-center gap-4">
            <BookOpen className="w-10 h-10 text-blue-600" />
            <div>
              <p className="text-sm text-gray-600">Subjects</p>
              <p className="text-3xl font-bold text-gray-800">{stats.total_subjects}</p>
            </div>
          </div>
        </div>

        <div className="bg-green-50 rounded-lg p-6">
          <div className="flex items-center gap-4">
            <FolderTree className="w-10 h-10 text-green-600" />
            <div>
              <p className="text-sm text-gray-600">Categories</p>
              <p className="text-3xl font-bold text-gray-800">{stats.total_categories}</p>
            </div>
          </div>
        </div>

        <div className="bg-purple-50 rounded-lg p-6">
          <div className="flex items-center gap-4">
            <ListChecks className="w-10 h-10 text-purple-600" />
            <div>
              <p className="text-sm text-gray-600">Questions</p>
              <p className="text-3xl font-bold text-gray-800">{stats.total_questions}</p>
            </div>
          </div>
        </div>

        <div className="bg-orange-50 rounded-lg p-6">
          <div className="flex items-center gap-4">
            <Users className="w-10 h-10 text-orange-600" />
            <div>
              <p className="text-sm text-gray-600">Users</p>
              <p className="text-3xl font-bold text-gray-800">{stats.total_users}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Questions by Level */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h4 className="text-lg font-semibold text-gray-800 mb-4">Questions by Student Level</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4 border-l-4 border-blue-500">
            <p className="text-sm text-gray-600">Primary</p>
            <p className="text-2xl font-bold text-gray-800">{stats.questions_by_level.primary}</p>
          </div>
          <div className="bg-white rounded-lg p-4 border-l-4 border-green-500">
            <p className="text-sm text-gray-600">High School</p>
            <p className="text-2xl font-bold text-gray-800">{stats.questions_by_level.high_school}</p>
          </div>
          <div className="bg-white rounded-lg p-4 border-l-4 border-purple-500">
            <p className="text-sm text-gray-600">Tertiary</p>
            <p className="text-2xl font-bold text-gray-800">{stats.questions_by_level.tertiary}</p>
          </div>
        </div>
      </div>

      {/* Users by Role */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h4 className="text-lg font-semibold text-gray-800 mb-4">Users by Role</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4 border-l-4 border-red-500">
            <p className="text-sm text-gray-600">Administrators</p>
            <p className="text-2xl font-bold text-gray-800">{stats.users_by_role.admin}</p>
          </div>
          <div className="bg-white rounded-lg p-4 border-l-4 border-yellow-500">
            <p className="text-sm text-gray-600">Teachers</p>
            <p className="text-2xl font-bold text-gray-800">{stats.users_by_role.teacher}</p>
          </div>
          <div className="bg-white rounded-lg p-4 border-l-4 border-blue-500">
            <p className="text-sm text-gray-600">Students</p>
            <p className="text-2xl font-bold text-gray-800">{stats.users_by_role.student}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AdminStatistics
