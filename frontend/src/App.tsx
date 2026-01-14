import { useState, useEffect } from 'react'
import Login from './Login'
import Cadastro from './Cadastro'

function App() {
  const [currentPage, setCurrentPage] = useState<'login' | 'cadastro'>('login')

  // Detectar mudanças no hash da URL
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1) // Remove o #
      if (hash === 'cadastro') {
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

  return currentPage === 'login' ? <Login /> : <Cadastro />
}

export default App
