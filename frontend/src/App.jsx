import { useState } from 'react'
import Landing from './pages/Landing.jsx'
import Home from './pages/Home.jsx'

export default function App() {
  const [started, setStarted] = useState(false)

  if (!started) {
    return <Landing onStart={() => setStarted(true)} />
  }

  return <Home onBack={() => setStarted(false)} />
}