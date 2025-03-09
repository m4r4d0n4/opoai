import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
import Login from "./Login";
import Register from "./Register";
import Chat from "./Chat";
import Header from "./Header";
import TopicSelection from "./TopicSelection";
import "../styles/styles.css";

export default function App() {
  const [token, setToken] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);

  useEffect(() => {
    const savedToken = localStorage.getItem("authToken");
    if (savedToken) {
      setToken(savedToken);
    }
  }, []);

  return (
    <Router>
      <Header />
      <div className="container">
        <Routes>
          <Route path="/" element={!token ? <Navigate to="/login" /> : <Navigate to="/topics" />} />
          <Route path="/login" element={<Login setToken={setToken} />} />
          <Route path="/register" element={<Register />} />
          <Route path="/topics" element={token ? <TopicSelection setSelectedTopic={setSelectedTopic} /> : <Navigate to="/login" />} />
          <Route path="/chat" element={token && selectedTopic ? <Chat token={token} topic={selectedTopic} /> : <Navigate to="/topics" />} />
        </Routes>
      </div>
    </Router>
  );
}