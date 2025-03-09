import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function Login({ setToken }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      const res = await axios.post("http://192.168.1.137:5000/login", { username, password });
      const token = res.data.token;
      setToken(token);
      localStorage.setItem("authToken", token); // Guarda el token en localStorage
      navigate("/topics");
    } catch (err) {
      setError("Credenciales incorrectas");
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleLogin();
    }
  };

  return (
    <div className="auth-box">
      <h2>Iniciar Sesión</h2>
      <input
        type="text"
        placeholder="Usuario"
        onChange={(e) => setUsername(e.target.value)}
        onKeyPress={handleKeyPress}
      />
      <input
        type="password"
        placeholder="Contraseña"
        onChange={(e) => setPassword(e.target.value)}
        onKeyPress={handleKeyPress}
      />
      <button onClick={handleLogin}>Entrar</button>
      {error && <p className="error">{error}</p>}
      <p>¿No tienes cuenta? <span onClick={() => navigate("/register")} className="link">Regístrate</span></p>
    </div>
  );
}