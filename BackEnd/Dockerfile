FROM node:16-alpine AS development

WORKDIR /app

RUN apk add --no-cache python3 make g++ curl

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]