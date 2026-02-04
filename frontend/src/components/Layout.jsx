import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { 
  Brain, LayoutDashboard, FileText, Calculator, 
  TrendingUp, MessageCircle, Award, LogOut, Menu, X, Calendar 
} from 'lucide-react'
import { useState } from 'react'

function Layout({ children }) {
  const { user, logout, currentFY, setCurrentFY } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Generate Year Options (e.g., 2023-24, 2024-25, 2025-26)
  const currentYear = new Date().getFullYear();
  const yearOptions = [
    `${currentYear-2}-${(currentYear-1).toString().slice(-2)}`,
    `${currentYear-1}-${(currentYear).toString().slice(-2)}`,
    `${currentYear}-${(currentYear+1).toString().slice(-2)}`,
  ];

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Documents', href: '/documents', icon: FileText },
    { name: 'Tax Calculation', href: '/tax-calculation', icon: Calculator },
    { name: 'Investments', href: '/investments', icon: TrendingUp },
    { name: 'Q&A', href: '/qna', icon: MessageCircle },
    { name: 'Benefits', href: '/benefits', icon: Award },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <nav className="bg-white border-b border-gray-100 z-50 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 justify-between items-center">
            
            {/* Left Side: Logo */}
            <div className="flex items-center flex-shrink-0">
              <Link to="/dashboard" className="flex items-center gap-2 group">
                <div className="bg-primary-50 p-2 rounded-lg group-hover:bg-primary-100 transition-colors">
                  <Brain className="w-6 h-6 text-primary-600" />
                </div>
                <span className="text-xl font-bold bg-gradient-to-r from-primary-700 to-primary-500 bg-clip-text text-transparent">AI-CA</span>
              </Link>
            </div>

            {/* Center: Navigation Links (Desktop) */}
            <div className="hidden md:flex items-center space-x-1 lg:space-x-2">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-gray-900 text-white shadow-md'
                        : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                    title={item.name}
                  >
                    <Icon className={`w-4 h-4 ${isActive ? 'text-primary-300' : 'text-gray-400 group-hover:text-gray-500'}`} />
                    <span className="hidden lg:inline">{item.name}</span>
                  </Link>
                )
              })}
            </div>

            {/* Right Side: Actions */}
            <div className="flex items-center gap-3">
              {/* Year Selector */}
              <div className="hidden md:flex relative items-center bg-gray-50 px-3 py-1.5 rounded-full border border-gray-200 hover:border-primary-200 transition-colors">
                <span className="text-xs font-medium text-gray-500 mr-2 hidden xl:inline">FY</span>
                <select 
                  value={currentFY} 
                  onChange={(e) => setCurrentFY(e.target.value)}
                  className="bg-transparent text-sm font-semibold text-gray-900 focus:outline-none cursor-pointer border-none p-0 pr-6 appearance-none relative z-10"
                >
                  {yearOptions.map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
                <Calendar className="w-3.5 h-3.5 text-primary-500 absolute right-3 pointer-events-none z-0" />
              </div>

              {/* User Profile */}
              <div className="hidden lg:flex items-center gap-3 pl-3 border-l border-gray-200">
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900">{user?.name}</p>
                  <p className="text-xs text-gray-400 font-mono">{user?.pan_card}</p>
                </div>
                <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold text-xs ring-2 ring-white shadow-sm">
                  {user?.name?.charAt(0) || 'U'}
                </div>
              </div>
              
              {/* Logout */}
              <button
                onClick={handleLogout}
                className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
                title="Logout"
              >
                <LogOut className="w-5 h-5" />
              </button>

              {/* Mobile menu button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 rounded-lg text-gray-500 hover:bg-gray-100 focus:outline-none"
              >
                {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-200">
             {/* Mobile User Info */}
             <div className="px-4 py-3 bg-gray-50 border-b border-gray-100">
               <div className="flex items-center">
                 <div className="flex-shrink-0">
                   <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-bold">
                     {user?.name?.charAt(0) || 'U'}
                   </div>
                 </div>
                 <div className="ml-3">
                   <div className="text-base font-medium text-gray-800">{user?.name}</div>
                   <div className="text-sm font-medium text-gray-500">{user?.email}</div>
                 </div>
               </div>
               
               {/* Mobile Year Selector */}
               <div className="mt-3 flex items-center justify-between bg-white px-3 py-2 rounded-lg border border-gray-200 shadow-sm">
                 <div className="flex items-center space-x-2">
                   <Calendar className="w-4 h-4 text-gray-500" />
                   <span className="text-sm font-medium text-gray-700">Financial Year:</span>
                 </div>
                 <select 
                    value={currentFY} 
                    onChange={(e) => setCurrentFY(e.target.value)}
                    className="bg-transparent text-sm font-bold text-primary-700 outline-none"
                  >
                    {yearOptions.map(year => (
                      <option key={year} value={year}>{year}</option>
                    ))}
                  </select>
               </div>
             </div>

            <div className="px-2 pt-2 pb-3 space-y-1">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${
                      isActive
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="font-medium">{item.name}</span>
                  </Link>
                )
              })}
            </div>
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  )
}

export default Layout

