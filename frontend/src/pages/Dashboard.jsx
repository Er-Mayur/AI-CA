import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { 
  FileText, CheckCircle, XCircle, Calculator, 
  TrendingUp, TrendingDown, Calendar, Activity 
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

function Dashboard() {
  const { currentFY } = useAuth()
  const [stats, setStats] = useState(null)
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (currentFY) {
      fetchDashboardData()
    }
  }, [currentFY])

  const fetchDashboardData = async () => {
    try {
      const [statsRes, activitiesRes] = await Promise.all([
        api.get(`/dashboard/stats/${currentFY}`),
        api.get(`/dashboard/activities/${currentFY}`)
      ])
      
      setStats(statsRes.data)
      setActivities(activitiesRes.data)
    } catch (error) {
      toast.error('Failed to fetch dashboard data')
    } finally {
      setLoading(false)
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

  const taxData = stats?.tax_computed ? [
    { name: 'Gross Income', value: stats.gross_income },
    { name: 'Total Tax', value: stats.total_tax },
    { name: 'TDS Deducted', value: stats.tds_deducted },
  ] : []

  const COLORS = ['#0ea5e9', '#f59e0b', '#10b981']

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600 mt-1">Financial Year: {currentFY}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Welcome back,</p>
            <p className="text-lg font-semibold text-gray-900">{stats?.name}</p>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Documents Uploaded"
            value={`${stats?.documents_verified || 0} / ${stats?.documents_uploaded || 0}`}
            icon={<FileText className="w-8 h-8 text-primary-600" />}
            color="blue"
          />
          <StatCard
            title="Tax Computed"
            value={stats?.tax_computed ? 'Yes' : 'No'}
            icon={stats?.tax_computed ? <CheckCircle className="w-8 h-8 text-green-600" /> : <XCircle className="w-8 h-8 text-gray-400" />}
            color={stats?.tax_computed ? 'green' : 'gray'}
          />
          <StatCard
            title="Gross Income"
            value={`₹${(stats?.gross_income || 0).toLocaleString('en-IN')}`}
            icon={<TrendingUp className="w-8 h-8 text-blue-600" />}
            color="blue"
          />
          <StatCard
            title="Tax / Refund"
            value={`₹${Math.abs(stats?.net_payable_refund || 0).toLocaleString('en-IN')}`}
            subtitle={stats?.net_payable_refund < 0 ? 'Payable' : 'Refund'}
            icon={stats?.net_payable_refund < 0 ? 
              <TrendingDown className="w-8 h-8 text-red-600" /> : 
              <TrendingUp className="w-8 h-8 text-green-600" />
            }
            color={stats?.net_payable_refund < 0 ? 'red' : 'green'}
          />
        </div>

        {/* Charts */}
        {stats?.tax_computed && (
          <div className="grid lg:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Income & Tax Breakdown</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={taxData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
                  <Bar dataKey="value" fill="#0ea5e9" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Tax Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={taxData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ₹${(value / 1000).toFixed(0)}K`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {taxData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Recommended Regime */}
        {stats?.recommended_regime && (
          <div className="card bg-primary-50 border-primary-200">
            <div className="flex items-start space-x-4">
              <Calculator className="w-8 h-8 text-primary-600 mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Recommended Tax Regime</h3>
                <p className="text-primary-700 font-medium mt-1">{stats.recommended_regime}</p>
                <p className="text-gray-600 mt-2">
                  This recommendation is based on your income and available deductions.
                  View detailed comparison in Tax Calculation page.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Recent Activities */}
        <div className="card">
          <div className="flex items-center space-x-2 mb-4">
            <Activity className="w-6 h-6 text-primary-600" />
            <h3 className="text-lg font-semibold">Recent Activities</h3>
          </div>
          <div className="space-y-3">
            {activities.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No activities yet</p>
            ) : (
              activities.slice(0, 10).map((activity) => (
                <div key={activity.id} className="flex items-start space-x-3 pb-3 border-b border-gray-100 last:border-0">
                  <Calendar className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-gray-900">{activity.description}</p>
                    <p className="text-sm text-gray-500 mt-1">
                      {new Date(activity.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}

function StatCard({ title, value, subtitle, icon, color }) {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200',
    green: 'bg-green-50 border-green-200',
    red: 'bg-red-50 border-red-200',
    gray: 'bg-gray-50 border-gray-200'
  }

  return (
    <div className={`card ${colorClasses[color] || colorClasses.blue}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && <p className="text-sm text-gray-600 mt-1">{subtitle}</p>}
        </div>
        {icon}
      </div>
    </div>
  )
}

export default Dashboard

