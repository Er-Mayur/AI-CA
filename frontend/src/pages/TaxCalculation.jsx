import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { Calculator, TrendingUp, Download, FileText, Info } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import jsPDF from 'jspdf'

function TaxCalculation() {
  const { currentFY } = useAuth()
  const [computation, setComputation] = useState(null)
  const [loading, setLoading] = useState(true)
  const [calculating, setCalculating] = useState(false)

  useEffect(() => {
    if (currentFY) {
      fetchComputation()
    }
  }, [currentFY])

  const fetchComputation = async () => {
    try {
      const response = await api.get(`/tax/computation/${currentFY}`)
      setComputation(response.data)
    } catch (error) {
      // Computation doesn't exist yet
    } finally {
      setLoading(false)
    }
  }

  const handleCalculate = async () => {
    setCalculating(true)
    try {
      const response = await api.post(`/tax/calculate/${currentFY}`)
      setComputation(response.data)
      toast.success('Tax calculated successfully!')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Calculation failed')
    } finally {
      setCalculating(false)
    }
  }

  const handleDownloadPDF = () => {
    if (!computation) return

    const doc = new jsPDF()
    
    // Title
    doc.setFontSize(20)
    doc.text('Tax Computation Report', 20, 20)
    
    doc.setFontSize(12)
    doc.text(`Financial Year: ${computation.financial_year}`, 20, 35)
    doc.text(`Assessment Year: ${computation.assessment_year}`, 20, 42)
    
    // Income Details
    doc.setFontSize(14)
    doc.text('Income Details', 20, 55)
    doc.setFontSize(11)
    doc.text(`Gross Total Income: ₹${computation.gross_total_income.toLocaleString('en-IN')}`, 25, 65)
    doc.text(`Salary Income: ₹${computation.salary_income.toLocaleString('en-IN')}`, 25, 72)
    
    // Old Regime
    doc.setFontSize(14)
    doc.text('Old Regime', 20, 85)
    doc.setFontSize(11)
    doc.text(`Taxable Income: ₹${computation.old_regime_taxable_income.toLocaleString('en-IN')}`, 25, 95)
    doc.text(`Total Tax: ₹${computation.old_regime_total_tax.toLocaleString('en-IN')}`, 25, 102)
    
    // New Regime
    doc.setFontSize(14)
    doc.text('New Regime', 20, 115)
    doc.setFontSize(11)
    doc.text(`Taxable Income: ₹${computation.new_regime_taxable_income.toLocaleString('en-IN')}`, 25, 125)
    doc.text(`Total Tax: ₹${computation.new_regime_total_tax.toLocaleString('en-IN')}`, 25, 132)
    
    // Recommendation
    doc.setFontSize(14)
    doc.text('Recommendation', 20, 145)
    doc.setFontSize(11)
    doc.text(`Recommended Regime: ${computation.recommended_regime}`, 25, 155)
    doc.text(`Tax Savings: ₹${computation.tax_savings.toLocaleString('en-IN')}`, 25, 162)
    doc.text(`Recommended ITR Form: ${computation.recommended_itr_form}`, 25, 169)
    
    // Final Tax
    doc.setFontSize(14)
    doc.text('Final Tax Liability', 20, 182)
    doc.setFontSize(11)
    doc.text(`Total TDS: ₹${computation.total_tds.toLocaleString('en-IN')}`, 25, 192)
    doc.text(`Tax Payable: ₹${computation.tax_payable.toLocaleString('en-IN')}`, 25, 199)
    doc.text(`Refund Amount: ₹${computation.refund_amount.toLocaleString('en-IN')}`, 25, 206)
    
    doc.save(`tax-computation-${currentFY}.pdf`)
    toast.success('PDF downloaded successfully')
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

  const chartData = computation ? [
    {
      name: 'Old Regime',
      'Taxable Income': computation.old_regime_taxable_income,
      'Total Tax': computation.old_regime_total_tax
    },
    {
      name: 'New Regime',
      'Taxable Income': computation.new_regime_taxable_income,
      'Total Tax': computation.new_regime_total_tax
    }
  ] : []

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Tax Calculation</h1>
            <p className="text-gray-600 mt-1">Financial Year {currentFY}</p>
          </div>
          {computation && (
            <button
              onClick={handleDownloadPDF}
              className="btn-primary flex items-center space-x-2"
            >
              <Download className="w-5 h-5" />
              <span>Download PDF</span>
            </button>
          )}
        </div>

        {/* Calculate Button */}
        {!computation && (
          <div className="card text-center py-12">
            <Calculator className="w-16 h-16 text-primary-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Calculate Your Taxes</h2>
            <p className="text-gray-600 mb-6">
              Make sure you have uploaded all required documents before calculating
            </p>
            <button
              onClick={handleCalculate}
              disabled={calculating}
              className="btn-primary flex items-center space-x-2 mx-auto"
            >
              {calculating ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <>
                  <Calculator className="w-5 h-5" />
                  <span>Calculate Tax</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Computation Results */}
        {computation && (
          <>
            {/* Regime Comparison Chart */}
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Regime Comparison</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
                  <Legend />
                  <Bar dataKey="Taxable Income" fill="#0ea5e9" />
                  <Bar dataKey="Total Tax" fill="#f59e0b" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Recommendation */}
            <div className="card bg-green-50 border-green-200">
              <div className="flex items-start space-x-4">
                <TrendingUp className="w-8 h-8 text-green-600 mt-1" />
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-900">Recommended: {computation.recommended_regime}</h3>
                  <p className="text-gray-700 mt-2 whitespace-pre-line">{computation.recommendation_reason}</p>
                  <div className="mt-4 p-4 bg-white rounded-lg">
                    <p className="font-semibold text-gray-900">Recommended ITR Form: {computation.recommended_itr_form}</p>
                    <p className="text-sm text-gray-600 mt-1">Use this form when filing your income tax return</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Income Details */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="card">
                <h3 className="text-lg font-semibold mb-4">Income Breakdown</h3>
                <div className="space-y-3">
                  <DetailRow label="Gross Total Income" value={computation.gross_total_income} />
                  <DetailRow label="Salary Income" value={computation.salary_income} />
                  <DetailRow label="House Property" value={computation.house_property_income} />
                  <DetailRow label="Capital Gains" value={computation.capital_gains} />
                  <DetailRow label="Other Income" value={computation.other_income} />
                </div>
              </div>

              <div className="card">
                <h3 className="text-lg font-semibold mb-4">Tax Summary</h3>
                <div className="space-y-3">
                  <DetailRow label="Total TDS" value={computation.total_tds} />
                  <DetailRow label="Tax Payable" value={computation.tax_payable} highlight={computation.tax_payable > 0} />
                  <DetailRow label="Refund Amount" value={computation.refund_amount} highlight={computation.refund_amount > 0} success />
                  <DetailRow label="Tax Savings" value={computation.tax_savings} success />
                </div>
              </div>
            </div>

            {/* Detailed Computation */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Old Regime */}
              <div className="card">
                <h3 className="text-lg font-semibold mb-4">Old Regime Calculation</h3>
                <div className="space-y-2 text-sm">
                  <DetailRow label="Total Deductions" value={computation.old_regime_total_deductions} small />
                  <DetailRow label="Taxable Income" value={computation.old_regime_taxable_income} small />
                  <DetailRow label="Tax Before Rebate" value={computation.old_regime_tax_before_rebate} small />
                  <DetailRow label="Rebate u/s 87A" value={computation.old_regime_rebate} small success />
                  <DetailRow label="Tax After Rebate" value={computation.old_regime_tax_after_rebate} small />
                  <DetailRow label="Surcharge" value={computation.old_regime_surcharge} small />
                  <DetailRow label="Health & Education Cess" value={computation.old_regime_cess} small />
                  <DetailRow label="Total Tax" value={computation.old_regime_total_tax} small bold />
                </div>
              </div>

              {/* New Regime */}
              <div className="card">
                <h3 className="text-lg font-semibold mb-4">New Regime Calculation</h3>
                <div className="space-y-2 text-sm">
                  <DetailRow label="Total Deductions" value={computation.new_regime_total_deductions} small />
                  <DetailRow label="Taxable Income" value={computation.new_regime_taxable_income} small />
                  <DetailRow label="Tax Before Rebate" value={computation.new_regime_tax_before_rebate} small />
                  <DetailRow label="Rebate u/s 87A" value={computation.new_regime_rebate} small success />
                  <DetailRow label="Tax After Rebate" value={computation.new_regime_tax_after_rebate} small />
                  <DetailRow label="Surcharge" value={computation.new_regime_surcharge} small />
                  <DetailRow label="Health & Education Cess" value={computation.new_regime_cess} small />
                  <DetailRow label="Total Tax" value={computation.new_regime_total_tax} small bold />
                </div>
              </div>
            </div>

            {/* Recalculate Button */}
            <div className="text-center">
              <button
                onClick={handleCalculate}
                disabled={calculating}
                className="btn-secondary flex items-center space-x-2 mx-auto"
              >
                {calculating ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-600"></div>
                ) : (
                  <>
                    <Calculator className="w-5 h-5" />
                    <span>Recalculate</span>
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

function DetailRow({ label, value, highlight, success, small, bold }) {
  const formattedValue = `₹${value.toLocaleString('en-IN')}`
  
  return (
    <div className={`flex justify-between items-center pb-2 border-b border-gray-100 ${small ? '' : 'py-1'}`}>
      <span className={`text-gray-600 ${bold ? 'font-semibold' : ''}`}>{label}</span>
      <span className={`${
        success ? 'text-green-600 font-semibold' :
        highlight ? 'text-red-600 font-semibold' :
        bold ? 'font-bold text-gray-900' : 'text-gray-900'
      }`}>
        {formattedValue}
      </span>
    </div>
  )
}

export default TaxCalculation

