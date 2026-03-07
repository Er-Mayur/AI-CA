import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import toast from 'react-hot-toast'
import { 
  Shield, Plus, Edit2, Trash2, Copy, Check, X, 
  ChevronDown, ChevronUp, FileText, AlertTriangle,
  Download, Upload, RefreshCw, Eye, EyeOff
} from 'lucide-react'
import Layout from '../components/Layout'

function AdminTaxRules() {
  const { user } = useAuth()
  const navigate = useNavigate()
  
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedRule, setSelectedRule] = useState(null)
  const [showEditor, setShowEditor] = useState(false)
  const [editorMode, setEditorMode] = useState('view') // view, edit, create
  const [editJson, setEditJson] = useState('')
  const [jsonError, setJsonError] = useState(null)
  const [template, setTemplate] = useState(null)
  const [showDuplicateModal, setShowDuplicateModal] = useState(false)
  const [duplicateData, setDuplicateData] = useState({ newFY: '', newAY: '' })
  const [expandedRows, setExpandedRows] = useState({})

  // Check admin access
  useEffect(() => {
    if (!user?.is_admin) {
      toast.error('Admin access required')
      navigate('/dashboard')
    }
  }, [user, navigate])

  // Load tax rules
  useEffect(() => {
    if (user?.is_admin) {
      loadRules()
    }
  }, [user])

  const loadRules = async () => {
    try {
      setLoading(true)
      const response = await api.get('/admin/tax-rules')
      setRules(response.data)
    } catch (error) {
      console.error('Failed to load tax rules:', error)
      if (error.response?.status === 403) {
        toast.error('Admin access required')
        navigate('/dashboard')
      } else {
        toast.error('Failed to load tax rules')
      }
    } finally {
      setLoading(false)
    }
  }

  const loadFullRule = async (fy) => {
    try {
      const response = await api.get(`/admin/tax-rules/${fy}`)
      setSelectedRule(response.data)
      setEditJson(JSON.stringify(response.data.rules_json, null, 2))
      setJsonError(null)
    } catch (error) {
      toast.error('Failed to load rule details')
    }
  }

  const loadTemplate = async () => {
    try {
      const response = await api.get('/admin/tax-rules-template')
      setTemplate(response.data)
      setEditJson(JSON.stringify(response.data.template, null, 2))
      setJsonError(null)
    } catch (error) {
      toast.error('Failed to load template')
    }
  }

  const handleCreate = async () => {
    await loadTemplate()
    setEditorMode('create')
    setShowEditor(true)
    setSelectedRule(null)
  }

  const handleView = async (fy) => {
    await loadFullRule(fy)
    setEditorMode('view')
    setShowEditor(true)
  }

  const handleEdit = async (fy) => {
    await loadFullRule(fy)
    setEditorMode('edit')
    setShowEditor(true)
  }

  const handleDuplicate = (fy) => {
    setSelectedRule(rules.find(r => r.financial_year === fy))
    // Auto-generate next FY
    const [startYear] = fy.split('-')
    const nextStart = parseInt(startYear) + 1
    const nextEnd = (nextStart + 1).toString().slice(-2)
    setDuplicateData({
      newFY: `${nextStart}-${nextEnd}`,
      newAY: `${nextStart + 1}-${parseInt(nextEnd) + 1}`
    })
    setShowDuplicateModal(true)
  }

  const confirmDuplicate = async () => {
    try {
      const response = await api.post(
        `/admin/tax-rules/${selectedRule.financial_year}/duplicate`,
        null,
        { params: { new_financial_year: duplicateData.newFY, new_assessment_year: duplicateData.newAY } }
      )
      toast.success(response.data.message)
      setShowDuplicateModal(false)
      loadRules()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to duplicate rules')
    }
  }

  const handleDelete = async (fy) => {
    if (!confirm(`Are you sure you want to delete tax rules for FY ${fy}? This cannot be undone.`)) {
      return
    }
    
    try {
      await api.delete(`/admin/tax-rules/${fy}`)
      toast.success(`Tax rules for FY ${fy} deleted`)
      loadRules()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete rules')
    }
  }

  const toggleActive = async (fy, currentStatus) => {
    try {
      await api.put(`/admin/tax-rules/${fy}`, { is_active: !currentStatus })
      toast.success(`FY ${fy} is now ${!currentStatus ? 'active' : 'inactive'}`)
      loadRules()
    } catch (error) {
      toast.error('Failed to update status')
    }
  }

  const validateJson = (jsonStr) => {
    try {
      const parsed = JSON.parse(jsonStr)
      
      // Check required fields
      const required = ['cess', 'rebate_87A', 'surcharge_and_marginal_relief']
      const missing = required.filter(key => !parsed[key])
      
      if (missing.length > 0) {
        return `Missing required fields: ${missing.join(', ')}`
      }
      
      if (!parsed.slabs && !parsed.income_tax_slabs) {
        return "Missing tax slabs: must have either 'slabs' or 'income_tax_slabs'"
      }
      
      if (!parsed.deductions && !parsed.common_deductions_exemptions) {
        return "Missing deductions section"
      }
      
      return null
    } catch (e) {
      return `Invalid JSON: ${e.message}`
    }
  }

  const handleJsonChange = (value) => {
    setEditJson(value)
    setJsonError(validateJson(value))
  }

  const handleSave = async () => {
    const error = validateJson(editJson)
    if (error) {
      setJsonError(error)
      toast.error('Please fix JSON errors before saving')
      return
    }

    try {
      const rulesJson = JSON.parse(editJson)
      
      if (editorMode === 'create') {
        // Create new rule
        const fy = rulesJson.financial_year
        const ay = rulesJson.assessment_year
        
        if (!fy || !ay) {
          toast.error('financial_year and assessment_year are required in the JSON')
          return
        }
        
        await api.post('/admin/tax-rules', {
          financial_year: fy,
          assessment_year: ay,
          rules_json: rulesJson,
          is_active: true
        })
        toast.success(`Tax rules for FY ${fy} created successfully`)
      } else {
        // Update existing rule
        await api.put(`/admin/tax-rules/${selectedRule.financial_year}`, {
          rules_json: rulesJson
        })
        toast.success(`Tax rules for FY ${selectedRule.financial_year} updated`)
      }
      
      setShowEditor(false)
      loadRules()
    } catch (error) {
      const detail = error.response?.data?.detail
      if (typeof detail === 'object' && detail.errors) {
        toast.error(detail.errors.join(', '))
      } else {
        toast.error(detail || 'Failed to save rules')
      }
    }
  }

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const toggleRow = (fy) => {
    setExpandedRows(prev => ({ ...prev, [fy]: !prev[fy] }))
  }

  const downloadJson = () => {
    const blob = new Blob([editJson], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `tax_rules_${selectedRule?.financial_year || 'new'}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleFileUpload = (e) => {
    const file = e.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (event) => {
        const content = event.target.result
        handleJsonChange(content)
        toast.success('JSON file loaded')
      }
      reader.readAsText(file)
    }
  }

  if (!user?.is_admin) {
    return null
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-amber-100 rounded-xl">
                <Shield className="w-8 h-8 text-amber-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Tax Rules Management</h1>
                <p className="text-gray-500">Admin Panel - Manage tax rules for all financial years</p>
              </div>
            </div>
            <button
              onClick={handleCreate}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
              Add New FY Rules
            </button>
          </div>
        </div>

        {/* Instructions Card */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
          <h3 className="font-semibold text-blue-800 mb-2">How to Add New Financial Year Rules:</h3>
          <ol className="text-sm text-blue-700 space-y-1 list-decimal list-inside">
            <li>Visit <a href="https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable-1#taxdeductions" target="_blank" rel="noopener noreferrer" className="underline">Income Tax Department website</a> for official rules</li>
            <li>Click "Duplicate" on existing FY to use as template OR "Add New FY Rules"</li>
            <li>Update all values (slabs, deductions, rebate, surcharge) from official source</li>
            <li>Save and verify with test calculations</li>
          </ol>
        </div>

        {/* Rules Table */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Tax Rules</h2>
            <button
              onClick={loadRules}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
              title="Refresh"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-4 text-gray-500">Loading tax rules...</p>
            </div>
          ) : rules.length === 0 ? (
            <div className="p-12 text-center">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No tax rules found. Click "Add New FY Rules" to create.</p>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Financial Year</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Assessment Year</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cess</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Updated</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {rules.map((rule) => (
                  <tr key={rule.financial_year} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-semibold text-gray-900">FY {rule.financial_year}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-600">AY {rule.assessment_year}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => toggleActive(rule.financial_year, rule.is_active)}
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                          rule.is_active 
                            ? 'bg-green-100 text-green-800 hover:bg-green-200' 
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {rule.is_active ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
                        {rule.is_active ? 'Active' : 'Inactive'}
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-600">{rule.cess_percent}%</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-xs text-gray-500">{formatDate(rule.updated_at)}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => handleView(rule.financial_year)}
                          className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                          title="View"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleEdit(rule.financial_year)}
                          className="p-1.5 text-gray-500 hover:text-amber-600 hover:bg-amber-50 rounded"
                          title="Edit"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDuplicate(rule.financial_year)}
                          className="p-1.5 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded"
                          title="Duplicate for new FY"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(rule.financial_year)}
                          className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* JSON Editor Modal */}
        {showEditor && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl w-full max-w-5xl max-h-[90vh] flex flex-col">
              {/* Modal Header */}
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    {editorMode === 'create' 
                      ? 'Create New Tax Rules' 
                      : editorMode === 'edit' 
                        ? `Edit Tax Rules - FY ${selectedRule?.financial_year}`
                        : `View Tax Rules - FY ${selectedRule?.financial_year}`
                    }
                  </h2>
                  {template && editorMode === 'create' && (
                    <p className="text-sm text-gray-500 mt-1">Using template. Update all values from official source.</p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {editorMode !== 'view' && (
                    <label className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg cursor-pointer">
                      <Upload className="w-4 h-4" />
                      Import JSON
                      <input type="file" accept=".json" onChange={handleFileUpload} className="hidden" />
                    </label>
                  )}
                  <button
                    onClick={downloadJson}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
                  >
                    <Download className="w-4 h-4" />
                    Export
                  </button>
                  <button
                    onClick={() => setShowEditor(false)}
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Template Instructions */}
              {template && editorMode === 'create' && (
                <div className="px-6 py-3 bg-amber-50 border-b border-amber-200">
                  <h4 className="text-sm font-semibold text-amber-800 mb-1">Instructions:</h4>
                  <ul className="text-xs text-amber-700 space-y-0.5">
                    {template.instructions.slice(0, 5).map((inst, i) => (
                      <li key={i}>{inst}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* JSON Error Banner */}
              {jsonError && (
                <div className="px-6 py-3 bg-red-50 border-b border-red-200 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-500" />
                  <span className="text-sm text-red-700">{jsonError}</span>
                </div>
              )}

              {/* Editor Content */}
              <div className="flex-1 overflow-hidden p-6">
                <textarea
                  value={editJson}
                  onChange={(e) => handleJsonChange(e.target.value)}
                  disabled={editorMode === 'view'}
                  className={`w-full h-full font-mono text-sm p-4 border rounded-lg resize-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    editorMode === 'view' ? 'bg-gray-50 text-gray-600' : 'bg-white'
                  } ${jsonError ? 'border-red-300' : 'border-gray-300'}`}
                  placeholder="Enter tax rules JSON..."
                  spellCheck={false}
                />
              </div>

              {/* Modal Footer */}
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
                <button
                  onClick={() => setShowEditor(false)}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  {editorMode === 'view' ? 'Close' : 'Cancel'}
                </button>
                {editorMode !== 'view' && (
                  <button
                    onClick={handleSave}
                    disabled={!!jsonError}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <Check className="w-5 h-5" />
                    {editorMode === 'create' ? 'Create Rules' : 'Save Changes'}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Duplicate Modal */}
        {showDuplicateModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl w-full max-w-md p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Duplicate Tax Rules from FY {selectedRule?.financial_year}
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    New Financial Year (e.g., 2025-26)
                  </label>
                  <input
                    type="text"
                    value={duplicateData.newFY}
                    onChange={(e) => setDuplicateData(prev => ({ ...prev, newFY: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="2025-26"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    New Assessment Year (e.g., 2026-27)
                  </label>
                  <input
                    type="text"
                    value={duplicateData.newAY}
                    onChange={(e) => setDuplicateData(prev => ({ ...prev, newAY: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="2026-27"
                  />
                </div>
                <p className="text-sm text-amber-600 bg-amber-50 p-3 rounded-lg">
                  <AlertTriangle className="w-4 h-4 inline mr-1" />
                  Rules will be created as INACTIVE. Update values from official source before activating.
                </p>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowDuplicateModal(false)}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDuplicate}
                  disabled={!duplicateData.newFY || !duplicateData.newAY}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  <Copy className="w-5 h-5" />
                  Duplicate
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}

export default AdminTaxRules
