import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

export default function TopicSelection({ setSelectedTopic }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [topics, setTopics] = useState([]); // Inicializa como un array vacío
  const navigate = useNavigate();

  useEffect(() => {
    const fetchTopics = async () => {
      try {
        const response = await axios.get("http://192.168.1.134:5678/webhook/temas");
        // Verifica si la respuesta es un array o un objeto
        if (Array.isArray(response.data)) {
          setTopics(response.data);
        } else {
          // Si la respuesta no es un array, ajusta según la estructura de la respuesta
          setTopics([response.data]); // Ajusta esto según sea necesario
        }
      } catch (error) {
        console.error("Error fetching topics:", error);
      }
    };

    fetchTopics();
  }, []);

  const filteredTopics = topics.filter(topic =>
    topic.nombre_temario.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleTopicSelect = (topic) => {
    setSelectedTopic(topic);
    navigate("/chat");
  };

  return (
    <div className="topic-selection">
      <h2>Selecciona un Tema</h2>
      <input
        type="text"
        placeholder="Buscar tema..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <ul>
        {filteredTopics.map(topic => (
          <li key={topic.id} onClick={() => handleTopicSelect(topic)}>
            {topic.nombre_temario}
          </li>
        ))}
      </ul>
    </div>
  );
}