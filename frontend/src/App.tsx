import { useState, useEffect } from 'react'
import Login from './Login'
import Cadastro from './Cadastro'
import ChatsList from './ChatsList'
import Chat from './Chat'

type PageType = 'login' | 'cadastro' | 'chats' | 'chat'

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('login')

  // Detectar mudanças no hash da URL
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1) // Remove o #

      if (hash === 'cadastro') {
        setCurrentPage('cadastro')
      } else if (hash === 'chats') {
        setCurrentPage('chats')
      } else if (hash.startsWith('chat?')) {
        setCurrentPage('chat')
      } else {
        setCurrentPage('login')
      }
    }

    // Verificar hash inicial
    handleHashChange()

    // Escutar mudanças no hash
    window.addEventListener('hashchange', handleHashChange)

    return () => {
      window.removeEventListener('hashchange', handleHashChange)
    }
  }, [])

  const renderPage = () => {
    switch (currentPage) {
      case 'cadastro':
        return <Cadastro />
      case 'chats':
        return <ChatsList />
      case 'chat':
        return <Chat />
      default:
        return <Login />
    }
  }

  return renderPage()
}

export default App
