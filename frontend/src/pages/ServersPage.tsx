import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  Card, Button, Modal, Form, Input, InputNumber, Space, Tag, message, Popconfirm,
  Row, Col, Divider, Tabs, Badge, Collapse, Select, Switch, Tooltip, Typography
} from 'antd'
import {
  PlusOutlined, DeleteOutlined, ReloadOutlined, PlayCircleOutlined,
  SettingOutlined, InfoCircleOutlined, StarOutlined, StarFilled,
  CloudServerOutlined, LockOutlined, ToolOutlined, DashboardOutlined,
  DatabaseOutlined, ApiOutlined, CodeOutlined, ContainerOutlined,
  ClockCircleOutlined, UserOutlined, SafetyOutlined, ThunderboltOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Title, Text } = Typography
const { Panel } = Collapse
const { TabPane } = Tabs

interface Server {
  id: number
  name: string
  ip_address: string
  port: number
  username: string
  os_type?: string
  os_version?: string
  arch?: string
  status: string
  created_at: string
}

interface Component {
  name: string
  display_name: string
  category: string
  description: string
  default_version?: string
  versions?: string[]
  options?: any[]
  dependencies?: string[]
  ports?: number[]
  icon?: string
}

// 分类配置
const categoryConfig: Record<string, { name: string; icon: any; color: string }> = {
  system: { name: '系统基础', icon: <ToolOutlined />, color: '#faad14' },
  database: { name: '数据库', icon: <DatabaseOutlined />, color: '#1890ff' },
  middleware: { name: '中间件', icon: <ApiOutlined />, color: '#52c41a' },
  message_queue: { name: '消息队列', icon: <CloudServerOutlined />, color: '#fa8c16' },
  container: { name: '容器 & 编排', icon: <ContainerOutlined />, color: '#722ed1' },
  monitoring: { name: '监控', icon: <DashboardOutlined />, color: '#13c2c2' },
  development: { name: '开发环境', icon: <CodeOutlined />, color: '#2f54eb' },
  other: { name: '其他', icon: <SettingOutlined />, color: '#8c8c8c' },
}

// 子分类配置
const subCategoryConfig: Record<string, { name: string; icon: any }> = {
  mirror: { name: '软件源', icon: <CloudServerOutlined /> },
  settings: { name: '系统设置', icon: <SettingOutlined /> },
  security: { name: '安全配置', icon: <SafetyOutlined /> },
  performance: { name: '性能调优', icon: <ThunderboltOutlined /> },
  tools: { name: '系统工具', icon: <ToolOutlined /> },
  user: { name: '用户管理', icon: <UserOutlined /> },
}

const ServersPage = () => {
  const navigate = useNavigate()
  const [servers, setServers] = useState<Server[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [installModalOpen, setInstallModalOpen] = useState(false)
  const [selectedServer, setSelectedServer] = useState<Server | null>(null)
  const [form] = Form.useForm()

  const fetchServers = async () => {
    setLoading(true)
    try {
      const res = await axios.get('/api/v1/servers')
      setServers(res.data.items || [])
    } catch (error) {
      message.error('获取服务器列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchServers()
  }, [])

  const handleAdd = () => {
    form.resetFields()
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      await axios.post('/api/v1/servers', values)
      message.success('添加成功')
      setModalOpen(false)
      fetchServers()
    } catch (error) {
      message.error('添加失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await axios.delete(`/api/v1/servers/${id}`)
      message.success('删除成功')
      fetchServers()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleDetect = async (id: number) => {
    try {
      message.loading({ content: '正在检测系统信息...', key: 'detect' })
      const res = await axios.post(`/api/v1/servers/${id}/detect`)
      message.success({ content: `检测完成: ${res.data.os_type} ${res.data.os_version}`, key: 'detect' })
      fetchServers()
    } catch (error) {
      message.error({ content: '检测失败', key: 'detect' })
    }
  }

  const handleInstall = (server: Server) => {
    setSelectedServer(server)
    setInstallModalOpen(true)
  }

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 120,
    },
    {
      title: 'IP 地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 140,
    },
    {
      title: '端口',
      dataIndex: 'port',
      key: 'port',
      width: 70,
    },
    {
      title: '用户',
      dataIndex: 'username',
      key: 'username',
      width: 80,
    },
    {
      title: '系统',
      key: 'os',
      width: 200,
      render: (_: any, record: Server) => {
        if (record.os_type) {
          return (
            <Space>
              <Tag color="blue">{record.os_type}</Tag>
              <Text type="secondary">{record.os_version}</Text>
              <Text type="secondary">({record.arch})</Text>
            </Space>
          )
        }
        return <Text type="secondary">未检测</Text>
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => {
        const colors: Record<string, string> = {
          online: 'green',
          offline: 'red',
          unknown: 'default',
        }
        return <Badge status={colors[status] === 'green' ? 'success' : 'default'} text={status} />
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 260,
      render: (_: any, record: Server) => (
        <Space>
          <Button size="small" onClick={() => handleDetect(record.id)}>
            检测
          </Button>
          <Button type="primary" size="small" onClick={() => handleInstall(record)}>
            安装组件
          </Button>
          <Popconfirm title="确定删除?" onConfirm={() => handleDelete(record.id)}>
            <Button danger size="small">
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <Card
      title={
        <Space>
          <CloudServerOutlined />
          <span>服务器列表</span>
          <Badge count={servers.length} style={{ backgroundColor: '#1890ff' }} />
        </Space>
      }
      extra={
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchServers}>
            刷新
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            添加服务器
          </Button>
        </Space>
      }
    >
      <Row gutter={[16, 16]}>
        {servers.map(server => (
          <Col key={server.id} xs={24} sm={12} lg={8} xl={6}>
            <Card
              hoverable
              size="small"
              actions={[
                <Tooltip title="检测系统">
                  <Button type="text" size="small" onClick={() => handleDetect(server.id)}>
                    检测
                  </Button>
                </Tooltip>,
                <Tooltip title="安装组件">
                  <Button type="text" size="small" type="primary" onClick={() => handleInstall(server)}>
                    安装
                  </Button>
                </Tooltip>,
                <Popconfirm title="确定删除?" onConfirm={() => handleDelete(server.id)}>
                  <Button type="text" size="small" danger>删除</Button>
                </Popconfirm>,
              ]}
            >
              <Card.Meta
                title={
                  <Space>
                    <Text strong>{server.name}</Text>
                    <Badge 
                      status={server.status === 'online' ? 'success' : 'default'} 
                    />
                  </Space>
                }
                description={
                  <div>
                    <div><Text type="secondary">{server.ip_address}:{server.port}</Text></div>
                    <div><Text type="secondary">{server.username}</Text></div>
                    {server.os_type && (
                      <div style={{ marginTop: 8 }}>
                        <Tag color="blue">{server.os_type} {server.os_version}</Tag>
                      </div>
                    )}
                  </div>
                }
              />
            </Card>
          </Col>
        ))}
        {servers.length === 0 && (
          <Col span={24}>
            <div style={{ textAlign: 'center', padding: 60, color: '#999' }}>
              <CloudServerOutlined style={{ fontSize: 48, marginBottom: 16 }} />
              <div>暂无服务器，点击"添加服务器"开始</div>
            </div>
          </Col>
        )}
      </Row>

      <Modal
        title="添加服务器"
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        okText="添加"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input placeholder="服务器名称" />
          </Form.Item>
          <Form.Item name="ip_address" label="IP 地址" rules={[{ required: true }]}>
            <Input placeholder="192.168.1.100" />
          </Form.Item>
          <Form.Item name="port" label="SSH 端口" initialValue={22}>
            <InputNumber min={1} max={65535} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="username" label="用户名" initialValue="root">
            <Input placeholder="root" />
          </Form.Item>
          <Form.Item name="password" label="密码">
            <Input.Password placeholder="SSH 密码" />
          </Form.Item>
          <Form.Item name="ssh_key" label="SSH 私钥">
            <Input.TextArea rows={4} placeholder="-----BEGIN RSA PRIVATE KEY-----" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`安装组件 - ${selectedServer?.name}`}
        open={installModalOpen}
        onCancel={() => setInstallModalOpen(false)}
        footer={null}
        width={900}
        destroyOnClose
      >
        {selectedServer && (
          <InstallForm
            serverId={selectedServer.id}
            serverOs={selectedServer.os_type}
            onSuccess={() => {
              setInstallModalOpen(false)
              navigate('/tasks')
            }}
          />
        )}
      </Modal>
    </Card>
  )
}

// 安装组件表单 - 新版优化布局
interface InstallFormProps {
  serverId: number
  serverOs?: string
  onSuccess: () => void
}

const InstallForm = ({ serverId, serverOs, onSuccess }: InstallFormProps) => {
  const [loading, setLoading] = useState(false)
  const [components, setComponents] = useState<Component[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [searchText, setSearchText] = useState('')
  const [selected, setSelected] = useState<string[]>([])
  const [favorites, setFavorites] = useState<string[]>(() => {
    const saved = localStorage.getItem('envinit-favorites')
    return saved ? JSON.parse(saved) : []
  })

  useEffect(() => {
    axios.get('/api/v1/components').then(res => {
      setComponents(res.data.items || [])
    })
  }, [])

  const toggleFavorite = (name: string) => {
    const newFavorites = favorites.includes(name)
      ? favorites.filter(f => f !== name)
      : [...favorites, name]
    setFavorites(newFavorites)
    localStorage.setItem('envinit-favorites', JSON.stringify(newFavorites))
  }

  const filteredComponents = components.filter(comp => {
    const matchCategory = selectedCategory === 'all' || comp.category === selectedCategory
    const matchSearch = !searchText || 
      comp.name.toLowerCase().includes(searchText.toLowerCase()) ||
      comp.display_name.toLowerCase().includes(searchText.toLowerCase())
    return matchCategory && matchSearch
  })

  // 按分类分组
  const grouped = filteredComponents.reduce((acc, comp) => {
    const cat = comp.category
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(comp)
    return acc
  }, {} as Record<string, Component[]>)

  // 收藏的组件
  const favoriteComponents = components.filter(c => favorites.includes(c.name))

  const handleInstall = async () => {
    setLoading(true)
    try {
      await axios.post('/api/v1/tasks', {
        server_id: serverId,
        task_type: 'install',
        component_names: selected,
      })
      message.success('任务已创建')
      onSuccess()
    } catch (error) {
      message.error('创建任务失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {/* 搜索和分类过滤 */}
      <div style={{ marginBottom: 16 }}>
        <Space style={{ width: '100%' }} direction="vertical">
          <Input.Search
            placeholder="搜索组件..."
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            style={{ width: '100%' }}
            allowClear
          />
          <div>
            <Button 
              type={selectedCategory === 'all' ? 'primary' : 'default'}
              onClick={() => setSelectedCategory('all')}
              style={{ marginRight: 8, marginBottom: 8 }}
            >
              全部 ({components.length})
            </Button>
            {favorites.length > 0 && (
              <Button
                type={selectedCategory === 'favorites' ? 'primary' : 'default'}
                onClick={() => setSelectedCategory('favorites')}
                style={{ marginRight: 8, marginBottom: 8 }}
                icon={<StarFilled />}
              >
                收藏 ({favorites.length})
              </Button>
            )}
            {Object.entries(categoryConfig).map(([key, config]) => {
              const count = components.filter(c => c.category === key).length
              if (count === 0) return null
              return (
                <Button
                  key={key}
                  type={selectedCategory === key ? 'primary' : 'default'}
                  onClick={() => setSelectedCategory(key)}
                  style={{ marginRight: 8, marginBottom: 8 }}
                >
                  {config.icon} {config.name} ({count})
                </Button>
              )
            })}
          </div>
        </Space>
      </div>

      <Divider />

      {/* 组件列表 */}
      <div style={{ maxHeight: 450, overflowY: 'auto' }}>
        {selectedCategory === 'favorites' && favoriteComponents.length > 0 ? (
          <Row gutter={[12, 12]}>
            {favoriteComponents.map(comp => (
              <Col key={comp.name} xs={12} sm={8} md={6}>
                <ComponentCard
                  component={comp}
                  selected={selected.includes(comp.name)}
                  favorite={true}
                  onSelect={() => {
                    if (selected.includes(comp.name)) {
                      setSelected(selected.filter(s => s !== comp.name))
                    } else {
                      setSelected([...selected, comp.name])
                    }
                  }}
                  onToggleFavorite={() => toggleFavorite(comp.name)}
                />
              </Col>
            ))}
          </Row>
        ) : (
          <Collapse
            defaultActiveKey={Object.keys(grouped)}
            ghost
          >
            {Object.entries(grouped).map(([category, comps]) => {
              const config = categoryConfig[category] || { name: category, icon: null }
              return (
                <Panel
                  header={
                    <Space>
                      {config.icon}
                      <span style={{ fontWeight: 500 }}>{config.name}</span>
                      <Tag>{comps.length}</Tag>
                    </Space>
                  }
                  key={category}
                >
                  <Row gutter={[12, 12]}>
                    {comps.map(comp => (
                      <Col key={comp.name} xs={12} sm={8} md={6}>
                        <ComponentCard
                          component={comp}
                          selected={selected.includes(comp.name)}
                          favorite={favorites.includes(comp.name)}
                          onSelect={() => {
                            if (selected.includes(comp.name)) {
                              setSelected(selected.filter(s => s !== comp.name))
                            } else {
                              setSelected([...selected, comp.name])
                            }
                          }}
                          onToggleFavorite={() => toggleFavorite(comp.name)}
                        />
                      </Col>
                    ))}
                  </Row>
                </Panel>
              )
            })}
          </Collapse>
        )}

        {filteredComponents.length === 0 && (
          <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
            没有找到匹配的组件
          </div>
        )}
      </div>

      <Divider />

      {/* 底部操作栏 */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        background: '#fafafa',
        padding: '12px 16px',
        borderRadius: 8,
        marginTop: 16
      }}>
        <Space>
          <Text>已选择: </Text>
          {selected.length === 0 ? (
            <Text type="secondary">暂无</Text>
          ) : (
            <>
              {selected.slice(0, 5).map(name => (
                <Tag key={name} closable onClose={() => setSelected(selected.filter(s => s !== name))}>
                  {name}
                </Tag>
              ))}
              {selected.length > 5 && <Tag>+{selected.length - 5}</Tag>}
            </>
          )}
        </Space>
        <Space>
          <Button onClick={onSuccess}>取消</Button>
          <Button
            type="primary"
            loading={loading}
            disabled={selected.length === 0}
            onClick={handleInstall}
            icon={<PlayCircleOutlined />}
          >
            开始安装 ({selected.length} 个)
          </Button>
        </Space>
      </div>
    </div>
  )
}

// 组件卡片
interface ComponentCardProps {
  component: Component
  selected: boolean
  favorite: boolean
  onSelect: () => void
  onToggleFavorite: () => void
}

const ComponentCard = ({ component, selected, favorite, onSelect, onToggleFavorite }: ComponentCardProps) => {
  return (
    <Card
      hoverable
      size="small"
      style={{
        borderColor: selected ? '#1890ff' : undefined,
        background: selected ? '#e6f7ff' : undefined,
      }}
      onClick={onSelect}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 500, marginBottom: 4 }}>{component.display_name}</div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {component.description?.slice(0, 30)}...
          </Text>
        </div>
        <Space size={0}>
          <Tooltip title={favorite ? '取消收藏' : '收藏'}>
            <Button 
              type="text" 
              size="small" 
              icon={favorite ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
              onClick={(e) => { e.stopPropagation(); onToggleFavorite() }}
            />
          </Tooltip>
        </Space>
      </div>
      {selected && (
        <div style={{ position: 'absolute', top: 8, right: 8 }}>
          <Tag color="blue">✓</Tag>
        </div>
      )}
    </Card>
  )
}

export default ServersPage