import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './components/App';
import './styles/styles.css';

// Obtén el contenedor donde se montará la aplicación
const container = document.getElementById('root');

// Crea un root y renderiza el componente App
const root = createRoot(container);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);