import React, { useState, useEffect, useRef } from 'react'
import { Send, User, Bot, Loader2, ThumbsUp, ThumbsDown, Copy, RotateCcw, Mail } from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

const ChatInterface = ({ sessionId, isConnected }) => {
  const [messages, setMessages] = useState([])
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Initial welcome message
  useEffect(() => {
    const welcomeMessage = {
      id: 'welcome',
      type: 'bot',
      content: "Hello! I'm your AI admission assistant. I can help you with information about admission requirements, deadlines, tuition, programs, and more. What would you like to know?",
      timestamp: new Date(),
      intent: 'greeting',
      confidence: 1.0
    }
    setMessages([welcomeMessage])
  }, [])

  // Listen for sample questions from parent component
  useEffect(() => {
    const handleSampleQuestion = (event) => {
      const { question } = event.detail
      setInputText(question)
      // Auto-focus input after setting question
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus()
        }
      }, 100)
    }

    window.addEventListener('sampleQuestion', handleSampleQuestion)
    return () => window.removeEventListener('sampleQuestion', handleSampleQuestion)
  }, [])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const sendMessage = async () => {
    if (!inputText.trim() || isLoading || !isConnected) return

    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputText.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputText('')
    setIsLoading(true)
    setIsTyping(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: sessionId
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      // Simulate typing delay for better UX
      setTimeout(() => {
        const botMessage = {
          id: (Date.now() + 1).toString(),
          type: 'bot',
          content: data.response,
          timestamp: new Date(),
          intent: data.intent,
          confidence: data.confidence
        }

        setMessages(prev => [...prev, botMessage])
        setIsTyping(false)
        setIsLoading(false)
      }, 1000)

    } catch (error) {
      console.error('Error sending message:', error)
      
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: "I'm sorry, I'm having trouble connecting right now. Please try again or contact our admissions office directly at (555) 123-4567.",
        timestamp: new Date(),
        isError: true
      }

      setMessages(prev => [...prev, errorMessage])
      setIsTyping(false)
      setIsLoading(false)
      
      toast.error('Failed to send message. Please try again.')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const copyMessage = (content) => {
    navigator.clipboard.writeText(content)
    toast.success('Message copied to clipboard')
  }

  const retryMessage = (messageIndex) => {
    const userMessage = messages[messageIndex - 1]
    if (userMessage && userMessage.type === 'user') {
      setInputText(userMessage.content)
      // Remove the failed bot response
      setMessages(prev => prev.slice(0, messageIndex))
    }
  }

  const sendFeedback = async (messageId, type) => {
    try {
      await fetch('/api/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message_id: messageId,
          feedback_type: type
        })
      })
      
      toast.success(`Thank you for your ${type === 'positive' ? 'positive' : 'negative'} feedback!`)
    } catch (error) {
      console.error('Error sending feedback:', error)
    }
  }

  const clearChat = () => {
    const welcomeMessage = messages[0]
    setMessages([welcomeMessage])
    toast.success('Chat cleared')
  }

  const requestFollowUp = () => {
    const emailModal = document.createElement('div')
    emailModal.innerHTML = `
      <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
          <h3 class="text-lg font-semibold mb-4">Request Follow-up Email</h3>
          <input type="email" placeholder="Your email address" class="w-full p-3 border rounded-lg mb-4" id="followup-email">
          <input type="text" placeholder="Your name" class="w-full p-3 border rounded-lg mb-4" id="followup-name">
          <div class="flex space-x-3">
            <button onclick="this.closest('.fixed').remove()" class="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg">Cancel</button>
            <button onclick="sendFollowUp()" class="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg">Send</button>
          </div>
        </div>
      </div>
    `
    document.body.appendChild(emailModal)

    window.sendFollowUp = async () => {
      const email = document.getElementById('followup-email').value
      const name = document.getElementById('followup-name').value
      
      if (!email || !name) {
        toast.error('Please fill in all fields')
        return
      }

      try {
        await fetch('/api/followup', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email,
            name,
            session_id: sessionId,
            inquiry_type: 'general'
          })
        })
        
        toast.success('Follow-up email will be sent shortly!')
        emailModal.remove()
      } catch (error) {
        console.error('Error requesting follow-up:', error)
        toast.error('Failed to send follow-up request')
      }
    }
  }

  return (
    <div className="flex flex-col h-[600px]">
      {/* Chat Header */}
      <div className="flex justify-between items-center p-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="bg-blue-100 p-2 rounded-full">
            <Bot className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">AI Assistant</h3>
            <p className="text-sm text-gray-500">
              {isConnected ? 'Online and ready to help' : 'Connection issues'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={requestFollowUp}
            className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            title="Request follow-up email"
          >
            <Mail className="h-5 w-5" />
          </button>
          <button
            onClick={clearChat}
            className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            title="Clear chat"
          >
            <RotateCcw className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        {messages.map((message, index) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} message-enter`}
          >
            <div className={`flex max-w-[80%] ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'} items-start space-x-3`}>
              {/* Avatar */}
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                message.type === 'user' ? 'bg-blue-600' : message.isError ? 'bg-red-100' : 'bg-gray-100'
              }`}>
                {message.type === 'user' ? (
                  <User className="h-4 w-4 text-white" />
                ) : (
                  <Bot className={`h-4 w-4 ${message.isError ? 'text-red-600' : 'text-gray-600'}`} />
                )}
              </div>

              {/* Message Content */}
              <div className={`flex flex-col ${message.type === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`px-4 py-2 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white'
                    : message.isError
                    ? 'bg-red-50 text-red-800 border border-red-200'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  
                  {/* Intent and Confidence (for bot messages) */}
                  {message.type === 'bot' && message.intent && message.confidence && !message.isError && (
                    <div className="mt-2 text-xs opacity-75">
                      Intent: {message.intent} ({Math.round(message.confidence * 100)}% confident)
                    </div>
                  )}
                </div>

                {/* Message Actions */}
                <div className="flex items-center space-x-2 mt-1">
                  <span className="text-xs text-gray-500">
                    {format(message.timestamp, 'HH:mm')}
                  </span>
                  
                  {message.type === 'bot' && !message.isError && (
                    <>
                      <button
                        onClick={() => copyMessage(message.content)}
                        className="text-xs text-gray-500 hover:text-blue-600"
                        title="Copy message"
                      >
                        <Copy className="h-3 w-3" />
                      </button>
                      <button
                        onClick={() => sendFeedback(message.id, 'positive')}
                        className="text-xs text-gray-500 hover:text-green-600"
                        title="This was helpful"
                      >
                        <ThumbsUp className="h-3 w-3" />
                      </button>
                      <button
                        onClick={() => sendFeedback(message.id, 'negative')}
                        className="text-xs text-gray-500 hover:text-red-600"
                        title="This wasn't helpful"
                      >
                        <ThumbsDown className="h-3 w-3" />
                      </button>
                    </>
                  )}
                  
                  {message.isError && (
                    <button
                      onClick={() => retryMessage(index)}
                      className="text-xs text-red-600 hover:text-red-800"
                      title="Retry this message"
                    >
                      <RotateCcw className="h-3 w-3" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Typing Indicator */}
        {isTyping && (
          <div className="flex justify-start">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                <Bot className="h-4 w-4 text-gray-600" />
              </div>
              <div className="bg-gray-100 px-4 py-2 rounded-lg">
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)} 
              onKeyPress={handleKeyPress}
              placeholder={isConnected ? "Type your question here..." : "Waiting for connection..."}
              disabled={!isConnected || isLoading}
              className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-500"
              rows="2"
              maxLength="500"
            />
            <div className="absolute bottom-2 right-2 text-xs text-gray-400">
              {inputText.length}/500
            </div>
          </div>
          
          <button
            onClick={sendMessage}
            disabled={!inputText.trim() || isLoading || !isConnected}
            className="flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </div>
        
        {!isConnected && (
          <p className="text-sm text-red-600 mt-2">
            Connection lost. Please check your internet connection and try again.
          </p>
        )}
      </div>
    </div>
  )
}

export default ChatInterface