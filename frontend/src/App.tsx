import { useState, useEffect } from 'react'
import Login from './Login'
import Cadastro from './Cadastro'
import Chat from './Chat'
import ChatsList from './ChatsList'

function App() {
  const [currentPage, setCurrentPage] = useState<'login' | 'cadastro' | 'chats' | 'chat'>('login')

  // Detectar mudanças no hash da URL
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1) // Remove o #

      if (hash.startsWith('chat?')) {
        setCurrentPage('chat')
      } else if (hash === 'chats') {
        setCurrentPage('chats')
      } else if (hash === 'cadastro') {
        setCurrentPage('cadastro')
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

  return (
    <>
      {currentPage === 'login' && <Login />}
      {currentPage === 'cadastro' && <Cadastro />}
      {currentPage === 'chats' && <ChatsList />}
      {currentPage === 'chat' && <Chat />}
    </>
  )
}

export default App
