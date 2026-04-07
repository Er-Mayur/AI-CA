import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'
import api from '../services/api'
import toast from 'react-hot-toast'
import { 
  User, Mail, CreditCard, Calendar, Users, 
  Lock, Trash2, Save, AlertTriangle, Eye, EyeOff, Shield, Edit3, LogOut
} from 'lucide-react'

function Profile() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  
  // Editable fields
  const [gender, setGender] = useState(user?.gender || '')
  const [isEditingGender, setIsEditingGender] = useState(false)
  const [savingGender, setSavingGender] = useState(false)
  
  // Password change
  const [showPasswordSection, setShowPasswordSection] = useState(false)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [changingPassword, setChangingPassword] = useState(false)
  
  // Delete account
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleteConfirmation, setDeleteConfirmation] = useState('')
  const [deletingAccount, setDeletingAccount] = useState(false)

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-IN', { 
      day: '2-digit', 
      month: 'long', 
      year: 'numeric' 
    })
  }

  // Handle gender update
  const handleGenderUpdate = async () => {
    if (!gender) {
      toast.error('Please select a gender')
      return
    }
    
    setSavingGender(true)
    try {
      await api.put('/auth/profile', { gender })
      toast.success('Gender updated successfully')
      setIsEditingGender(false)
      // Refresh user data
      window.location.reload()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update gender')
    } finally {
      setSavingGender(false)
    }
  }

  // Handle password change
  const handlePasswordChange = async (e) => {
    e.preventDefault()
    
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match')
      return
    }
    
    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters')
      return
    }
    
    setChangingPassword(true)
    try {
      await api.put('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword
      })
      toast.success('Password changed successfully')
      setShowPasswordSection(false)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to change password')
    } finally {
      setChangingPassword(false)
    }
  }

  // Handle account deletion
  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== 'DELETE') {
      toast.error('Please type DELETE to confirm')
      return
    }
    
    setDeletingAccount(true)
    try {
      await api.delete('/auth/account')
      toast.success('Account deleted successfully')
      logout()
      navigate('/')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete account')
    } finally {
      setDeletingAccount(false)
      setShowDeleteModal(false)
    }
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto py-8 px-4">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Profile Settings</h1>
          <p className="text-gray-600 mt-2">Manage your account settings and preferences</p>
        </div>

        {/* Profile Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden mb-6">
          {/* Profile Header */}
          <div className="bg-gradient-to-r from-primary-600 to-primary-700 px-6 py-8">
            <div className="flex items-center gap-4">
              <div className="h-20 w-20 rounded-full bg-white/20 backdrop-blur flex items-center justify-center text-white text-3xl font-bold ring-4 ring-white/30">
                {user?.name?.charAt(0) || 'U'}
              </div>
              <div className="text-white">
                <h2 className="text-2xl font-bold">{user?.name}</h2>
                <p className="text-primary-100 flex items-center gap-2 mt-1">
                  <CreditCard className="w-4 h-4" />
                  {user?.pan_card}
                </p>
              </div>
            </div>
          </div>

          {/* Personal Information */}
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <User className="w-5 h-5 text-primary-600" />
              Personal Information
            </h3>
            
            <div className="grid md:grid-cols-2 gap-6">
              {/* Name - Not Editable */}
              <div className="bg-gray-50 rounded-xl p-4">
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wide flex items-center gap-1">
                  <Lock className="w-3 h-3" /> Full Name
                </label>
                <p className="text-lg font-semibold text-gray-900 mt-1">{user?.name}</p>
                <p className="text-xs text-gray-400 mt-1">Cannot be modified</p>
              </div>

              {/* Email - Not Editable */}
              <div className="bg-gray-50 rounded-xl p-4">
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wide flex items-center gap-1">
                  <Lock className="w-3 h-3" /> Email Address
                </label>
                <p className="text-lg font-semibold text-gray-900 mt-1 flex items-center gap-2">
                  <Mail className="w-4 h-4 text-gray-400" />
                  {user?.email}
                </p>
                <p className="text-xs text-gray-400 mt-1">Cannot be modified</p>
              </div>

              {/* PAN Card - Not Editable */}
              <div className="bg-gray-50 rounded-xl p-4">
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wide flex items-center gap-1">
                  <Lock className="w-3 h-3" /> PAN Card
                </label>
                <p className="text-lg font-semibold text-gray-900 mt-1 font-mono">{user?.pan_card}</p>
                <p className="text-xs text-gray-400 mt-1">Cannot be modified</p>
              </div>

              {/* Date of Birth - Not Editable */}
              <div className="bg-gray-50 rounded-xl p-4">
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wide flex items-center gap-1">
                  <Lock className="w-3 h-3" /> Date of Birth
                </label>
                <p className="text-lg font-semibold text-gray-900 mt-1 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  {formatDate(user?.date_of_birth)}
                </p>
                <p className="text-xs text-gray-400 mt-1">Cannot be modified</p>
              </div>

              {/* Gender - Editable */}
              <div className="bg-white border border-gray-200 rounded-xl p-4">
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wide flex items-center gap-1">
                  <Edit3 className="w-3 h-3 text-primary-500" /> Gender
                </label>
                {isEditingGender ? (
                  <div className="mt-2 space-y-3">
                    <select
                      value={gender}
                      onChange={(e) => setGender(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="">Select Gender</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                    </select>
                    <div className="flex gap-2">
                      <button
                        onClick={handleGenderUpdate}
                        disabled={savingGender}
                        className="flex-1 bg-primary-600 text-white py-2 px-3 rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50 flex items-center justify-center gap-1"
                      >
                        {savingGender ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                        ) : (
                          <>
                            <Save className="w-4 h-4" /> Save
                          </>
                        )}
                      </button>
                      <button
                        onClick={() => {
                          setIsEditingGender(false)
                          setGender(user?.gender || '')
                        }}
                        className="px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg text-sm"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between mt-1">
                    <p className="text-lg font-semibold text-gray-900 flex items-center gap-2 capitalize">
                      <Users className="w-4 h-4 text-gray-400" />
                      {user?.gender || 'Not specified'}
                    </p>
                    <button
                      onClick={() => setIsEditingGender(true)}
                      className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                    >
                      Edit
                    </button>
                  </div>
                )}
              </div>

              {/* Account Type */}
              <div className="bg-gray-50 rounded-xl p-4">
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Account Type</label>
                <p className="text-lg font-semibold text-gray-900 mt-1 flex items-center gap-2">
                  <Shield className="w-4 h-4 text-gray-400" />
                  {user?.is_admin ? 'Administrator' : 'Standard User'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Security Section */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden mb-6">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Lock className="w-5 h-5 text-primary-600" />
              Security
            </h3>

            {/* Change Password */}
            <div className="border border-gray-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900">Password</h4>
                  <p className="text-sm text-gray-500">Change your account password</p>
                </div>
                {!showPasswordSection && (
                  <button
                    onClick={() => setShowPasswordSection(true)}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    Change Password
                  </button>
                )}
              </div>

              {showPasswordSection && (
                <form onSubmit={handlePasswordChange} className="mt-4 space-y-4 border-t pt-4">
                  {/* Current Password */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
                    <div className="relative">
                      <input
                        type={showCurrentPassword ? 'text' : 'password'}
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 pr-10"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* New Password */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
                    <div className="relative">
                      <input
                        type={showNewPassword ? 'text' : 'password'}
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 pr-10"
                        required
                        minLength={6}
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* Confirm Password */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      required
                    />
                    {confirmPassword && newPassword !== confirmPassword && (
                      <p className="text-red-500 text-xs mt-1">Passwords do not match</p>
                    )}
                  </div>

                  <div className="flex gap-2">
                    <button
                      type="submit"
                      disabled={changingPassword}
                      className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
                    >
                      {changingPassword ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                      ) : (
                        <>
                          <Save className="w-4 h-4" /> Update Password
                        </>
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setShowPasswordSection(false)
                        setCurrentPassword('')
                        setNewPassword('')
                        setConfirmPassword('')
                      }}
                      className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>

        {/* Logout Section */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden mb-6">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <LogOut className="w-5 h-5 text-gray-600" />
                  Sign Out
                </h3>
                <p className="text-sm text-gray-500 mt-1">Sign out of your account on this device</p>
              </div>
              <button
                onClick={() => {
                  logout()
                  navigate('/')
                  toast.success('Logged out successfully')
                }}
                className="bg-gray-900 hover:bg-gray-800 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="bg-white rounded-2xl shadow-sm border border-red-200 overflow-hidden">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-red-600 mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              Danger Zone
            </h3>

            <div className="border border-red-200 rounded-xl p-4 bg-red-50">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-red-800">Delete Account</h4>
                  <p className="text-sm text-red-600">Permanently delete your account and all associated data. This action cannot be undone.</p>
                </div>
                <button
                  onClick={() => setShowDeleteModal(true)}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete Account
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Delete Confirmation Modal */}
        {showDeleteModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
              <div className="text-center mb-6">
                <div className="mx-auto w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
                  <AlertTriangle className="w-6 h-6 text-red-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-900">Delete Account?</h3>
                <p className="text-gray-600 mt-2">
                  This will permanently delete your account, all documents, tax computations, and data. This action cannot be undone.
                </p>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Type <span className="font-bold text-red-600">DELETE</span> to confirm
                </label>
                <input
                  type="text"
                  value={deleteConfirmation}
                  onChange={(e) => setDeleteConfirmation(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  placeholder="DELETE"
                />
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowDeleteModal(false)
                    setDeleteConfirmation('')
                  }}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteAccount}
                  disabled={deleteConfirmation !== 'DELETE' || deletingAccount}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                  {deletingAccount ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  ) : (
                    <>
                      <Trash2 className="w-4 h-4" />
                      Delete Forever
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}

export default Profile
