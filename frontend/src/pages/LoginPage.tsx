import { useState } from 'react'
import { Form, Input, Button, Card, message, Space, Typography } from 'antd'
import { UserOutlined, LockOutlined, LoginOutlined } from '@ant-design/icons'
import axios from 'axios'

const { Title, Text } = Typography

interface LoginForm {
  username: string
  password: string
}

interface LoginProps {
  onLogin: (user: any) => void
}

const LoginPage = ({ onLogin }: LoginProps) => {
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  const handleLogin = async (values: LoginForm) => {
    setLoading(true)
    try {
      // OAuth2 form encoding
      const formData = new FormData()
      formData.append('username', values.username)
      formData.append('password', values.password)

      const res = await axios.post('/api/v1/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })

      // Store token
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('user', JSON.stringify(res.data.user))
      
      // Set default auth header
      axios.defaults.headers.common['Authorization'] = `Bearer ${res.data.access_token}`
      
      message.success(`欢迎回来，${res.data.user.username}！`)
      onLogin(res.data.user)
    } catch (error: any) {
      const msg = error.response?.data?.detail || '登录失败'
      message.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    }}>
      <Card
        style={{
          width: 400,
          boxShadow: '0 4px 24px rgba(0,0,0,0.15)',
          borderRadius: 12,
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ fontSize: 48, marginBottom: 8 }}>🛠️</div>
          <Title level={2} style={{ margin: 0 }}>ServerCraft</Title>
          <Text type="secondary">环境初始化平台</Text>
        </div>

        <Form
          form={form}
          layout="vertical"
          onFinish={handleLogin}
          autoComplete="off"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              size="large"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 8 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<LoginOutlined />}
              size="large"
              block
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            首次使用？第一个注册的用户将成为管理员
          </Text>
        </div>
      </Card>
    </div>
  )
}

export default LoginPage