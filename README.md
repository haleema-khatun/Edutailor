
<h1 align="center">🌟 Edutailor</h1>

<p align="center">
  <a href="https://github.com/haleema-khatun/Edutailor/stargazers">
    <img src="https://img.shields.io/github/stars/haleema-khatun/Edutailor?style=for-the-badge&logo=github" alt="GitHub stars">
  </a>
  <a href="https://github.com/haleema-khatun/Edutailor/issues">
    <img src="https://img.shields.io/github/issues/haleema-khatun/Edutailor?style=for-the-badge&logo=github" alt="GitHub issues">
  </a>
  <a href="https://github.com/haleema-khatun/Edutailor/contributors">
    <img src="https://img.shields.io/github/contributors/haleema-khatun/Edutailor?style=for-the-badge" alt="Contributors">
  </a>
  <a href="https://github.com/haleema-khatun/Edutailor/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/haleema-khatun/Edutailor?style=for-the-badge" alt="License">
  </a>
</p>

---

## 🎯 About Edutailor
Edutailor is a **modern, interactive learning platform** designed to make education **engaging, accessible, and fun**.  
It combines dynamic content, AI-assisted tools, and responsive design to provide an enhanced learning experience for all ages.

---

## 🚀 Features
- **Interactive Learning Modules:** Make education more engaging.  
- **Responsive Design:** Works perfectly on desktop, tablet, and mobile.  
- **User-Friendly UI:** Clean interface built with HTML, CSS, JavaScript.  
- **Python Backend:** Dynamic functionality powered by Python.  
- **AI Integration:** Intelligent features to tailor learning content.  

---

- **Frontend:** React SPA, communicates with backend via REST API.  
- **Backend:** Flask application exposing endpoints with validations and structured responses.  
- **Database:** Relational schema to ensure consistency, relational constraints, and simple CRUD operations.  
- **AI Guidance:** Used for code generation, refactoring, and reviewing technical decisions.

---

## 💡 Key Technical Decisions

1. **Flask + Python Backend**
   - Lightweight and fast for creating REST APIs.
   - Easy integration with relational databases and AI-assisted code generation.

2. **React Frontend**
   - Component-based structure ensures clarity and maintainability.
   - State management using React hooks (useState/useEffect).

3. **Relational Database**
   - Chosen for data consistency and enforceable schemas.
   - Simple tables with primary/foreign keys to prevent invalid states.

4. **AI Usage**
   - Guided AI agents to generate boilerplate, suggest optimizations, and validate architecture.
   - All AI-generated code critically reviewed before integration.
   - Maintained prompting rules in `claude.md` / `agents.md`.

5. **Testing & Verification**
   - Backend: Pytest for API endpoints and validation checks.
   - Frontend: Jest unit tests for component behavior.
   - Ensures correctness after adding new features or refactoring.

---

## 🧩 Features (Minimal)

- User can **create, read, update, and delete** records in the database via API.
- Frontend interface to **display, edit, and submit** data.
- Validations to prevent invalid states.
- Error handling with meaningful messages and logs.

---

## 📁 AI Guidance Files

- `claude.md` – Prompts and rules for AI agents.
- `agents.md` – Instructions for AI-generated code review.
- `prompting_rules.md` – Constraints for safe code generation.
- `coding_standards.md` – Conventions for consistency and readability.

---

 ## Edutailor Project Architecture
Frontend (React)
├─ Components
├─ Pages
├─ Services (API calls)
├─ State Management (hooks/context)
Backend (Flask)
├─ app.py (Flask app)
├─ routes/ (API endpoints)
├─ models/ (DB models)
├─ services/ (business logic)
├─ utils/ (helpers, validations)
Database (Relational)
├─ Tables with relationships
├─ Constraints (PK, FK, Not Null)
├─ Seed & migration scripts
AI Guidance Files
├─ claude.md
├─ agents.md
├─ prompting_rules.md
├─ coding_standards.md

## 📝 Setup & Running

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask server
export FLASK_APP=app.py
flask run

## 📌 Installation & Setup
```bash
# Clone the repository
git clone https://github.com/haleema-khatun/Edutailor.git

# Go into the project folder
cd Edutailor

# Open index.html in a browser or run Python backend

🤝 Contributing

We welcome contributions!

Fork the repo

Create a new branch (git checkout -b feature/YourFeature)

Commit your changes (git commit -m 'Add YourFeature')

Push to your branch (git push origin feature/YourFeature)

Open a Pull Request

📞 Contact

Haleema Khatun – GitHub Profile


📜 License

This project is licensed under the MIT License – see LICENSE
 for details.

