// src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { configureStore } from '@reduxjs/toolkit'
import { Provider } from 'react-redux'
import { thunk } from 'redux-thunk'
import logger from 'redux-logger'
import rootReducer from './reducers'
import App from './App'
import './index.css'
import 'bootstrap/dist/css/bootstrap.min.css'

// Create Redux store - fixed to avoid duplicate middleware
const store = configureStore({
  reducer: rootReducer,
  // Use middleware in a way that prevents duplicates
  middleware: (getDefaultMiddleware) => {
    // Start with the default middleware (includes thunk already)
    const middleware = getDefaultMiddleware();
    
    // Only add logger in development
    if (process.env.NODE_ENV !== 'production') {
      return middleware.concat(logger);
    }
    
    return middleware;
  }
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </React.StrictMode>
)