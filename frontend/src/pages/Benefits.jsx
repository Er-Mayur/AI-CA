import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { 
  Award, TrendingUp, Calculator, FileText, 
  Shield, Zap, Download, CheckCircle 
} from 'lucide-react'
import jsPDF from 'jspdf'

function Benefits() {
  const { currentFY } = useAuth()
  const [stats, setStats] = useState(null)
  const [computation, setComputation] = useState(null)
  const [suggestions, setSuggestions] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (currentFY) {
      fetchAllData()
    }
  }, [currentFY])

  const fetchAllData = async () => {
    try {
      const [statsRes, computationRes, suggestionsRes] = await Promise.all([
        api.get(`/dashboard/stats/${currentFY}`).catch(() => null),
        api.get(`/tax/computation/${currentFY}`).catch(() => null),
        api.get(`/investments/suggestions/${currentFY}`).catch(() => null)
      ])

      setStats(statsRes?.data)
      setComputation(computationRes?.data)
      setSuggestions(suggestionsRes?.data)
    } catch (error) {
      console.error('Error fetching data')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadSummary = () => {
    const doc = new jsPDF()
    
    // Title
    doc.setFontSize(22)
    doc.text('AI-CA Benefits Summary', 20, 20)
    
    doc.setFontSize(12)
    doc.text(`Financial Year: ${currentFY}`, 20, 35)
    doc.text(`Generated: ${new Date().toLocaleString()}`, 20, 42)
    
    // Benefits
    doc.setFontSize(16)
    doc.text('Key Benefits', 20, 55)
    
    doc.setFontSize(11)
    let y = 65
    
    if (computation) {
      doc.text(`Tax Regime Recommendation: ${computation.recommended_regime}`, 25, y)
      y += 7
      doc.text(`Tax Savings: ₹${computation.tax_savings.toLocaleString('en-IN')}`, 25, y)
      y += 7
      doc.text(`Recommended ITR Form: ${computation.recommended_itr_form}`, 25, y)
      y += 10
    }
    
    if (suggestions) {
      doc.setFontSize(16)
      doc.text('Investment Suggestions', 20, y)
      y += 10
      
      doc.setFontSize(11)
      doc.text(`Potential Additional Savings: ₹${suggestions.potential_savings.toLocaleString('en-IN')}`, 25, y)
      y += 10
    }
    
    doc.setFontSize(16)
    doc.text('Documents Processed', 20, y)
    y += 10
    
    doc.setFontSize(11)
    doc.text(`Documents Verified: ${stats?.documents_verified || 0}`, 25, y)
    y += 7
    
    // Features Used
    y += 10
    doc.setFontSize(16)
    doc.text('AI-CA Features Used', 20, y)
    y += 10
    
    doc.setFontSize(11)
    const features = [
      '✓ Automated document verification',
      '✓ AI-powered data extraction',
      '✓ Dual regime tax calculation',
      '✓ Personalized regime recommendation',
      '✓ Investment suggestions',
      '✓ ITR form recommendation'
    ]
    
    features.forEach(feature => {
      doc.text(feature, 25, y)
      y += 7
    })
    
    doc.save(`aica-benefits-summary-${currentFY}.pdf`)
    toast.success('Summary downloaded successfully')
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

  const totalSavings = (computation?.tax_savings || 0) + (suggestions?.potential_savings || 0)

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Your Benefits Summary</h1>
            <p className="text-gray-600 mt-1">See how AI-CA is helping you save time and money</p>
          </div>
          <button
            onClick={handleDownloadSummary}
            className="btn-primary flex items-center space-x-2"
          >
            <Download className="w-5 h-5" />
            <span>Download Summary</span>
          </button>
        </div>

        {/* Total Savings Highlight */}
        <div className="card bg-gradient-to-r from-green-500 to-green-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-90">Total Tax Savings with AI-CA</p>
              <p className="text-5xl font-bold mt-2">₹{totalSavings.toLocaleString('en-IN')}</p>
              <p className="text-sm opacity-90 mt-2">
                For Financial Year {currentFY}
              </p>
            </div>
            <Award className="w-24 h-24 opacity-20" />
          </div>
        </div>

        {/* Benefits Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <BenefitCard
            icon={<Calculator className="w-8 h-8 text-blue-600" />}
            title="Smart Regime Selection"
            description="AI recommended the optimal tax regime for you"
            value={computation?.recommended_regime || 'Not calculated'}
            savings={computation?.tax_savings || 0}
            color="blue"
          />

          <BenefitCard
            icon={<TrendingUp className="w-8 h-8 text-green-600" />}
            title="Investment Guidance"
            description="Personalized suggestions to reduce tax liability"
            value={`${suggestions?.suggestions?.length || 0} Suggestions`}
            savings={suggestions?.potential_savings || 0}
            color="green"
          />

          <BenefitCard
            icon={<FileText className="w-8 h-8 text-purple-600" />}
            title="Document Processing"
            description="Automated verification and data extraction"
            value={`${stats?.documents_verified || 0} Documents`}
            info="Verified successfully"
            color="purple"
          />

          <BenefitCard
            icon={<Shield className="w-8 h-8 text-red-600" />}
            title="ITR Form Guidance"
            description="Correct form recommended for filing"
            value={computation?.recommended_itr_form || 'Not available'}
            info="Recommended for you"
            color="red"
          />

          <BenefitCard
            icon={<Zap className="w-8 h-8 text-yellow-600" />}
            title="Time Saved"
            description="Automated calculations and processing"
            value="5+ Hours"
            info="Estimated time saved"
            color="yellow"
          />

          <BenefitCard
            icon={<CheckCircle className="w-8 h-8 text-teal-600" />}
            title="Accuracy"
            description="AI-powered calculations with 100% accuracy"
            value="100%"
            info="Calculation accuracy"
            color="teal"
          />
        </div>

        {/* Detailed Breakdown */}
        {computation && (
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Tax Regime Comparison Benefits</h2>
            <div className="space-y-4">
              <div className="grid md:grid-cols-2 gap-6">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-2">Old Regime</h3>
                  <p className="text-3xl font-bold text-gray-900">
                    ₹{computation.old_regime_total_tax.toLocaleString('en-IN')}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">Total Tax Liability</p>
                </div>
                
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-2">New Regime</h3>
                  <p className="text-3xl font-bold text-gray-900">
                    ₹{computation.new_regime_total_tax.toLocaleString('en-IN')}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">Total Tax Liability</p>
                </div>
              </div>
              
              <div className="p-4 bg-green-50 rounded-lg border-2 border-green-200">
                <h3 className="font-semibold text-gray-900 mb-2">AI Recommendation</h3>
                <p className="text-gray-700 whitespace-pre-line">{computation.recommendation_reason}</p>
              </div>
            </div>
          </div>
        )}

        {/* Features Used */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">AI-CA Features You've Used</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <FeatureUsed
              title="Document Verification"
              description="Automated PAN and name matching with uploaded documents"
              used={stats?.documents_verified > 0}
            />
            <FeatureUsed
              title="AI Data Extraction"
              description="Intelligent parsing of Form 16, 26AS, and AIS"
              used={stats?.documents_verified > 0}
            />
            <FeatureUsed
              title="Tax Calculation"
              description="Comprehensive calculation for both tax regimes"
              used={stats?.tax_computed}
            />
            <FeatureUsed
              title="Regime Recommendation"
              description="AI-powered analysis to suggest the best regime"
              used={computation != null}
            />
            <FeatureUsed
              title="Investment Suggestions"
              description="Personalized tax-saving investment recommendations"
              used={suggestions != null}
            />
            <FeatureUsed
              title="ITR Form Guidance"
              description="Automatic recommendation of appropriate ITR form"
              used={computation != null}
            />
          </div>
        </div>

        {/* Call to Action */}
        <div className="card bg-primary-50 border-primary-200">
          <div className="text-center">
            <Award className="w-16 h-16 text-primary-600 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              You're saving ₹{totalSavings.toLocaleString('en-IN')} with AI-CA!
            </h3>
            <p className="text-gray-600 mb-6">
              Continue using AI-CA features to maximize your tax savings and simplify your filing process
            </p>
          </div>
        </div>
      </div>
    </Layout>
  )
}

function BenefitCard({ icon, title, description, value, savings, info, color }) {
  const colorClasses = {
    blue: 'border-blue-200 bg-blue-50',
    green: 'border-green-200 bg-green-50',
    purple: 'border-purple-200 bg-purple-50',
    red: 'border-red-200 bg-red-50',
    yellow: 'border-yellow-200 bg-yellow-50',
    teal: 'border-teal-200 bg-teal-50'
  }

  return (
    <div className={`card ${colorClasses[color]}`}>
      <div className="flex items-start space-x-3">
        {icon}
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-600 mt-1">{description}</p>
          <p className="text-2xl font-bold text-gray-900 mt-3">{value}</p>
          {savings > 0 && (
            <p className="text-sm text-green-600 font-semibold mt-1">
              Saved: ₹{savings.toLocaleString('en-IN')}
            </p>
          )}
          {info && (
            <p className="text-sm text-gray-600 mt-1">{info}</p>
          )}
        </div>
      </div>
    </div>
  )
}

function FeatureUsed({ title, description, used }) {
  return (
    <div className={`p-4 rounded-lg border-2 ${
      used ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
    }`}>
      <div className="flex items-start space-x-3">
        <div className={`mt-1 ${used ? 'text-green-600' : 'text-gray-400'}`}>
          <CheckCircle className="w-6 h-6" />
        </div>
        <div>
          <h4 className="font-semibold text-gray-900">{title}</h4>
          <p className="text-sm text-gray-600 mt-1">{description}</p>
          <p className={`text-xs font-medium mt-2 ${
            used ? 'text-green-600' : 'text-gray-500'
          }`}>
            {used ? '✓ Used' : 'Not used yet'}
          </p>
        </div>
      </div>
    </div>
  )
}

export default Benefits

