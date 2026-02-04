import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { TrendingUp, Lightbulb, DollarSign, Shield, ArrowRight } from 'lucide-react'

function Investments() {
  const { currentFY } = useAuth()
  const [suggestions, setSuggestions] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    if (currentFY) {
      fetchSuggestions()
    }
  }, [currentFY])

  const fetchSuggestions = async () => {
    try {
      const response = await api.get(`/investments/suggestions/${currentFY}`)
      setSuggestions(response.data)
    } catch (error) {
      // Suggestions don't exist yet
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      const response = await api.post(`/investments/suggest/${currentFY}`)
      setSuggestions(response.data)
      toast.success('Investment suggestions generated!')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate suggestions')
    } finally {
      setGenerating(false)
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
          <h1 className="text-3xl font-bold text-gray-900">Investment Suggestions</h1>
          <p className="text-gray-600 mt-1">AI-powered recommendations to minimize your tax liability</p>
        </div>

        {/* Generate Button */}
        {!suggestions && (
          <div className="card text-center py-12">
            <Lightbulb className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Get Personalized Investment Suggestions</h2>
            <p className="text-gray-600 mb-6">
              Our AI will analyze your income and current deductions to recommend tax-saving investments
            </p>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="btn-primary flex items-center space-x-2 mx-auto"
            >
              {generating ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <>
                  <TrendingUp className="w-5 h-5" />
                  <span>Generate Suggestions</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Suggestions */}
        {suggestions && (
          <>
            {/* Potential Savings */}
            <div className="card bg-green-50 border-green-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Potential Tax Savings</h3>
                  <p className="text-3xl font-bold text-green-600 mt-2">
                    ₹{suggestions.potential_savings.toLocaleString('en-IN')}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    By implementing these investment suggestions
                  </p>
                </div>
                <DollarSign className="w-16 h-16 text-green-600" />
              </div>
            </div>

            {/* Suggestions List */}
            <div className="space-y-4">
              {suggestions.suggestions.map((suggestion, index) => (
                <InvestmentCard key={index} suggestion={suggestion} index={index} />
              ))}
            </div>

            {/* Disclaimer */}
            <div className="card bg-yellow-50 border-yellow-200">
              <div className="flex items-start space-x-3">
                <Shield className="w-6 h-6 text-yellow-600 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-gray-900">Important Disclaimer</h3>
                  <p className="text-sm text-gray-600 mt-2">
                    These are AI-generated suggestions based on your tax profile. Please consult with a 
                    qualified financial advisor or chartered accountant before making any investment decisions. 
                    Past performance is not indicative of future results. Investment in securities market 
                    is subject to market risks.
                  </p>
                </div>
              </div>
            </div>

            {/* Regenerate Button */}
            <div className="text-center">
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="btn-secondary flex items-center space-x-2 mx-auto"
              >
                {generating ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-600"></div>
                ) : (
                  <>
                    <TrendingUp className="w-5 h-5" />
                    <span>Regenerate Suggestions</span>
                  </>
                )}
              </button>
            </div>
          </>
        )}
      </div>
    </Layout>
  )
}

function InvestmentCard({ suggestion, index }) {
  const riskColors = {
    'Low': 'bg-green-100 text-green-800',
    'Medium': 'bg-yellow-100 text-yellow-800',
    'High': 'bg-red-100 text-red-800',
    'Low to Medium': 'bg-blue-100 text-blue-800'
  }

  return (
    <div className="card hover:shadow-lg transition-shadow">
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0 w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
          <span className="text-xl font-bold text-primary-600">{index + 1}</span>
        </div>
        
        <div className="flex-1">
          <div className="flex items-start justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              {suggestion.investment_type || suggestion.type}
            </h3>
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
              riskColors[suggestion.risk_level || 'Medium']
            }`}>
              {suggestion.risk_level || 'Medium'} Risk
            </span>
          </div>
          
          <p className="text-gray-600 mt-2">
            {suggestion.explanation || suggestion.description}
          </p>
          
          <div className="grid md:grid-cols-2 gap-4 mt-4">
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-sm text-gray-600">Recommended Amount</p>
              <p className="text-xl font-bold text-gray-900">
                ₹{(suggestion.recommended_amount || suggestion.amount || 0).toLocaleString('en-IN')}
              </p>
            </div>
            
            <div className="bg-green-50 p-3 rounded-lg">
              <p className="text-sm text-gray-600">Potential Tax Savings</p>
              <p className="text-xl font-bold text-green-600">
                ₹{(suggestion.potential_tax_savings || suggestion.savings || 0).toLocaleString('en-IN')}
              </p>
            </div>
          </div>
          
          <div className="mt-4 flex items-center text-primary-600 hover:text-primary-700 cursor-pointer">
            <span className="text-sm font-medium">Learn more about this investment</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </div>
        </div>
      </div>
    </div>
  )
}

export default Investments

