# Usamos la imagen oficial de Node.js
FROM node:16

# Establecemos el directorio de trabajo
WORKDIR /app

# Inicializamos un nuevo proyecto React (si no existe el package.json)
RUN npx create-react-app . 

# Copiamos el resto de los archivos del frontend (en caso de que ya tengas algo de código)
COPY . .

# Instalamos las dependencias necesarias
RUN npm install
RUN npm install axios
RUN npm install uuid
RUN npm install marked
RUN npm install react-router-dom

# Exponemos el puerto 3000
EXPOSE 3000

# Ejecutamos la aplicación en modo desarrollo
CMD ["npm", "start"]
