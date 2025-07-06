import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Activity, Cpu, HardDrive, Thermometer, Zap, Wifi } from 'lucide-react';

const PerformanceDashboard = ({ serverUrl }) => {
  const [performanceData, setPerformanceData] = useState([]);
  const [currentMetrics, setCurrentMetrics] = useState(null);
  const [systemInfo, setSystemInfo] = useState(null);
  const [appleSiliconMetrics, setAppleSiliconMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Format timestamp for display
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
  };

  // Custom tooltip for charts
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border rounded shadow-lg">
          <p className="text-sm font-medium">{formatTimestamp(label)}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {`${entry.name}: ${entry.value}${entry.name.includes('Usage') || entry.name.includes('Temperature') ? '%' : ''}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  useEffect(() => {
    const fetchAllData = async () => {
      try {
        // Fetch performance history
        const historyResponse = await fetch(`${serverUrl}/api/performance/history`);
        if (historyResponse.ok) {
          const historyData = await historyResponse.json();
          // Format timestamps for chart display
          const formattedData = historyData.map(point => ({
            ...point,
            displayTime: formatTimestamp(point.timestamp)
          }));
          setPerformanceData(formattedData);
        }

        // Fetch current metrics
        const currentResponse = await fetch(`${serverUrl}/api/performance/current`);
        if (currentResponse.ok) {
          const currentData = await currentResponse.json();
          setCurrentMetrics(currentData);
        }

        // Fetch system info
        const systemResponse = await fetch(`${serverUrl}/api/performance/system-info`);
        if (systemResponse.ok) {
          const systemData = await systemResponse.json();
          setSystemInfo(systemData.data);
        }

        // Fetch Apple Silicon metrics
        const appleResponse = await fetch(`${serverUrl}/api/performance/apple-silicon-metrics`);
        if (appleResponse.ok) {
          const appleData = await appleResponse.json();
          setAppleSiliconMetrics(appleData.data);
        }

        setLoading(false);
        setError(null);
      } catch (e) {
        setError(e.message);
        setLoading(false);
      }
    };

    fetchAllData();
    const interval = setInterval(fetchAllData, 3000); // Refresh every 3 seconds

    return () => clearInterval(interval);
  }, [serverUrl]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Activity className="animate-spin h-8 w-8 mx-auto mb-2 text-blue-500" />
          <div>Loading performance data...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-red-600">
            <Activity className="h-8 w-8 mx-auto mb-2" />
            <div>Error fetching performance data: {error}</div>
            <div className="text-sm text-gray-500 mt-2">
              Make sure the server is running on {serverUrl}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Current Metrics Cards */}
      {currentMetrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Cpu className="h-8 w-8 text-blue-500" />
                <div className="ml-4">
                  <p className="text-2xl font-bold">{currentMetrics.cpu_usage}%</p>
                  <p className="text-xs text-muted-foreground">CPU Usage</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <HardDrive className="h-8 w-8 text-green-500" />
                <div className="ml-4">
                  <p className="text-2xl font-bold">{currentMetrics.memory_usage}%</p>
                  <p className="text-xs text-muted-foreground">Memory Usage</p>
                  <p className="text-xs text-gray-500">
                    {currentMetrics.memory_used_gb?.toFixed(1)} / {currentMetrics.memory_total_gb?.toFixed(1)} GB
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Thermometer className="h-8 w-8 text-red-500" />
                <div className="ml-4">
                  <p className="text-2xl font-bold">{currentMetrics.temperature}°C</p>
                  <p className="text-xs text-muted-foreground">Temperature</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Zap className="h-8 w-8 text-yellow-500" />
                <div className="ml-4">
                  <p className="text-2xl font-bold">{currentMetrics.load_average?.toFixed(2)}</p>
                  <p className="text-xs text-muted-foreground">Load Average</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* System Information */}
      {systemInfo && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Cpu className="h-5 w-5 mr-2" />
              System Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <h4 className="font-semibold mb-2">CPU</h4>
                <div className="text-sm space-y-1">
                  <p>Physical Cores: {systemInfo.cpu?.physical_cores}</p>
                  <p>Logical Cores: {systemInfo.cpu?.logical_cores}</p>
                  {systemInfo.cpu?.max_frequency > 0 && (
                    <p>Max Frequency: {(systemInfo.cpu.max_frequency / 1000).toFixed(1)} GHz</p>
                  )}
                </div>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Memory</h4>
                <div className="text-sm space-y-1">
                  <p>Total: {systemInfo.memory?.total_gb} GB</p>
                  <p>Available: {systemInfo.memory?.available_gb} GB</p>
                </div>
              </div>
              {systemInfo.apple_silicon && (
                <div>
                  <h4 className="font-semibold mb-2">Apple Silicon</h4>
                  <div className="text-sm space-y-1">
                    <p>Chip: {systemInfo.apple_silicon?.chip_name}</p>
                    {systemInfo.apple_silicon?.gpu_cores > 0 && (
                      <p>GPU Cores: {systemInfo.apple_silicon.gpu_cores}</p>
                    )}
                    {systemInfo.apple_silicon?.neural_engine_cores > 0 && (
                      <p>Neural Engine: {systemInfo.apple_silicon.neural_engine_cores} cores</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>CPU Usage Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="displayTime" 
                  tick={{ fontSize: 12 }}
                  interval="preserveStartEnd"
                />
                <YAxis domain={[0, 100]} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="cpu_usage" 
                  stroke="#8884d8" 
                  strokeWidth={2}
                  name="CPU Usage"
                  activeDot={{ r: 4 }} 
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Memory Usage Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="displayTime" 
                  tick={{ fontSize: 12 }}
                  interval="preserveStartEnd"
                />
                <YAxis domain={[0, 100]} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="memory_usage" 
                  stroke="#82ca9d" 
                  fill="#82ca9d"
                  fillOpacity={0.3}
                  name="Memory Usage"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Temperature Monitoring</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="displayTime" 
                  tick={{ fontSize: 12 }}
                  interval="preserveStartEnd"
                />
                <YAxis domain={[30, 90]} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="temperature" 
                  stroke="#ff7300" 
                  strokeWidth={2}
                  name="Temperature (°C)"
                  activeDot={{ r: 4 }} 
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Network & Disk I/O</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="displayTime" 
                  tick={{ fontSize: 12 }}
                  interval="preserveStartEnd"
                />
                <YAxis />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="disk_read_mb" 
                  stroke="#8884d8" 
                  strokeWidth={2}
                  name="Disk Read (MB)"
                  activeDot={{ r: 4 }} 
                />
                <Line 
                  type="monotone" 
                  dataKey="disk_write_mb" 
                  stroke="#82ca9d" 
                  strokeWidth={2}
                  name="Disk Write (MB)"
                  activeDot={{ r: 4 }} 
                />
                <Line 
                  type="monotone" 
                  dataKey="network_sent_mb" 
                  stroke="#ff7300" 
                  strokeWidth={2}
                  name="Network Sent (MB)"
                  activeDot={{ r: 4 }} 
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Apple Silicon Specific Metrics */}
      {appleSiliconMetrics && appleSiliconMetrics.benchmarks && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Zap className="h-5 w-5 mr-2" />
              Apple Silicon Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {appleSiliconMetrics.benchmarks.cpu && (
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-semibold mb-2">CPU Performance</h4>
                  <p className="text-2xl font-bold text-blue-600">
                    {appleSiliconMetrics.benchmarks.cpu.score?.toFixed(1)}
                  </p>
                  <p className="text-sm text-gray-600">Score</p>
                </div>
              )}
              {appleSiliconMetrics.benchmarks.gpu && (
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <h4 className="font-semibold mb-2">GPU Performance</h4>
                  <p className="text-2xl font-bold text-green-600">
                    {appleSiliconMetrics.benchmarks.gpu.score?.toFixed(1)}
                  </p>
                  <p className="text-sm text-gray-600">Score</p>
                </div>
              )}
              {appleSiliconMetrics.benchmarks.neural_engine && (
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <h4 className="font-semibold mb-2">Neural Engine</h4>
                  <p className="text-2xl font-bold text-purple-600">
                    {appleSiliconMetrics.benchmarks.neural_engine.tops?.toFixed(1)} TOPS
                  </p>
                  <p className="text-sm text-gray-600">Performance</p>
                </div>
              )}
              {appleSiliconMetrics.benchmarks.memory && (
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <h4 className="font-semibold mb-2">Memory Bandwidth</h4>
                  <p className="text-2xl font-bold text-orange-600">
                    {appleSiliconMetrics.benchmarks.memory.bandwidth_mb_s?.toFixed(0)}
                  </p>
                  <p className="text-sm text-gray-600">MB/s</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default PerformanceDashboard;
