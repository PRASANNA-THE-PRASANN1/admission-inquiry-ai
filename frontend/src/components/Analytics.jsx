import React, { useState, useEffect } from 'react'
import { BarChart3, Users, MessageCircle, Zap, TrendingUp, Clock, Target, AlertCircle, RefreshCw } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts'
import { format, subDays } from 'date-fns'
import toast from 'react-hot-toast'

const Analytics = ({ sessionId, isConnected }) => {
  const [analyticsData, setAnalyticsData] = useState(null)
  const [timeRange, setTimeRange] = useState(7) // Days
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)

  useEffect(() => {
    fetchAnalytics()
  }, [timeRange])

  const fetchAnalytics = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`/api/analytics?days=${timeRange}`)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      setAnalyticsData(data.analytics)
      setLastUpdated(new Date())
      
    } catch (error) {
      console.error('Error fetching analytics:', error)
      toast.error('Failed to load analytics data')
    } finally {
      setIsLoading(false)
    }
  }

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#F97316']

  // Process data for charts
  const processIntentData = () => {
    if (!analyticsData?.intent_distribution) return []
    
    return Object.entries(analyticsData.intent_distribution)
      .map(([intent, count]) => ({
        name: intent.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value: count,
        percentage: Math.round((count / analyticsData.total_interactions) * 100)
      }))
      .sort((a, b) => b.value - a.value)
  }

  const processChannelData = () => {
    if (!analyticsData?.channel_distribution) return []
    
    return Object.entries(analyticsData.channel_distribution).map(([channel, count]) => ({
      name: channel.charAt(0).toUpperCase() + channel.slice(1),
      value: count
    }))
  }

  const processDailyData = () => {
    if (!analyticsData?.daily_interactions) return []
    
    const days = []
    for (let i = timeRange - 1; i >= 0; i--) {
      const date = format(subDays(new Date(), i), 'yyyy-MM-dd')
      const count = analyticsData.daily_interactions[date] || 0
      days.push({
        date: format(subDays(new Date(), i), 'MMM dd'),
        interactions: count
      })
    }
    return days
  }

  const processConfidenceData = () => {
    if (!analyticsData?.average_confidence) return []
    
    return Object.entries(analyticsData.average_confidence)
      .map(([intent, confidence]) => ({
        intent: intent.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        confidence: Math.round(confidence * 100)
      }))
      .sort((a, b) => b.confidence - a.confidence)
  }

  const MetricCard = ({ title, value, change, icon: Icon, color = 'blue' }) => (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {change !== undefined && (
            <p className={`text-sm mt-1 ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {change >= 0 ? '+' : ''}{change}% from last period
            </p>
          )}
        </div>
        <div className={`p-3 rounded-full bg-${color}-100`}>
          <Icon className={`h-6 w-6 text-${color}-600`} />
        </div>
      </div>
    </div>
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="loading-animation mx-auto mb-4"></div>
          <p className="text-gray-600">Loading analytics data...</p>
        </div>
      </div>
    )
  }

  if (!analyticsData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">Failed to load analytics data</p>
          <button
            onClick={fetchAnalytics}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  const intentData = processIntentData()
  const channelData = processChannelData()
  const dailyData = processDailyData()
  const confidenceData = processConfidenceData()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h2>
          <p className="text-gray-600 mt-1">
            System insights for the last {timeRange} days
            {lastUpdated && (
              <span className="ml-2 text-sm">
                • Last updated: {format(lastUpdated, 'HH:mm')}
              </span>
            )}
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          {/* Time Range Selector */}
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          
          {/* Refresh Button */}
          <button
            onClick={fetchAnalytics}
            disabled={isLoading}
            className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Interactions"
          value={analyticsData.total_interactions?.toLocaleString() || '0'}
          icon={MessageCircle}
          color="blue"
        />
        <MetricCard
          title="Unique Sessions"
          value={analyticsData.unique_sessions?.toLocaleString() || '0'}
          icon={Users}
          color="green"
        />
        <MetricCard
          title="Avg Response Time"
          value={`${analyticsData.average_processing_time?.toFixed(2) || '0.00'}s`}
          icon={Clock}
          color="yellow"
        />
        <MetricCard
          title="System Status"
          value={isConnected ? 'Online' : 'Offline'}
          icon={isConnected ? Zap : AlertCircle}
          color={isConnected ? 'green' : 'red'}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Interactions Chart */}
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Interactions</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="interactions" 
                stroke="#3B82F6" 
                strokeWidth={2}
                dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Intent Distribution Pie Chart */}
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Popular Topics</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={intentData.slice(0, 6)} // Show top 6
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percentage }) => `${name} (${percentage}%)`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {intentData.slice(0, 6).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Channel Distribution */}
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Communication Channels</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={channelData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#10B981" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Confidence Scores */}
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Confidence by Topic</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={confidenceData} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 100]} />
              <YAxis dataKey="intent" type="category" width={100} />
              <Tooltip formatter={(value) => [`${value}%`, 'Confidence']} />
              <Bar dataKey="confidence" fill="#8B5CF6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Intents Table */}
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Discussion Topics</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2">Topic</th>
                  <th className="text-right py-2">Count</th>
                  <th className="text-right py-2">Percentage</th>
                </tr>
              </thead>
              <tbody>
                {intentData.slice(0, 8).map((item, index) => (
                  <tr key={index} className="border-b border-gray-100">
                    <td className="py-2">{item.name}</td>
                    <td className="text-right py-2">{item.value}</td>
                    <td className="text-right py-2">{item.percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Entity Distribution */}
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Extracted Information Types</h3>
          <div className="space-y-3">
            {analyticsData.entity_distribution && Object.entries(analyticsData.entity_distribution).length > 0 ? (
              Object.entries(analyticsData.entity_distribution)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 6)
                .map(([entityType, count]) => (
                  <div key={entityType} className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 capitalize">
                      {entityType.replace('_', ' ')}
                    </span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ 
                            width: `${Math.min(100, (count / Math.max(...Object.values(analyticsData.entity_distribution))) * 100)}%` 
                          }}
                        />
                      </div>
                      <span className="text-sm font-medium w-8 text-right">{count}</span>
                    </div>
                  </div>
                ))
            ) : (
              <p className="text-gray-500 text-sm">No entity data available</p>
            )}
          </div>
        </div>
      </div>

      {/* System Health */}
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className={`w-12 h-12 rounded-full mx-auto mb-2 flex items-center justify-center ${
              isConnected ? 'bg-green-100' : 'bg-red-100'
            }`}>
              {isConnected ? (
                <Zap className="h-6 w-6 text-green-600" />
              ) : (
                <AlertCircle className="h-6 w-6 text-red-600" />
              )}
            </div>
            <p className="text-sm font-medium text-gray-900">Connection</p>
            <p className={`text-xs ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
              {isConnected ? 'Online' : 'Offline'}
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 rounded-full bg-blue-100 mx-auto mb-2 flex items-center justify-center">
              <Target className="h-6 w-6 text-blue-600" />
            </div>
            <p className="text-sm font-medium text-gray-900">Overall Accuracy</p>
            <p className="text-xs text-blue-600">
              {analyticsData.average_confidence ? 
                `${Math.round(Object.values(analyticsData.average_confidence).reduce((a, b) => a + b, 0) / Object.values(analyticsData.average_confidence).length * 100)}%` : 
                'N/A'
              }
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 rounded-full bg-purple-100 mx-auto mb-2 flex items-center justify-center">
              <TrendingUp className="h-6 w-6 text-purple-600" />
            </div>
            <p className="text-sm font-medium text-gray-900">Daily Average</p>
            <p className="text-xs text-purple-600">
              {Math.round(analyticsData.total_interactions / timeRange)} interactions
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Analytics