import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import { handleGoogleRedirect } from './lib/auth'

// Web'de Google'dan geri donus: hash'teki id_token'i isle, oturumu ac.
// App zaten stored user'ı okudugu icin sonuc beklemeye gerek yok.
void handleGoogleRedirect()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
