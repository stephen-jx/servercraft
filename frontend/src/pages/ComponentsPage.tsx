import { useState, useEffect } from 'react'
import { Card, Row, Col, Tag, Input, Space, Collapse, Badge, Button, Tooltip, Empty, Typography } from 'antd'
import { SearchOutlined, StarOutlined, StarFilled, InfoCircleOutlined } from '@ant-design/icons'
import axios from 'axios'

const { Title, Text } = Typography
const { Panel } = Collapse

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
const categoryConfig: Record<string, { name: string; color: string; description: string }> = {
  system: { name: '系统基础', color: 'gold', description: '软件源、系统设置、安全、性能调优' },
  database: { name: '数据库', color: 'blue', description: 'MySQL、PostgreSQL、Redis、MongoDB' },
  middleware: { name: '中间件', color: 'green', description: 'Nginx、Apache 等服务' },
  message_queue: { name: '消息队列', color: 'orange', description: 'RabbitMQ、Kafka' },
  container: { name: '容器 & 编排', color: 'purple', description: 'Docker、Kubernetes' },
  monitoring: { name: '监控', color: 'cyan', description: 'Prometheus、Grafana' },
  development: { name: '开发环境', color: 'geekblue', description: 'Node.js、Python、Go、Java' },
  other: { name: '其他', color: 'default', description: '其他组件' },
}

const ComponentsPage = () => {
  const [components, setComponents] = useState<Component[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [favorites, setFavorites] = useState<string[]>(() => {
    const saved = localStorage.getItem('envinit-favorites')
    return saved ? JSON.parse(saved) : []
  })

  useEffect(() => {
    setLoading(true)
    axios.get('/api/v1/components')
      .then(res => setComponents(res.data.items || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const toggleFavorite = (name: string) => {
    const newFavorites = favorites.includes(name)
      ? favorites.filter(f => f !== name)
      : [...favorites, name]
    setFavorites(newFavorites)
    localStorage.setItem('envinit-favorites', JSON.stringify(newFavorites))
  }

  const filteredComponents = components.filter(
    c =>
      (selectedCategory ? c.category === selectedCategory : true) &&
      (search
        ? c.name.toLowerCase().includes(search.toLowerCase()) ||
          c.display_name.toLowerCase().includes(search.toLowerCase()) ||
          c.description?.toLowerCase().includes(search.toLowerCase())
        : true)
  )

  // 按分类分组
  const grouped = filteredComponents.reduce((acc, comp) => {
    const category = comp.category
    if (!acc[category]) acc[category] = []
    acc[category].push(comp)
    return acc
  }, {} as Record<string, Component[]>)

  // 统计
  const stats = {
    total: components.length,
    categories: Object.keys(grouped).length,
    favorites: favorites.length,
  }

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <Title level={2} style={{ margin: 0, color: '#1890ff' }}>{stats.total}</Title>
              <Text type="secondary">组件总数</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <Title level={2} style={{ margin: 0, color: '#52c41a' }}>{stats.categories}</Title>
              <Text type="secondary">分类数量</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <Title level={2} style={{ margin: 0, color: '#faad14' }}>{stats.favorites}</Title>
              <Text type="secondary">我的收藏</Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 搜索和筛选 */}
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Input
            placeholder="搜索组件名称、描述..."
            prefix={<SearchOutlined />}
            value={search}
            onChange={e => setSearch(e.target.value)}
            allowClear
            size="large"
          />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            <Button
              type={selectedCategory === null ? 'primary' : 'default'}
              onClick={() => setSelectedCategory(null)}
            >
              全部 ({components.length})
            </Button>
            {Object.entries(categoryConfig).map(([key, config]) => {
              const count = components.filter(c => c.category === key).length
              if (count === 0) return null
              return (
                <Button
                  key={key}
                  type={selectedCategory === key ? 'primary' : 'default'}
                  onClick={() => setSelectedCategory(key)}
                >
                  <Badge color={config.color} /> {config.name} ({count})
                </Button>
              )
            })}
          </div>
        </Space>
      </Card>

      {/* 收藏的组件 */}
      {favorites.length > 0 && !selectedCategory && (
        <Card 
          title={
            <Space>
              <StarFilled style={{ color: '#faad14' }} />
              <span>我的收藏</span>
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          <Row gutter={[12, 12]}>
            {components
              .filter(c => favorites.includes(c.name))
              .filter(c => !search || 
                c.name.toLowerCase().includes(search.toLowerCase()) ||
                c.display_name.toLowerCase().includes(search.toLowerCase())
              )
              .map(comp => (
                <Col key={comp.name} xs={12} sm={8} md={6} lg={4}>
                  <ComponentCard
                    component={comp}
                    isFavorite
                    onToggleFavorite={() => toggleFavorite(comp.name)}
                  />
                </Col>
              ))}
          </Row>
        </Card>
      )}

      {/* 分类组件列表 */}
      {filteredComponents.length > 0 ? (
        <Collapse
          defaultActiveKey={Object.keys(grouped)}
          style={{ background: '#fff', borderRadius: 8 }}
        >
          {Object.entries(grouped).map(([category, comps]) => {
            const config = categoryConfig[category] || { name: category, color: 'default', description: '' }
            return (
              <Panel
                header={
                  <Space>
                    <Badge color={config.color} />
                    <span style={{ fontWeight: 500 }}>{config.name}</span>
                    <Tag>{comps.length}</Tag>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {config.description}
                    </Text>
                  </Space>
                }
                key={category}
              >
                <Row gutter={[12, 12]}>
                  {comps.map(comp => (
                    <Col key={comp.name} xs={12} sm={8} md={6} lg={4}>
                      <ComponentCard
                        component={comp}
                        isFavorite={favorites.includes(comp.name)}
                        onToggleFavorite={() => toggleFavorite(comp.name)}
                      />
                    </Col>
                  ))}
                </Row>
              </Panel>
            )
          })}
        </Collapse>
      ) : (
        <Card>
          <Empty description="没有找到匹配的组件" />
        </Card>
      )}
    </div>
  )
}

// 组件卡片
interface ComponentCardProps {
  component: Component
  isFavorite: boolean
  onToggleFavorite: () => void
}

const ComponentCard = ({ component, isFavorite, onToggleFavorite }: ComponentCardProps) => {
  const categoryConfigItem = categoryConfig[component.category] || { name: component.category, color: 'default' }
  
  return (
    <Card
      hoverable
      size="small"
      style={{ height: '100%' }}
      actions={[
        <Tooltip key="favorite" title={isFavorite ? '取消收藏' : '收藏'}>
          <Button
            type="text"
            size="small"
            icon={isFavorite ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
            onClick={onToggleFavorite}
          />
        </Tooltip>,
        <Tooltip key="info" title="查看详情">
          <Button type="text" size="small" icon={<InfoCircleOutlined />} />
        </Tooltip>,
      ]}
    >
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>
          {component.display_name}
        </div>
        <Tag color={categoryConfigItem.color} style={{ marginBottom: 8 }}>
          {categoryConfigItem.name}
        </Tag>
        <div style={{ fontSize: 12, color: '#666', lineHeight: 1.4 }}>
          {component.description?.slice(0, 50)}
          {component.description && component.description.length > 50 && '...'}
        </div>
        {component.default_version && (
          <div style={{ marginTop: 8 }}>
            <Text type="secondary" style={{ fontSize: 11 }}>v{component.default_version}</Text>
          </div>
        )}
        {component.dependencies && component.dependencies.length > 0 && (
          <div style={{ marginTop: 8 }}>
            <Text type="secondary" style={{ fontSize: 11 }}>
              依赖: {component.dependencies.join(', ')}
            </Text>
          </div>
        )}
      </div>
    </Card>
  )
}

export default ComponentsPage