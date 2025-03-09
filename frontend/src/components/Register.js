import React, { useState } from "react";
import axios from "axios";

export default function Register({ setView }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleRegister = async () => {
    await axios.post("http://192.168.1.134:5000/register", { username, password });
    setView("login");
  };

  return (
    <div className="auth-box">
      <h2>Registro</h2>
      <input type="text" placeholder="Usuario" onChange={(e) => setUsername(e.target.value)} />
      <input type="password" placeholder="Contraseña" onChange={(e) => setPassword(e.target.value)} />
      <button onClick={handleRegister}>Registrar</button>
      <p>¿Ya tienes cuenta? <span onClick={() => setView("login")} className="link">Inicia sesión</span></p>
    </div>
  );
}