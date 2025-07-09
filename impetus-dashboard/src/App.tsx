import { Layout, Menu } from 'antd';
import { ThunderboltOutlined, DatabaseOutlined } from '@ant-design/icons';
import VectorDBVisualizer from './components/VectorDBVisualizer';

const { Header, Content, Sider } = Layout;

export default function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible>
        <div className="demo-logo-vertical" />
        <Menu
          theme="dark"
          defaultSelectedKeys={['1']}
          items={[
            {
              key: '1',
              icon: <DatabaseOutlined />,
              label: 'VectorDB Dashboard',
            },
            {
              key: '2',
              icon: <ThunderboltOutlined />,
              label: 'MCP Services',
            },
          ]}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: '#fff' }} />
        <Content style={{ margin: '24px 16px' }}>
          <VectorDBVisualizer />
        </Content>
      </Layout>
    </Layout>
  );
}
