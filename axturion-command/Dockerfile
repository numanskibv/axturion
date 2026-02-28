FROM node:20-alpine

WORKDIR /app

ARG NEXT_PUBLIC_DEV_MODE
ENV NEXT_PUBLIC_DEV_MODE=${NEXT_PUBLIC_DEV_MODE}

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]