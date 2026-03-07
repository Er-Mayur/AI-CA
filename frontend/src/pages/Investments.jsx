import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { 
  TrendingUp, Lightbulb, DollarSign, Shield, ArrowRight, 
  PiggyBank, Heart, Building, BookOpen, CheckCircle, Clock,
  Target, Percent, ChevronDown, ChevronUp
} from 'lucide-react'

function Investments() {
  const { currentFY } = useAuth()
  const [suggestions, setSuggestions] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [expandedCard, setExpandedCard] = useState(null)

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
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Investment Suggestions</h1>
            <p className="text-gray-600 mt-1">AI-powered recommendations to minimize your tax liability</p>
          </div>
          {suggestions && (
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="btn-secondary flex items-center space-x-2"
            >
              {generating ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-600"></div>
              ) : (
                <>
                  <TrendingUp className="w-5 h-5" />
                  <span>Regenerate</span>
                </>
              )}
            </button>
          )}
        </div>

        {/* Generate Button - No suggestions yet */}
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
            {/* Summary Cards */}
            <div className="grid md:grid-cols-3 gap-4">
              {/* Potential Savings */}
              <div className="card bg-gradient-to-br from-green-50 to-green-100 border-green-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-green-700 font-medium">Potential Tax Savings</p>
                    <p className="text-2xl font-bold text-green-600 mt-1">
                      ₹{(suggestions.potential_savings || 0).toLocaleString('en-IN')}
                    </p>
                  </div>
                  <DollarSign className="w-10 h-10 text-green-500" />
                </div>
              </div>

              {/* Current Taxable Income */}
              <div className="card bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-blue-700 font-medium">Taxable Income</p>
                    <p className="text-2xl font-bold text-blue-600 mt-1">
                      ₹{(suggestions.taxable_income || 0).toLocaleString('en-IN')}
                    </p>
                  </div>
                  <Target className="w-10 h-10 text-blue-500" />
                </div>
              </div>

              {/* Tax Rate */}
              <div className="card bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-purple-700 font-medium">Tax Rate (incl. cess)</p>
                    <p className="text-2xl font-bold text-purple-600 mt-1">
                      {((suggestions.tax_rate || 0) * 100).toFixed(1)}%
                    </p>
                  </div>
                  <Percent className="w-10 h-10 text-purple-500" />
                </div>
              </div>
            </div>

            {/* Deduction Limits Usage */}
            {suggestions.deduction_summary && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <PiggyBank className="w-5 h-5 mr-2 text-primary-600" />
                  Deduction Limits Utilization
                </h3>
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {Object.entries(suggestions.deduction_summary).map(([section, data]) => (
                    <DeductionProgress key={section} section={section} data={data} />
                  ))}
                </div>
              </div>
            )}

            {/* Suggestions List */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Recommended Investments</h3>
              {suggestions.suggestions && suggestions.suggestions.map((suggestion, index) => (
                <InvestmentCard 
                  key={index} 
                  suggestion={suggestion} 
                  index={index}
                  expanded={expandedCard === index}
                  onToggle={() => setExpandedCard(expandedCard === index ? null : index)}
                />
              ))}
            </div>

            {/* Disclaimer */}
            <div className="card bg-yellow-50 border-yellow-200">
              <div className="flex items-start space-x-3">
                <Shield className="w-6 h-6 text-yellow-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-gray-900">Important Disclaimer</h3>
                  <p className="text-sm text-gray-600 mt-2">
                    These are AI-generated suggestions based on your tax profile. Please consult with a 
                    qualified financial advisor or chartered accountant before making any investment decisions. 
                    Past performance is not indicative of future results. Investment in securities market 
                    is subject to market risks. Tax laws are subject to change.
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </Layout>
  )
}

function DeductionProgress({ section, data }) {
  const percentage = data.limit > 0 ? Math.min(100, (data.current / data.limit) * 100) : 0
  const remaining = data.remaining || 0
  
  const sectionNames = {
    '80C': 'Section 80C',
    '80CCD_1B': 'NPS (80CCD)',
    '80D': 'Health (80D)',
    '24b': 'Home Loan (24b)'
  }

  const getBarColor = () => {
    if (percentage >= 100) return 'bg-green-500'
    if (percentage >= 50) return 'bg-yellow-500'
    return 'bg-red-400'
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium text-gray-700">{sectionNames[section] || section}</span>
        <span className="text-xs text-gray-500">{percentage.toFixed(0)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
        <div 
          className={`h-2 rounded-full transition-all ${getBarColor()}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-gray-500">
        <span>₹{(data.current || 0).toLocaleString('en-IN')}</span>
        <span>Limit: ₹{(data.limit || 0).toLocaleString('en-IN')}</span>
      </div>
      {remaining > 0 && (
        <p className="text-xs text-green-600 mt-1 font-medium">
          ₹{remaining.toLocaleString('en-IN')} remaining
        </p>
      )}
    </div>
  )
}

function InvestmentCard({ suggestion, index, expanded, onToggle }) {
  const priorityColors = {
    'High': 'bg-red-100 text-red-800 border-red-200',
    'Medium': 'bg-yellow-100 text-yellow-800 border-yellow-200',
    'Low': 'bg-green-100 text-green-800 border-green-200'
  }

  const riskColors = {
    'Low': 'bg-green-100 text-green-800',
    'Medium': 'bg-yellow-100 text-yellow-800',
    'High': 'bg-red-100 text-red-800',
    'Low to Medium': 'bg-blue-100 text-blue-800'
  }

  const sectionIcons = {
    '80C': PiggyBank,
    '80CCD': Building,
    '80CCD(1B)': Building,
    '80D': Heart,
    '80E': BookOpen,
    '24b': Building
  }

  const IconComponent = sectionIcons[suggestion.section] || PiggyBank

  return (
    <div className="card hover:shadow-lg transition-all">
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0 w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
          <IconComponent className="w-6 h-6 text-primary-600" />
        </div>
        
        <div className="flex-1">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {suggestion.investment_type || suggestion.type}
              </h3>
              <div className="flex items-center space-x-2 mt-1 flex-wrap gap-1">
                <span className="px-2 py-0.5 bg-primary-100 text-primary-700 text-xs rounded-full font-medium">
                  {suggestion.section || '80C'}
                </span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                  priorityColors[suggestion.priority || 'Medium']
                }`}>
                  {suggestion.priority || 'Medium'} Priority
                </span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                  riskColors[suggestion.risk_level || 'Medium']
                }`}>
                  {suggestion.risk_level || 'Medium'} Risk
                </span>
              </div>
            </div>
            <button 
              onClick={onToggle}
              className="text-gray-400 hover:text-gray-600"
            >
              {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </button>
          </div>
          
          <p className="text-gray-600 mt-3">
            {suggestion.explanation || suggestion.description}
          </p>
          
          <div className="grid md:grid-cols-3 gap-4 mt-4">
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

            <div className="bg-blue-50 p-3 rounded-lg">
              <div className="flex items-center">
                <Clock className="w-4 h-4 text-blue-500 mr-1" />
                <p className="text-sm text-gray-600">Lock-in Period</p>
              </div>
              <p className="text-lg font-bold text-blue-600">
                {suggestion.lock_in_period || 'Varies'}
              </p>
            </div>
          </div>

          {/* Action Steps - Expandable */}
          {expanded && suggestion.action_steps && suggestion.action_steps.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                How to Invest
              </h4>
              <ul className="space-y-2">
                {suggestion.action_steps.map((step, i) => (
                  <li key={i} className="flex items-start">
                    <span className="flex-shrink-0 w-6 h-6 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-xs font-medium mr-3">
                      {i + 1}
                    </span>
                    <span className="text-sm text-gray-600">{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {!expanded && (
            <button 
              onClick={onToggle}
              className="mt-4 flex items-center text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              <span>View action steps</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default Investments

