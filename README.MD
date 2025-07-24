
# Voro

**Voro** is a simple yet strategic multiplayer web game.
The rules are easy to learn, but mastering it takes time and clever tactics.

### 🎮 How to Play

* Click on a circle to increase its count by one.
* When a circle reaches **4**, it **explodes** and sends one unit to each of its four neighboring circles.
* These chain reactions can lead to strategic captures and dynamic shifts on the board.
* Anyone of any age can learn the game in minutes — but mastering strategies can take a lifetime.

---

## 🧱 Tech Stack

### ⚙️ Backend

* **Django** (core web framework)
* **Django Channels** + **Daphne** (WebSockets for real-time gameplay)
* **PostgreSQL** (database)
* **NGINX** (reverse proxy for deployment)

<img src="https://datascientest.com/en/files/2023/05/django1.jpg" width="30%">

### 🖥️ Frontend

* Pure **HTML/CSS** with a bit of **Bootstrap**
* Background music and user customization (profile pic and colors)

### 🚢 Deployment

* **Docker** & **Docker Compose**

<img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSgbZ2MIpY2RxhPKAIHbcXy5Kf058evd7QfYQ&s" width="30%">

---

## 🗂️ Project Structure

The Django project includes one main app: `base`

* `game_logic.py`: Contains the rules and mechanics of the game.
* `consumer.py`: Handles WebSocket communication using Django Channels.
* Other Django files handle users, views, models, and routing.

---

## 🚀 Getting Started

### 🧪 Development

1. Clone the repository:

   ```bash
   git clone https://github.com/seyed0123/Voro
   cd Voro
   cd begholplay
   ```

2. Create a `.env` file and fill in your settings:

   ```dotenv
   POSTGRES_DB=
   POSTGRES_USER=
   POSTGRES_PASSWORD=
   DB_HOST=
   DB_PORT=
   ADMIN_USER=
   ADMIN_EMAIL=
   ADMIN_PASSWORD=
   ```

3. Run migrations:

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. Run the development server:

   ```bash
   python manage.py runserver
   ```

---

### 🐳 Production with Docker

1. Build and start the containers:

   ```bash
   docker-compose up
   ```

2. Access the game at [http://localhost](http://localhost)

---

## 📸 Screenshots

| Home                                            | Profile                                         | Join Lobby                                      |
| ----------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- |
| ![](begholplay/shots/Screenshot%202025-07-24%20171510.png) | ![](begholplay/shots/Screenshot%202025-07-24%20171632.png) | ![](begholplay/shots/Screenshot%202025-07-24%20171742.png) |

| Lobby                                           | Game Page                                       | Win Ceremony                                    |
| ----------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- |
| ![](begholplay/shots/Screenshot%202025-07-24%20171825.png) | ![](begholplay/shots/Screenshot%202025-07-24%20171939.png) | ![](begholplay/shots/Screenshot%202025-07-24%20172000.png) |

---

## 📌 Notes

* Designed for quick fun and replayability.
* Built as a lightweight, real-time multiplayer game using only essential tools.

---
