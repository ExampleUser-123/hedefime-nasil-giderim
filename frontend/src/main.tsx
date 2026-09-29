import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'
import './index.css'
import { handleGoogleRedirect, hydrateAuthSession } from './lib/auth'

// Web'de Google'dan geri donus: hash'teki id_token'i isle, oturumu ac.
// App zaten stored user'ı okudugu icin sonuc beklemeye gerek yok.
async function boot() {
  await hydrateAuthSession()
  await handleGoogleRedirect()
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </React.StrictMode>,
  )
}

void boot()
