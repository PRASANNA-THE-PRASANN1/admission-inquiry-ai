import React, { useState, useEffect } from 'react'
import { Toaster } from 'react-hot-toast'
import { MessageCircle, Mic, BarChart3, Settings, Info, Phone, Mail } from 'lucide-react'
import ChatInterface from './components/ChatInterface'
import VoiceInterface from './components/VoiceInterface'
import Analytics from './components/Analytics'
import './styles/index.css'

function App() {
  const [activeTab, setActiveTab] = useState('chat')
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  const [isConnected, setIsConnected] = useState(false)
  const [systemStatus, setSystemStatus] = useState('checking')

  // Check system health on component mount
  useEffect(() => {
    checkSystemHealth()
  }, [])

  const checkSystemHealth = async () => {
    try {
      const response = await fetch('/api/health')
      if (response.ok) {
        setIsConnected(true)
        setSystemStatus('healthy')
      } else {
        setIsConnected(false)
        setSystemStatus('error')
      }
    } catch (error) {
      console.error('Health check failed:', error)
      setIsConnected(false)
      setSystemStatus('error')
    }
  }

  const tabs = [
    { id: 'chat', label: 'Chat', icon: MessageCircle, component: ChatInterface },
    { id: 'voice', label: 'Voice', icon: Mic, component: VoiceInterface },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, component: Analytics },
  ]

  // Get the active component (properly cased)
  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <div className="bg-blue-600 p-2 rounded-lg">
                <MessageCircle className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  AI Admission Assistant
                </h1>
                <p className="text-sm text-gray-500">
                  Get instant answers to your admission questions
                </p>
              </div>
            </div>
            
            {/* System Status */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  systemStatus === 'healthy' ? 'bg-green-500' : 
                  systemStatus === 'checking' ? 'bg-yellow-500' : 'bg-red-500'
                }`} />
                <span className="text-sm text-gray-600">
                  {systemStatus === 'healthy' ? 'Online' : 
                   systemStatus === 'checking' ? 'Connecting...' : 'Offline'}
                </span>
              </div>
              
              {/* Quick Contact */}
              <div className="hidden md:flex items-center space-x-3 text-sm text-gray-600">
                <div className="flex items-center space-x-1">
                  <Phone className="h-4 w-4" />
                  <span>(555) 123-4567</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Mail className="h-4 w-4" />
                  <span>admissions@university.edu</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="mb-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {!isConnected && (
            <div className="bg-red-50 border-b border-red-200 px-6 py-4">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-red-500 rounded-full" />
                <p className="text-red-700 text-sm">
                  Connection to server lost. Some features may not work properly.
                  <button 
                    onClick={checkSystemHealth}
                    className="ml-2 text-red-600 underline hover:text-red-800"
                  >
                    Retry connection
                  </button>
                </p>
              </div>
            </div>
          )}
          
          <div className="p-6">
            {ActiveComponent && (
              <ActiveComponent 
                sessionId={sessionId} 
                isConnected={isConnected}
                onConnectionChange={setIsConnected}
              />
            )}
          </div>
        </div>

        {/* Quick Help */}
        <div className="mt-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-6 text-white">
          <div className="flex items-start space-x-4">
            <div className="bg-white/20 p-2 rounded-lg">
              <Info className="h-6 w-6" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold mb-2">How can I help you today?</h3>
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div>
                  <h4 className="font-medium mb-2">I can answer questions about:</h4>
                  <ul className="space-y-1 text-blue-100">
                    <li>• Admission requirements and deadlines</li>
                    <li>• Tuition fees and financial aid</li>
                    <li>• Academic programs and majors</li>
                    <li>• Campus visits and housing</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Getting started:</h4>
                  <ul className="space-y-1 text-blue-100">
                    <li>• Use the Chat tab for text conversations</li>
                    <li>• Try Voice for hands-free interaction</li>
                    <li>• Check Analytics for system insights</li>
                    <li>• Ask questions in natural language</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sample Questions */}
        <div className="mt-6 grid md:grid-cols-3 gap-4">
          {[
            "What are the admission requirements?",
            "When is the application deadline?",
            "How much does tuition cost?"
          ].map((question, index) => (
            <button
              key={index}
              onClick={() => {
                setActiveTab('chat')
                // This will be handled by the ChatInterface component
                setTimeout(() => {
                  const event = new CustomEvent('sampleQuestion', { 
                    detail: { question } 
                  })
                  window.dispatchEvent(event)
                }, 100)
              }}
              className="bg-white p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-sm transition-all text-left text-sm text-gray-700 hover:text-blue-600"
            >
              <div className="flex items-center space-x-2">
                <MessageCircle className="h-4 w-4 text-blue-500" />
                <span>"{question}"</span>
              </div>
            </button>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-50 border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Contact Information</h3>
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-center space-x-2">
                  <Phone className="h-4 w-4" />
                  <span>(555) 123-4567</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Mail className="h-4 w-4" />
                  <span>admissions@university.edu</span>
                </div>
                <p>123 University Avenue<br />Springfield, IL 62701</p>
              </div>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Office Hours</h3>
              <div className="text-sm text-gray-600 space-y-1">
                <p>Monday - Friday: 8:00 AM - 5:00 PM</p>
                <p>Saturday: 9:00 AM - 1:00 PM</p>
                <p>Sunday: Closed</p>
                <p className="mt-2 text-blue-600">Virtual appointments available</p>
              </div>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Quick Links</h3>
              <div className="space-y-2 text-sm">
                <a href="#" className="block text-blue-600 hover:text-blue-800">
                  Application Portal
                </a>
                <a href="#" className="block text-blue-600 hover:text-blue-800">
                  Financial Aid
                </a>
                <a href="#" className="block text-blue-600 hover:text-blue-800">
                  Campus Tours
                </a>
                <a href="#" className="block text-blue-600 hover:text-blue-800">
                  Academic Programs
                </a>
              </div>
            </div>
          </div>
          
          <div className="border-t border-gray-200 mt-8 pt-8 text-center text-sm text-gray-500">
            <p>© 2024 Springfield University. All rights reserved. | 
              <span className="ml-2">Powered by AI Assistant v1.0</span>
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App