import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// New function for uploading documents with polling
export const uploadDocumentWithPolling = async (file, financialYear, docType, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('financial_year', financialYear);
  formData.append('doc_type', docType);

  // 1. Initial upload request
  const initialResponse = await api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  const documentId = initialResponse.data.id;
  onProgress({ status: 'UPLOADING', message: 'File uploaded, starting verification...', documentId });

  // 2. Polling for status
  return new Promise((resolve, reject) => {
    const interval = setInterval(async () => {
      try {
        const statusResponse = await api.get(`/documents/status/${documentId}`);
        const { processing_status, verification_message } = statusResponse.data;

        onProgress({ status: processing_status, message: verification_message });

        if (processing_status === 'SUCCESS') {
          clearInterval(interval);
          // Fetch the final document data
          const finalDocument = await api.get(`/documents/${documentId}`);
          resolve(finalDocument.data);
        } else if (processing_status === 'FAILED') {
          clearInterval(interval);
          reject(new Error(verification_message || 'Document processing failed.'));
        }
      } catch (error) {
        clearInterval(interval);
        reject(error);
      }
    }, 3000); // Poll every 3 seconds
  });
};

export default api

