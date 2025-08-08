import React, { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Volume2, VolumeX, Play, Pause, RotateCcw, Download } from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

const VoiceInterface = ({ sessionId, isConnected }) => {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [conversations, setConversations] = useState([])
  const [currentAudio, setCurrentAudio] = useState(null)
  const [audioPermission, setAudioPermission] = useState(null)

  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const timerRef = useRef(null)
  const audioRef = useRef(null)
  const streamRef = useRef(null)

  // Check for microphone permission on component mount
  useEffect(() => {
    checkAudioPermission()
    return () => {
      stopRecording()
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

  const checkAudioPermission = async () => {
    try {
      const permission = await navigator.permissions.query({ name: 'microphone' })
      setAudioPermission(permission.state)
      
      permission.addEventListener('change', () => {
        setAudioPermission(permission.state)
      })
    } catch (error) {
      console.error('Error checking audio permission:', error)
    }
  }

  const startRecording = async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('MediaDevices API not supported')
      }

      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000
        } 
      })
      
      streamRef.current = stream
      audioChunksRef.current = []

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = processRecording

      mediaRecorder.start(1000) // Collect data every second
      setIsRecording(true)
      setRecordingTime(0)
      
      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)

      toast.success('Recording started')

    } catch (error) {
      console.error('Error starting recording:', error)
      toast.error('Failed to start recording. Please check microphone permissions.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }

      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
        streamRef.current = null
      }
    }
  }

  const processRecording = async () => {
    if (audioChunksRef.current.length === 0) {
      toast.error('No audio recorded')
      return
    }

    setIsProcessing(true)

    try {
      // Create audio blob
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
      
      // Create form data
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.webm')
      formData.append('session_id', sessionId)

      // Send to backend
      const response = await fetch('/api/voice', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      // Create conversation entry
      const conversation = {
        id: Date.now().toString(),
        timestamp: new Date(),
        transcript: data.transcript,
        response: data.response,
        audioUrl: data.audio_url,
        intent: data.intent,
        confidence: data.confidence,
        recordingDuration: recordingTime
      }

      setConversations(prev => [...prev, conversation])
      setRecordingTime(0)
      
      // Auto-play response if not muted
      if (!isMuted && data.audio_url) {
        playAudio(data.audio_url)
      }

      toast.success('Voice message processed successfully')

    } catch (error) {
      console.error('Error processing recording:', error)
      toast.error('Failed to process voice message')
    } finally {
      setIsProcessing(false)
    }
  }

  const playAudio = async (audioUrl) => {
    try {
      if (currentAudio) {
        currentAudio.pause()
        setCurrentAudio(null)
      }

      const audio = new Audio(`/api${audioUrl}`)
      audioRef.current = audio
      setCurrentAudio(audio)

      audio.onloadstart = () => setIsPlaying(true)
      audio.onended = () => {
        setIsPlaying(false)
        setCurrentAudio(null)
      }
      audio.onerror = () => {
        setIsPlaying(false)
        setCurrentAudio(null)
        toast.error('Failed to play audio response')
      }

      await audio.play()

    } catch (error) {
      console.error('Error playing audio:', error)
      toast.error('Failed to play audio')
      setIsPlaying(false)
    }
  }

  const pauseAudio = () => {
    if (currentAudio) {
      currentAudio.pause()
      setIsPlaying(false)
    }
  }

  const downloadAudio = (audioUrl, filename) => {
    const link = document.createElement('a')
    link.href = `/api${audioUrl}`
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const clearConversations = () => {
    setConversations([])
    if (currentAudio) {
      currentAudio.pause()
      setCurrentAudio(null)
    }
    toast.success('Voice conversations cleared')
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Check if browser supports required APIs
  const isSupported = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder)

  if (!isSupported) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="bg-yellow-100 p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
            <MicOff className="h-8 w-8 text-yellow-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Voice features not supported
          </h3>
          <p className="text-gray-600 max-w-md">
            Your browser doesn't support the required audio APIs for voice interaction. 
            Please use the chat interface instead or try a modern browser.
          </p>
        </div>
      </div>
    )
  }

  if (audioPermission === 'denied') {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="bg-red-100 p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
            <MicOff className="h-8 w-8 text-red-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Microphone access denied
          </h3>
          <p className="text-gray-600 max-w-md mb-4">
            Please enable microphone access in your browser settings to use voice features.
          </p>
          <button
            onClick={checkAudioPermission}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Check Permissions Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[600px]">
      {/* Voice Control Header */}
      <div className="flex justify-between items-center p-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="bg-purple-100 p-2 rounded-full">
            <Mic className="h-5 w-5 text-purple-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Voice Assistant</h3>
            <p className="text-sm text-gray-500">
              {isConnected ? 'Speak naturally for voice interaction' : 'Connection issues'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsMuted(!isMuted)}
            className={`p-2 rounded-lg transition-colors ${
              isMuted ? 'text-red-600 bg-red-50' : 'text-gray-500 hover:text-purple-600 hover:bg-purple-50'
            }`}
            title={isMuted ? 'Unmute responses' : 'Mute responses'}
          >
            {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
          </button>
          <button
            onClick={clearConversations}
            className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            title="Clear voice conversations"
          >
            <RotateCcw className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Recording Controls */}
      <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50">
        <div className="flex flex-col items-center space-y-4">
          {/* Recording Button */}
          <button
            onClick={isRecording ? stopRecording : startRecording}
            disabled={!isConnected || isProcessing}
            className={`w-20 h-20 rounded-full flex items-center justify-center transition-all duration-200 ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
                : isProcessing
                ? 'bg-gray-400 cursor-not-allowed text-white'
                : 'bg-purple-600 hover:bg-purple-700 text-white hover:scale-105'
            }`}
          >
            {isProcessing ? (
              <div className="loading-animation"></div>
            ) : isRecording ? (
              <MicOff className="h-8 w-8" />
            ) : (
              <Mic className="h-8 w-8" />
            )}
          </button>

          {/* Status Display */}
          <div className="text-center">
            {isRecording && (
              <div className="flex items-center space-x-2">
                <div className="voice-wave"></div>
                <div className="voice-wave"></div>
                <div className="voice-wave"></div>
                <div className="voice-wave"></div>
                <div className="voice-wave"></div>
              </div>
            )}
            
            <p className="text-sm font-medium text-gray-700 mt-2">
              {isProcessing ? 'Processing your voice...' :
               isRecording ? `Recording: ${formatTime(recordingTime)}` :
               'Tap to start recording'}
            </p>
            
            {isRecording && (
              <p className="text-xs text-gray-500 mt-1">
                Tap again to stop and send
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {conversations.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <Mic className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No voice conversations yet</p>
              <p className="text-sm mt-1">Start recording to begin</p>
            </div>
          </div>
        ) : (
          <div className="p-4 space-y-4">
            {conversations.map((conversation) => (
              <div key={conversation.id} className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                {/* Conversation Header */}
                <div className="flex justify-between items-start mb-3">
                  <div className="text-xs text-gray-500">
                    {format(conversation.timestamp, 'MMM dd, HH:mm')} • 
                    Duration: {formatTime(conversation.recordingDuration)}
                  </div>
                  {conversation.audioUrl && (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => downloadAudio(conversation.audioUrl, `response_${conversation.id}.wav`)}
                        className="text-gray-400 hover:text-blue-600"
                        title="Download audio response"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                      <button
                        onClick={isPlaying ? pauseAudio : () => playAudio(conversation.audioUrl)}
                        className="text-gray-400 hover:text-purple-600"
                        title={isPlaying ? 'Pause' : 'Play response'}
                      >
                        {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                      </button>
                    </div>
                  )}
                </div>

                {/* User Transcript */}
                <div className="mb-3">
                  <div className="flex items-center space-x-2 mb-1">
                    <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                      <Mic className="h-3 w-3 text-blue-600" />
                    </div>
                    <span className="text-sm font-medium text-gray-700">You said:</span>
                  </div>
                  <div className="bg-blue-50 p-3 rounded-lg">
                    <p className="text-sm text-gray-800">
                      {conversation.transcript || 'Could not transcribe audio'}
                    </p>
                  </div>
                </div>

                {/* Assistant Response */}
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <div className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center">
                      <Volume2 className="h-3 w-3 text-purple-600" />
                    </div>
                    <span className="text-sm font-medium text-gray-700">Assistant replied:</span>
                    {conversation.intent && conversation.confidence && (
                      <span className="text-xs text-gray-500">
                        ({conversation.intent}, {Math.round(conversation.confidence * 100)}% confident)
                      </span>
                    )}
                  </div>
                  <div className="bg-purple-50 p-3 rounded-lg">
                    <p className="text-sm text-gray-800">{conversation.response}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Connection Status */}
      {!isConnected && (
        <div className="p-4 bg-red-50 border-t border-red-200">
          <p className="text-sm text-red-600 text-center">
            Connection lost. Voice features may not work properly.
          </p>
        </div>
      )}
    </div>
  )
}

export default VoiceInterface