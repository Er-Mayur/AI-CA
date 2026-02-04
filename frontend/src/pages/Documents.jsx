import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { Upload, FileText, CheckCircle, XCircle, Trash2, AlertCircle, X, ChevronDown, ChevronUp } from 'lucide-react'

function Documents() {
  const { currentFY } = useAuth()
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadForm, setUploadForm] = useState({
    doc_type: 'Form 16',
    file: null
  })
  const [errorDetails, setErrorDetails] = useState(null)
  const [showErrorModal, setShowErrorModal] = useState(false)
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false)

  useEffect(() => {
    if (currentFY) {
      fetchDocuments()
    }
  }, [currentFY])

  const fetchDocuments = async () => {
    try {
      const response = await api.get(`/documents/list/${currentFY}`)
      setDocuments(response.data)
    } catch (error) {
      toast.error('Failed to fetch documents')
    } finally {
      setLoading(false)
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file && file.type === 'application/pdf') {
      setUploadForm({ ...uploadForm, file })
    } else {
      toast.error('Please select a PDF file')
    }
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    
    if (!uploadForm.file) {
      toast.error('Please select a file')
      return
    }

    setUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', uploadForm.file)
      formData.append('financial_year', currentFY)
      formData.append('doc_type', uploadForm.doc_type)

      const response = await api.post('/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      toast.success('Document uploaded and verified successfully!')
      setUploadForm({ ...uploadForm, file: null })
      document.getElementById('file-input').value = ''
      setErrorDetails(null)
      setShowErrorModal(false)
      setShowTechnicalDetails(false)
      fetchDocuments()
    } catch (error) {
      // Handle verification errors with detailed messages
      const errorDetail = error.response?.data?.detail || 'Upload failed'
      
      // Parse error message to extract structured information
      if (typeof errorDetail === 'string') {
        const lines = errorDetail.split('\n').filter(line => line.trim())
        
        if (lines.length > 1) {
          // Parse structured error message
          const mainError = lines[0] || 'Verification failed'
          const reasons = lines.filter(line => line.trim().startsWith('[REASON]'))
          const actions = lines.filter(line => line.trim().startsWith('[ACTION]'))
          const solutions = lines.filter(line => line.trim().startsWith('[SOLUTION]'))
          
          // Determine error type from main error message
          let errorType = 'general'
          if (mainError.includes('PAN')) {
            errorType = 'pan'
          } else if (mainError.includes('Financial Year') || mainError.includes('FY')) {
            errorType = 'financial_year'
          } else if (mainError.includes('Document Type') || mainError.includes('doc_type')) {
            errorType = 'document_type'
          }
          
          // Store error details for display
          setErrorDetails({
            mainError,
            reasons,
            actions,
            solutions,
            errorType,
            fullMessage: errorDetail
          })
          setShowErrorModal(true)
          
          // Show main error in toast
          toast.error(mainError, {
            duration: 6000,
          })
        } else {
          // Simple error message
          toast.error(errorDetail)
        }
        
        // Log full error for debugging
        console.error('Verification Error:', errorDetail)
      } else {
        toast.error(errorDetail)
      }
    } finally {
      setUploading(false)
    }
  }
  
  const closeErrorModal = () => {
    setErrorDetails(null)
    setShowErrorModal(false)
    setShowTechnicalDetails(false)
  }

  const handleDelete = async (documentId) => {
    if (!confirm('Are you sure you want to delete this document?')) {
      return
    }

    try {
      await api.delete(`/documents/${documentId}`)
      toast.success('Document deleted')
      fetchDocuments()
    } catch (error) {
      toast.error('Failed to delete document')
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Documents</h1>
          <p className="text-gray-600 mt-1">Upload and manage your tax documents for FY {currentFY}</p>
        </div>

        {/* Error Details Modal */}
        {errorDetails && showErrorModal && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
            onClick={closeErrorModal}
          >
            <div 
              className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <XCircle className="w-6 h-6 text-red-600" />
                    <h3 className="text-xl font-bold text-gray-900">Verification Failed</h3>
                  </div>
                  <button
                    onClick={closeErrorModal}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>
                
                <div className="space-y-4">
                  {/* Main Error */}
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <p className="text-red-800 font-semibold">{errorDetails.mainError}</p>
                  </div>
                  
                  {/* Reasons */}
                  {errorDetails.reasons.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Reasons:</h4>
                      <ul className="space-y-2">
                        {errorDetails.reasons.map((reason, idx) => (
                          <li key={idx} className="flex items-start space-x-2 text-sm text-gray-600">
                            <AlertCircle className="w-5 h-5 text-orange-500 mt-0.5 flex-shrink-0" />
                            <span>{reason.replace('[REASON]', '').trim()}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {/* Actions */}
                  {errorDetails.actions.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">What to do:</h4>
                      <ul className="space-y-2">
                        {errorDetails.actions.map((action, idx) => (
                          <li key={idx} className="flex items-start space-x-2 text-sm text-gray-600">
                            <ChevronDown className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                            <span>{action.replace('[ACTION]', '').trim()}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {/* Solutions */}
                  {errorDetails.solutions.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Solutions:</h4>
                      <ul className="space-y-2">
                        {errorDetails.solutions.map((solution, idx) => (
                          <li key={idx} className="flex items-start space-x-2 text-sm text-gray-600">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                            <span>{solution.replace('[SOLUTION]', '').trim()}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {/* Full Error Details (Collapsible) */}
                  <div className="border-t pt-4 mt-4">
                    <button
                      onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                      className="flex items-center justify-between w-full text-sm text-gray-600 hover:text-gray-800"
                    >
                      <span>Technical Details</span>
                      {showTechnicalDetails ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </button>
                    {showTechnicalDetails && (
                      <pre className="mt-2 text-xs bg-gray-50 p-3 rounded overflow-x-auto">
                        {errorDetails.fullMessage}
                      </pre>
                    )}
                  </div>
                </div>
                
                <div className="mt-6 flex justify-end">
                  <button
                    onClick={closeErrorModal}
                    className="btn-primary"
                  >
                    Understood
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Upload Form */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Upload Document</h2>
          <form onSubmit={handleUpload} className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Document Type *
                </label>
                <select
                  value={uploadForm.doc_type}
                  onChange={(e) => setUploadForm({ ...uploadForm, doc_type: e.target.value })}
                  className="input-field"
                  required
                >
                  <option value="Form 16">Form 16</option>
                  <option value="Form 26AS">Form 26AS</option>
                  <option value="AIS">AIS (Annual Information Statement)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select PDF File *
                </label>
                <input
                  id="file-input"
                  type="file"
                  accept="application/pdf"
                  onChange={handleFileChange}
                  className="input-field"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={uploading}
              className="btn-primary flex items-center space-x-2"
            >
              {uploading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  <span>Upload Document</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Documents List */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Uploaded Documents</h2>
          
          {documents.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No documents uploaded yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {documents.map((doc) => (
                <div key={doc.id} className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      <FileText className="w-10 h-10 text-primary-600 mt-1" />
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">{doc.doc_type}</h3>
                        <p className="text-sm text-gray-600 mt-1">
                          Uploaded: {new Date(doc.uploaded_at).toLocaleDateString()}
                        </p>
                        
                        <div className="mt-2 flex items-center space-x-2">
                          {doc.verification_status === 'verified' ? (
                            <>
                              <CheckCircle className="w-5 h-5 text-green-600" />
                              <span className="text-sm text-green-600 font-medium">Verified</span>
                            </>
                          ) : doc.verification_status === 'failed' ? (
                            <>
                              <XCircle className="w-5 h-5 text-red-600" />
                              <span className="text-sm text-red-600 font-medium">Verification Failed</span>
                            </>
                          ) : (
                            <>
                              <AlertCircle className="w-5 h-5 text-yellow-600" />
                              <span className="text-sm text-yellow-600 font-medium">Pending Verification</span>
                            </>
                          )}
                        </div>
                        
                        {doc.verification_message && (
                          <p className="text-sm text-gray-600 mt-2 bg-gray-50 p-2 rounded">
                            {doc.verification_message}
                          </p>
                        )}
                      </div>
                    </div>
                    
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-6 h-6 text-blue-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-gray-900">Important Information</h3>
              <ul className="mt-2 space-y-1 text-sm text-gray-600">
                <li>• Only PDF files are accepted</li>
                <li>• Your name and PAN must match the uploaded documents</li>
                <li>• Documents are automatically verified after upload</li>
                <li>• You can replace documents by uploading a new file of the same type</li>
                <li>• All documents are required for accurate tax calculation</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}

export default Documents

