import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, Save, X } from 'lucide-react'

interface Category {
  id: number
  subject_id: number
  name: string
  description: string | null
  created_at: string
}

interface Subject {
  id: number
  name: string
  code: string
}

interface CategoryForm {
  subject_id: number
  name: string
  description: string
}

function CategoryManagement() {
  const [categories, setCategories] = useState<Category[]>([])
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [filterSubjectId, setFilterSubjectId] = useState<number | null>(null)
  const [formData, setFormData] = useState<CategoryForm>({
    subject_id: 0,
    name: '',
    description: ''
  })

  useEffect(() => {
    fetchSubjects()
    fetchCategories()
  }, [filterSubjectId])

  const fetchSubjects = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/admin/subjects')
      const data = await response.json()
      setSubjects(data)
    } catch (error) {
      console.error('Error fetching subjects:', error)
    }
  }

  const fetchCategories = async () => {
    try {
      const url = filterSubjectId
        ? `http://localhost:8000/api/admin/categories?subject_id=${filterSubjectId}`
        : 'http://localhost:8000/api/admin/categories'
      const response = await fetch(url)
      const data = await response.json()
      setCategories(data)
    } catch (error) {
      console.error('Error fetching categories:', error)
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
        ? `http://localhost:8000/api/admin/categories/${editingId}`
        : 'http://localhost:8000/api/admin/categories'

      const method = editingId ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      if (response.ok) {
        fetchCategories()
        resetForm()
      } else {
        const error = await response.json()
        alert(error.detail || 'Failed to save category')
      }
    } catch (error) {
      console.error('Error saving category:', error)
      alert('Failed to save category')
    }
  }

  const handleEdit = (category: Category) => {
    setEditingId(category.id)
    setFormData({
      subject_id: category.subject_id,
      name: category.name,
      description: category.description || ''
    })
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this category?')) return

    try {
      const response = await fetch(`http://localhost:8000/api/admin/categories/${id}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        fetchCategories()
      } else {
        alert('Failed to delete category')
      }
    } catch (error) {
      console.error('Error deleting category:', error)
      alert('Failed to delete category')
    }
  }

  const resetForm = () => {
    setFormData({ subject_id: 0, name: '', description: '' })
    setEditingId(null)
    setShowForm(false)
  }

  const getSubjectName = (subjectId: number) => {
    const subject = subjects.find(s => s.id === subjectId)
    return subject ? subject.name : 'Unknown'
  }

  if (loading) {
    return <div className="text-center py-8">Loading categories...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center gap-4 flex-wrap">
        <h3 className="text-xl font-bold text-gray-800">Category Management</h3>
        <div className="flex gap-2 items-center">
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
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 bg-cloudplus-600 text-white px-4 py-2 rounded-md hover:bg-cloudplus-700 transition-colors"
          >
            {showForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
            {showForm ? 'Cancel' : 'Add Category'}
          </button>
        </div>
      </div>

      {/* Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-gray-50 rounded-lg p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subject *
              </label>
              <select
                required
                value={formData.subject_id}
                onChange={(e) => setFormData({ ...formData, subject_id: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
              >
                <option value={0}>Select a subject</option>
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name} ({subject.code})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
                placeholder="e.g., Security"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-cloudplus-500"
              placeholder="Enter category description"
            />
          </div>
          <button
            type="submit"
            className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
          >
            <Save className="w-4 h-4" />
            {editingId ? 'Update Category' : 'Create Category'}
          </button>
        </form>
      )}

      {/* Categories List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {categories.length === 0 ? (
          <div className="col-span-2 text-center py-8 text-gray-500">
            No categories found. Create your first category to get started.
          </div>
        ) : (
          categories.map((category) => (
            <div
              key={category.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h4 className="text-lg font-semibold text-gray-800">{category.name}</h4>
                  <p className="text-sm text-blue-600 mt-1">
                    Subject: {getSubjectName(category.subject_id)}
                  </p>
                  {category.description && (
                    <p className="text-gray-600 mt-2 text-sm">{category.description}</p>
                  )}
                  <p className="text-xs text-gray-400 mt-2">
                    Created: {new Date(category.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(category)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                    title="Edit"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(category.id)}
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
    </div>
  )
}

export default CategoryManagement
