import { useState } from 'react'
import { UserPlus, ArrowRight } from 'lucide-react'

interface RegisterForm {
  username: string
  email: string
  password: string
  full_name: string
  role: string
  student_level: string
}

function RegisterPage() {
  const [formData, setFormData] = useState<RegisterForm>({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'student',
    student_level: 'tertiary'
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await fetch('http://localhost:8000/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      if (response.ok) {
        setSuccess(true)
        setFormData({
          username: '',
          email: '',
          password: '',
          full_name: '',
          role: 'student',
          student_level: 'tertiary'
        })
      } else {
        const data = await response.json()
        setError(data.detail || 'Registration failed')
      }
    } catch (err) {
      setError('Failed to connect to server')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-cloudplus-600 to-cloudplus-800 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-8">
        <div className="flex items-center gap-3 mb-6">
          <UserPlus className="w-8 h-8 text-cloudplus-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Create Account</h2>
            <p className="text-gray-600">Join the Study Platform</p>
          </div>
        </div>

        {success && (
          <div className="bg-green-50 border border-green-200 text-green-800 p-4 rounded-md mb-6">
            Registration successful! You can now log in with your credentials.
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-md mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username *
              </label>
              <input
                type="text"
                required
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
                placeholder="Choose a username"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Full Name *
              </label>
              <input
                type="text"
                required
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
                placeholder="Your full name"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email *
            </label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
              placeholder="your.email@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password *
            </label>
            <input
              type="password"
              required
              minLength={6}
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
              placeholder="At least 6 characters"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Account Type *
              </label>
              <select
                required
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
              >
                <option value="student">Student</option>
                <option value="teacher">Teacher</option>
                <option value="admin">Administrator</option>
              </select>
            </div>

            {formData.role === 'student' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Student Level *
                </label>
                <select
                  required
                  value={formData.student_level}
                  onChange={(e) => setFormData({ ...formData, student_level: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
                >
                  <option value="primary">Primary School</option>
                  <option value="high_school">High School</option>
                  <option value="tertiary">Tertiary/University</option>
                </select>
              </div>
            )}
          </div>

          {formData.role === 'student' && (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> Your student level determines which courses and quizzes you'll have access to.
                You can focus on content appropriate for your education level.
              </p>
            </div>
          )}

          {formData.role === 'teacher' && (
            <div className="bg-purple-50 border border-purple-200 rounded-md p-4">
              <p className="text-sm text-purple-800">
                <strong>Teacher Account:</strong> You'll have access to admin features for managing courses,
                creating questions, and organizing content for students.
              </p>
            </div>
          )}

          {formData.role === 'admin' && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-800">
                <strong>Administrator Account:</strong> You'll have full access to all platform features,
                including user management, course creation, and system configuration.
              </p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-cloudplus-600 text-white px-6 py-3 rounded-md hover:bg-cloudplus-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? (
              'Creating Account...'
            ) : (
              <>
                Create Account
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          Already have an account?{' '}
          <a href="#login" className="text-cloudplus-600 hover:text-cloudplus-700 font-medium">
            Sign in here
          </a>
        </div>
      </div>
    </div>
  )
}

export default RegisterPage
