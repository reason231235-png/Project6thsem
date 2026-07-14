# 📌 Cozy Clothings 🧥  
_A Django-powered e-commerce platform_  

Welcome to **Cozy Clothings**! This guide will help you **set up, run, and contribute** to the project. Whether you're a developer, contributor, or just curious, this README has everything you need to get started.

---

## ✨ Highlighting Features  
- **User Authentication & Account Management**: Secure user registration, login, and profile management. 
- **Product Listing & Filtering**: Browse products with advanced filtering options.
- **Shopping Cart & Checkout**: Smooth cart management and checkout process.
- **Auction-Based Product Sales**: Bid on products and receive email notifications.
- **Background Task Handling**: Powered by Celery for asynchronous tasks.
- **Payment Integration**: Supports eSewa and Khalti for seamless transactions.

---

## 📋 Prerequisites  
Before you begin, ensure you have the following installed: 
- **Python** (>= 3.8)  
- **pip** (Python package manager)  
- **Git**  
- **Redis** (for Celery tasks)  

---

## 🛠️ Setup Instructions  

### 1️⃣ Clone the Repository  
```bash
git clone https://github.com/mansijmaharzn/cozy-clothings.git
cd cozy-clothings
```

### 2️⃣ Create and Activate a Virtual Environment

- Linux/MacOS
```bash
python3 -m venv venv
source venv/bin/activate
```

- Windows
```bash
python -m venv venv
venv\Scripts\activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Setup the Database
```bash
python manage.py migrate
```

### 5️⃣ Start Redis (Required for Celery)
Make sure Redis is running before starting Celery:
```bash
redis-server
```

### 6️⃣ Start Celery Workers
```bash
celery -A cozy_clothings worker --loglevel=info
```

### 7️⃣ Start Celery Beat (For Scheduled Auction Tasks)
```bash
celery -A cozy_clothings beat --loglevel=info
```

### 8️⃣ (Optional) Start Flower (Celery Monitoring Tool)
```bash
celery -A cozy_clothings flower
```

### 9️⃣ Run the Development Server
```
python manage.py runserver
```

### 🔟 Access the Application
Open your browser and visit:  
🔗 [localhost:8000](http://127.0.0.1:8000)

---

## 🐳 Running with Docker
If you prefer running the project in Docker, follow these steps:

### 1️⃣ Build and Start Containers
```bash
docker compose up --build
```

### 2️⃣ Stop Containers
To stop the containers, use:
```bash
docker-compose down
```

### 3️⃣ Run Migrations Inside the Container
Access the Django container and run migrations:
```bash
docker exec -it cozy_clothings_django_container bash
python manage.py migrate
exit
```

### 4️⃣ Access the Application
Once the containers are running, visit:
🔗 [localhost:8000](http://127.0.0.1:8000)

---

## 👨‍💻 Contributing
We welcome contributions! Here's how you can help:

1. **Fork the repository** on GitHub.
1. **Create a new branch** for your feature or bugfix.
1. **Commit your changes** with clear and descriptive messages.
1. **Open a Pull Request** and describe your changes.

For major changes, please open an issue first to discuss what you'd like to add or modify.

---

## 📬 Need Help?
- 📩 Email me: mansijmaharzn@gmail.com  
- 🐛 Create a GitHub issue.

---

## 🚀 Happy Coding & Enjoy Shopping! 🛍️
This version is more visually appealing, better organized, and includes additional details like the project structure and clearer instructions. Let me know if you'd like further tweaks! 😊