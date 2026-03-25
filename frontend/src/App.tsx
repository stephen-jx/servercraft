import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, message } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import axios from 'axios'

import MainLayout from './layouts/MainLayout'
import LoginPage from './pages/LoginPage'
import ServersPage from './pages/ServersPage'
import TasksPage from './pages/TasksPage'
import TaskDetailPage from './pages/TaskDetailPage'
import ComponentsPage from './pages/ComponentsPage'

// 初始化 axios
const token = localStorage.getItem('token')
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

function App() {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 检查是否已登录
    const checkAuth = async () => {
      const savedUser = localStorage.getItem('user')
      const savedToken = localStorage.getItem('token')
      
      if (savedToken && savedUser) {
        try {
          // 验证 token 是否有效
          const res = await axios.get('/api/v1/auth/me')
          setUser(res.data)
        } catch (error) {
          // Token 无效，清除
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          delete axios.defaults.headers.common['Authorization']
        }
      }
      setLoading(false)
    }
    
    checkAuth()
  }, [])

  const handleLogin = (userData: any) => {
    setUser(userData)
  }

  const handleLogout = async () => {
    try {
      await axios.post('/api/v1/auth/logout')
    } catch (error) {
      // ignore
    }
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    delete axios.defaults.headers.common['Authorization']
    setUser(null)
    message.success('已退出登录')
  }

  if (loading) {
    return <div style={{ 
      height: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      background: '#f0f2f5'
    }}>
      加载中...
    </div>
  }

  if (!user) {
    return (
      <ConfigProvider locale={zhCN}>
        <LoginPage onLogin={handleLogin} />
      </ConfigProvider>
    )
  }

  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MainLayout user={user} onLogout={handleLogout} />}>
            <Route index element={<ServersPage />} />
            <Route path="servers" element={<ServersPage />} />
            <Route path="tasks" element={<TasksPage />} />
            <Route path="tasks/:id" element={<TaskDetailPage />} />
            <Route path="components" element={<ComponentsPage />} />
          </Route>
          <Route path="/login" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App