import { useState, useEffect, useRef } from 'react'
import Layout from '../components/Layout'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { MessageCircle, Send, HelpCircle, Book, Plus, Trash2, MessageSquare } from 'lucide-react'

function QnA() {
  const { currentFY } = useAuth()
  const [question, setQuestion] = useState('')
  const [conversations, setConversations] = useState([])
  const [currentConversation, setCurrentConversation] = useState(null)
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [loadingConversations, setLoadingConversations] = useState(false)
  const [commonQuestions, setCommonQuestions] = useState([])
  const messagesEndRef = useRef(null)

  useEffect(() => {
    fetchCommonQuestions()
    fetchConversations()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const fetchCommonQuestions = async () => {
    try {
      const response = await api.get('/qna/common-questions')
      setCommonQuestions(response.data.questions)
    } catch (error) {
      console.error('Failed to fetch common questions')
    }
  }

  const fetchConversations = async () => {
    setLoadingConversations(true)
    try {
      const response = await api.get('/qna/conversations')
      setConversations(response.data)
    } catch (error) {
      toast.error('Failed to load conversations')
    } finally {
      setLoadingConversations(false)
    }
  }

  const fetchConversationMessages = async (conversationId) => {
    try {
      const response = await api.get(`/qna/conversations/${conversationId}`)
      setMessages(response.data.messages || [])
      setCurrentConversation(response.data)
    } catch (error) {
      toast.error('Failed to load messages')
    }
  }

  const createNewChat = async () => {
    try {
      const response = await api.post('/qna/conversations', {
        title: 'New Chat'
      })
      setConversations([response.data, ...conversations])
      setCurrentConversation(response.data)
      setMessages([])
      toast.success('New chat created')
    } catch (error) {
      toast.error('Failed to create new chat')
    }
  }

  const deleteConversation = async (conversationId, e) => {
    e.stopPropagation()
    if (!confirm('Delete this conversation?')) return
    
    try {
      await api.delete(`/qna/conversations/${conversationId}`)
      setConversations(conversations.filter(c => c.id !== conversationId))
      
      if (currentConversation?.id === conversationId) {
        setCurrentConversation(null)
        setMessages([])
      }
      
      toast.success('Conversation deleted')
    } catch (error) {
      toast.error('Failed to delete conversation')
    }
  }

  const handleAsk = async (e) => {
    e?.preventDefault()
    
    if (!question.trim()) {
      toast.error('Please enter a question')
      return
    }

    const userMessage = {
      role: 'user',
      content: question,
      created_at: new Date().toISOString()
    }

    setMessages([...messages, userMessage])
    setLoading(true)
    const questionText = question
    setQuestion('')

    try {
      const response = await api.post('/qna/ask', {
        question: questionText,
        conversation_id: currentConversation?.id,
        financial_year: currentFY
      })

      const aiMessage = {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
        created_at: new Date().toISOString()
      }

      setMessages(prev => [...prev, aiMessage])
      
      // Update or set current conversation
      if (!currentConversation) {
        await fetchConversations()
        const newConv = await api.get(`/qna/conversations/${response.data.conversation_id}`)
        setCurrentConversation(newConv.data)
      } else {
        // Update conversation in list (it's now at the top)
        await fetchConversations()
      }
    } catch (error) {
      toast.error('Failed to get answer')
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleQuickQuestion = (q) => {
    setQuestion(q)
  }

  const selectConversation = (conversation) => {
    setCurrentConversation(conversation)
    fetchConversationMessages(conversation.id)
  }

  return (
    <Layout>
      <div className="flex h-[calc(100vh-120px)] gap-4">
        {/* Conversations Sidebar */}
        <div className="w-80 flex flex-col card overflow-hidden">
          {/* New Chat Button */}
          <button
            onClick={createNewChat}
            className="btn-primary flex items-center justify-center space-x-2 mb-4"
          >
            <Plus className="w-5 h-5" />
            <span>New Chat</span>
          </button>

          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto space-y-2">
            {loadingConversations ? (
              <div className="text-center text-gray-500 py-8">Loading...</div>
            ) : conversations.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <MessageSquare className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                <p className="text-sm">No conversations yet</p>
                <p className="text-xs mt-1">Start a new chat to begin</p>
              </div>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => selectConversation(conv)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors group ${
                    currentConversation?.id === conv.id
                      ? 'bg-primary-100 border-2 border-primary-600'
                      : 'bg-gray-50 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-gray-900 truncate text-sm">
                        {conv.title}
                      </h4>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(conv.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                    <button
                      onClick={(e) => deleteConversation(conv.id, e)}
                      className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 transition-opacity ml-2"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Info */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="bg-blue-50 rounded-lg p-3">
              <h4 className="font-semibold text-gray-900 text-sm mb-2">How it works</h4>
              <ul className="text-xs text-gray-600 space-y-1">
                <li>• Create new chats for different topics</li>
                <li>• All conversations are saved</li>
                <li>• Switch between chats anytime</li>
                <li>• Context-aware based on your data</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Chat Header */}
          {currentConversation && (
            <div className="card mb-4">
              <h2 className="font-semibold text-gray-900">{currentConversation.title}</h2>
              <p className="text-xs text-gray-500 mt-1">
                Started {new Date(currentConversation.created_at).toLocaleString()}
              </p>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 card overflow-y-auto mb-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <MessageCircle className="w-16 h-16 text-gray-300 mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {currentConversation ? 'No messages yet' : 'Start a Conversation'}
                </h3>
                <p className="text-gray-600">
                  Ask any question about Indian income tax, deductions, or filing requirements
                </p>

                {/* Common Questions */}
                {commonQuestions.length > 0 && (
                  <div className="mt-8 max-w-2xl">
                    <h4 className="font-semibold text-gray-900 mb-3">Common Questions</h4>
                    <div className="grid grid-cols-1 gap-2">
                      {commonQuestions.flatMap(cat => cat.questions).slice(0, 4).map((q, i) => (
                        <button
                          key={i}
                          onClick={() => handleQuickQuestion(q)}
                          className="text-left text-sm text-gray-600 hover:text-primary-600 hover:bg-primary-50 p-3 rounded-lg transition-colors border border-gray-200"
                        >
                          <HelpCircle className="w-4 h-4 inline mr-2" />
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message, index) => (
                  <MessageBubble key={index} message={message} />
                ))}
                {loading && (
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                      <MessageCircle className="w-5 h-5 text-primary-600" />
                    </div>
                    <div className="flex-1 bg-gray-100 rounded-lg p-4">
                      <div className="flex space-x-2">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input */}
          <form onSubmit={handleAsk} className="card">
            <div className="flex items-end space-x-3">
              <div className="flex-1">
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleAsk(e)
                    }
                  }}
                  placeholder="Ask your tax-related question... (Press Enter to send, Shift+Enter for new line)"
                  className="input-field resize-none"
                  rows="3"
                  disabled={loading}
                />
              </div>
              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="btn-primary flex items-center space-x-2 h-fit"
              >
                <Send className="w-5 h-5" />
                <span>Send</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </Layout>
  )
}

function MessageBubble({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser ? 'bg-primary-600' : 'bg-primary-100'
      }`}>
        {isUser ? (
          <span className="text-white text-sm font-semibold">You</span>
        ) : (
          <MessageCircle className="w-5 h-5 text-primary-600" />
        )}
      </div>
      
      <div className={`flex-1 max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`rounded-lg p-4 ${
          isUser ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-900'
        }`}>
          <p className="whitespace-pre-wrap">{message.content}</p>
          
          {message.sources && message.sources.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-300">
              <p className="text-xs font-semibold mb-1">Sources:</p>
              <ul className="text-xs space-y-1">
                {message.sources.map((source, index) => (
                  <li key={index}>• {source}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        <p className="text-xs text-gray-500 mt-1 px-2">
          {new Date(message.created_at).toLocaleTimeString()}
        </p>
      </div>
    </div>
  )
}

export default QnA

