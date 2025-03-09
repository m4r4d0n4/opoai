import React, { useState } from "react";
import axios from "axios";
import { marked } from "marked";
const { v4: uuidv4 } = require('uuid');
const sessionId = uuidv4();

export default function Chat({ token, topic }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await axios.post(
        `http://192.168.1.134:5678/webhook/opo-chat`, // Usa el campo db para la URL
        { sessionId: sessionId, message: input, file_id:topic.file_id }
      );

      const botMessage = { sender: "bot", text: response.data.output || "Sin respuesta" };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error enviando mensaje a n8n:", error);
    }

    setInput("");
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      sendMessage();
    }
  };

  return (
    <div className="chat-box">
      <h2>{topic.name}</h2>
      <ul className="messages">
        {messages.map((msg, index) => (
          <li key={index} className={msg.sender === "user" ? "user-message" : "bot-message"}>
            {msg.sender === "user" ? (
              msg.text
            ) : (
              <div dangerouslySetInnerHTML={{ __html: marked(msg.text) }} />
            )}
          </li>
        ))}
      </ul>
      <div className="input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Escribe un mensaje..."
        />
        <button onClick={sendMessage}>Enviar</button>
      </div>
    </div>
  );
}