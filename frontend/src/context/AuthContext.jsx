import { createContext, useContext, useState, useEffect } from 'react'
import api from '../services/api'

const AuthContext = createContext({})

export function useAuth() {
  return useContext(AuthContext)
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [currentFY, setCurrentFY] = useState(new Date().getMonth() > 2 ? `${new Date().getFullYear()}-${(new Date().getFullYear()+1).toString().slice(-2)}` : `${new Date().getFullYear()-1}-${new Date().getFullYear().toString().slice(-2)}`)

  useEffect(() => {
    // Check if user is logged in on mount
    const initAuth = async () => {
      const savedToken = localStorage.getItem('token')
      if (savedToken) {
        try {
          const response = await api.get('/auth/me')
          setUser(response.data)
        } catch (error) {
          localStorage.removeItem('token')
          setToken(null)
        }
      }
      setLoading(false)
    }

    initAuth()
  }, [])

  const login = async (identifier, password) => {
    const response = await api.post('/auth/login', { identifier, password })
    const { access_token, user } = response.data
    
    localStorage.setItem('token', access_token)
    setToken(access_token)
    setUser(user)
    
    return response.data
  }

  const register = async (userData) => {
    const response = await api.post('/auth/register', userData)
    const { access_token, user } = response.data
    
    localStorage.setItem('token', access_token)
    setToken(access_token)
    setUser(user)
    
    return response.data
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  const value = {
    user,
    token,
    login,
    register,
    logout,
    loading,
    currentFY,
    setCurrentFY
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

