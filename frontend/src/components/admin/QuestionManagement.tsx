import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, Save, X, Eye } from 'lucide-react'

interface Question {
  id: number
  subject_id: number
  category_id: number | null
  domain: string
  question_text: string
  option_a: string
  option_b: string
  option_c: string
  option_d: string
  correct_answer: string
  explanation: string
  difficulty: string
  student_level: string | null
  created_at: string
}

interface Subject {
  id: number
  name: string
  code: string
}

interface Category {
  id: number
  name: string
  subject_id: number
}

interface QuestionForm {
  subject_id: number
  category_id: number | null
  domain: string
  question_text: string
  option_a: string
  option_b: string
  option_c: string
  option_d: string
  correct_answer: string
  explanation: string
  difficulty: string
  student_level: string
}

function QuestionManagement() {
  const [questions, setQuestions] = useState<Question[]>([])
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [viewingQuestion, setViewingQuestion] = useState<Question | null>(null)

  // Filters
  const [filterSubjectId, setFilterSubjectId] = useState<number | null>(null)
  const [filterLevel, setFilterLevel] = useState<string>('')
  const [filterDifficulty, setFilterDifficulty] = useState<string>('')

  const [formData, setFormData] = useState<QuestionForm>({
    subject_id: 0,
    category_id: null,
    domain: '',
    question_text: '',
    option_a: '',
    option_b: '',
    option_c: '',
    option_d: '',
    correct_answer: 'A',
    explanation: '',
    difficulty: 'medium',
    student_level: 'tertiary'
  })

  useEffect(() => {
    fetchSubjects()
    fetchQuestions()
  }, [filterSubjectId, filterLevel, filterDifficulty])

  useEffect(() => {
    if (formData.subject_id > 0) {
      fetchCategories(formData.subject_id)
    }
  }, [formData.subject_id])

  const fetchSubjects = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/admin/subjects')
      const data = await response.json()
      setSubjects(data)
    } catch (error) {
      console.error('Error fetching subjects:', error)
    }
  }

  const fetchCategories = async (subjectId: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/admin/categories?subject_id=${subjectId}`)
      const data = await response.json()
      setCategories(data)
    } catch (error) {
      console.error('Error fetching categories:', error)
    }
  }

  const fetchQuestions = async () => {
    try {
      let url = 'http://localhost:8000/api/admin/questions?limit=100'
      if (filterSubjectId) url += `&subject_id=${filterSubjectId}`
      if (filterLevel) url += `&student_level=${filterLevel}`
      if (filterDifficulty) url += `&difficulty=${filterDifficulty}`

      const response = await fetch(url)
      const data = await response.json()
      setQuestions(data)
    } catch (error) {
      console.error('Error fetching questions:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (formData.subject_id === 0) {
      alert('Please select a subject')
      return
    }

    try {
      const url = editingId
        ? `http://localhost:8000/api/admin/questions/${editingId}`
        : 'http://localhost:8000/api/admin/questions'

      const method = editingId ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      if (response.ok) {
        fetchQuestions()
        resetForm()
      } else {
        const error = await response.json()
        alert(error.detail || 'Failed to save question')
      }
    } catch (error) {
      console.error('Error saving question:', error)
      alert('Failed to save question')
    }
  }

  const handleEdit = (question: Question) => {
    setEditingId(question.id)
    setFormData({
      subject_id: question.subject_id,
      category_id: question.category_id,
      domain: question.domain,
      question_text: question.question_text,
      option_a: question.option_a,
      option_b: question.option_b,
      option_c: question.option_c,
      option_d: question.option_d,
      correct_answer: question.correct_answer,
      explanation: question.explanation,
      difficulty: question.difficulty,
      student_level: question.student_level || 'tertiary'
    })
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this question?')) return

    try {
      const response = await fetch(`http://localhost:8000/api/admin/questions/${id}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        fetchQuestions()
      } else {
        alert('Failed to delete question')
      }
    } catch (error) {
      console.error('Error deleting question:', error)
      alert('Failed to delete question')
    }
  }

  const resetForm = () => {
    setFormData({
      subject_id: 0,
      category_id: null,
      domain: '',
      question_text: '',
      option_a: '',
      option_b: '',
      option_c: '',
      option_d: '',
      correct_answer: 'A',
      explanation: '',
      difficulty: 'medium',
      student_level: 'tertiary'
    })
    setEditingId(null)
    setShowForm(false)
  }

  const getSubjectName = (subjectId: number) => {
    const subject = subjects.find(s => s.id === subjectId)
    return subject ? subject.name : 'Unknown'
  }

  const getCategoryName = (categoryId: number | null) => {
    if (!categoryId) return 'N/A'
    const category = categories.find(c => c.id === categoryId)
    return category ? category.name : 'N/A'
  }

  if (loading) {
    return <div className="text-center py-8">Loading questions...</div>
  }

  return (
    <div className="space-y-6">
      {/* Header with Filters */}
      <div className="flex justify-between items-start gap-4 flex-wrap">
        <div>
          <h3 className="text-xl font-bold text-gray-800">Question Bank Management</h3>
          <p className="text-sm text-gray-600 mt-1">{questions.length} questions total</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 bg-cloudplus-600 text-white px-4 py-2 rounded-md hover:bg-cloudplus-700 transition-colors"
        >
          {showForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showForm ? 'Cancel' : 'Add Question'}
        </button>
      </div>

      {/* Filters */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Filters</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <select
            value={filterSubjectId || ''}
            onChange={(e) => setFilterSubjectId(e.target.value ? parseInt(e.target.value) : null)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
          >
            <option value="">All Subjects</option>
            {subjects.map((subject) => (
              <option key={subject.id} value={subject.id}>
                {subject.name}
              </option>
            ))}
          </select>
          <select
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
          >
            <option value="">All Levels</option>
            <option value="primary">Primary</option>
            <option value="high_school">High School</option>
            <option value="tertiary">Tertiary</option>
          </select>
          <select
            value={filterDifficulty}
            onChange={(e) => setFilterDifficulty(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
          >
            <option value="">All Difficulties</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </div>
      </div>

      {/* Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-gray-50 rounded-lg p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Subject *</label>
              <select
                required
                value={formData.subject_id}
                onChange={(e) => setFormData({ ...formData, subject_id: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
              >
                <option value={0}>Select a subject</option>
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <select
                value={formData.category_id || ''}
                onChange={(e) => setFormData({ ...formData, category_id: e.target.value ? parseInt(e.target.value) : null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
                disabled={formData.subject_id === 0}
              >
                <option value="">Select a category (optional)</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Domain *</label>
              <input
                type="text"
                required
                value={formData.domain}
                onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
                placeholder="e.g., Security"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Student Level *</label>
              <select
                required
                value={formData.student_level}
                onChange={(e) => setFormData({ ...formData, student_level: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
              >
                <option value="primary">Primary</option>
                <option value="high_school">High School</option>
                <option value="tertiary">Tertiary</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Difficulty *</label>
              <select
                required
                value={formData.difficulty}
                onChange={(e) => setFormData({ ...formData, difficulty: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Correct Answer *</label>
              <select
                required
                value={formData.correct_answer}
                onChange={(e) => setFormData({ ...formData, correct_answer: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
              >
                <option value="A">Option A</option>
                <option value="B">Option B</option>
                <option value="C">Option C</option>
                <option value="D">Option D</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Question Text *</label>
            <textarea
              required
              value={formData.question_text}
              onChange={(e) => setFormData({ ...formData, question_text: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
              placeholder="Enter the question text"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Option A *</label>
              <input
                type="text"
                required
                value={formData.option_a}
                onChange={(e) => setFormData({ ...formData, option_a: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Option B *</label>
              <input
                type="text"
                required
                value={formData.option_b}
                onChange={(e) => setFormData({ ...formData, option_b: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Option C *</label>
              <input
                type="text"
                required
                value={formData.option_c}
                onChange={(e) => setFormData({ ...formData, option_c: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Option D *</label>
              <input
                type="text"
                required
                value={formData.option_d}
                onChange={(e) => setFormData({ ...formData, option_d: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Explanation *</label>
            <textarea
              required
              value={formData.explanation}
              onChange={(e) => setFormData({ ...formData, explanation: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
              placeholder="Explain why the correct answer is correct"
            />
          </div>

          <button
            type="submit"
            className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
          >
            <Save className="w-4 h-4" />
            {editingId ? 'Update Question' : 'Create Question'}
          </button>
        </form>
      )}

      {/* Questions List */}
      <div className="space-y-3">
        {questions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No questions found. Create your first question to get started.
          </div>
        ) : (
          questions.map((question) => (
            <div
              key={question.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap mb-2">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                      {getSubjectName(question.subject_id)}
                    </span>
                    <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                      {question.student_level || 'N/A'}
                    </span>
                    <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-medium rounded">
                      {question.difficulty}
                    </span>
                    <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs font-medium rounded">
                      {question.domain}
                    </span>
                  </div>
                  <p className="text-gray-800 font-medium line-clamp-2">{question.question_text}</p>
                  <p className="text-xs text-gray-400 mt-2">
                    Correct Answer: {question.correct_answer} | Created: {new Date(question.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setViewingQuestion(question)}
                    className="p-2 text-green-600 hover:bg-green-50 rounded-md transition-colors"
                    title="View"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleEdit(question)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                    title="Edit"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(question.id)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Question View Modal */}
      {viewingQuestion && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-bold text-gray-800">Question Details</h3>
              <button
                onClick={() => setViewingQuestion(null)}
                className="p-2 text-gray-600 hover:bg-gray-100 rounded-md"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-gray-600">Subject</p>
                <p className="text-gray-800">{getSubjectName(viewingQuestion.subject_id)}</p>
              </div>

              <div className="flex gap-4">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600">Level</p>
                  <p className="text-gray-800">{viewingQuestion.student_level}</p>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600">Difficulty</p>
                  <p className="text-gray-800">{viewingQuestion.difficulty}</p>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600">Domain</p>
                  <p className="text-gray-800">{viewingQuestion.domain}</p>
                </div>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-600 mb-2">Question</p>
                <p className="text-gray-800">{viewingQuestion.question_text}</p>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-600 mb-2">Options</p>
                <div className="space-y-2">
                  <div className={`p-3 rounded-md ${viewingQuestion.correct_answer === 'A' ? 'bg-green-50 border-2 border-green-500' : 'bg-gray-50'}`}>
                    <p className="font-medium">A. {viewingQuestion.option_a}</p>
                  </div>
                  <div className={`p-3 rounded-md ${viewingQuestion.correct_answer === 'B' ? 'bg-green-50 border-2 border-green-500' : 'bg-gray-50'}`}>
                    <p className="font-medium">B. {viewingQuestion.option_b}</p>
                  </div>
                  <div className={`p-3 rounded-md ${viewingQuestion.correct_answer === 'C' ? 'bg-green-50 border-2 border-green-500' : 'bg-gray-50'}`}>
                    <p className="font-medium">C. {viewingQuestion.option_c}</p>
                  </div>
                  <div className={`p-3 rounded-md ${viewingQuestion.correct_answer === 'D' ? 'bg-green-50 border-2 border-green-500' : 'bg-gray-50'}`}>
                    <p className="font-medium">D. {viewingQuestion.option_d}</p>
                  </div>
                </div>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-600 mb-2">Explanation</p>
                <p className="text-gray-800 bg-blue-50 p-3 rounded-md">{viewingQuestion.explanation}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default QuestionManagement
