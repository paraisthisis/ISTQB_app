# ISTQB CTFL v4.0.1 Practice App

An interactive study and exam simulator for the ISTQB Certified Tester Foundation Level (CTFL v4.0.1) exam.

🌐 **Live Web App on GitHub Pages:** **[https://vasiarapti.github.io/ISTQB_app/](https://vasiarapti.github.io/ISTQB_app/)**

## Features
- 📚 **Study Mode**: Read the syllabus by chapter with key glossary terms.
- 🏋 **Practice Mode**: Test yourself question-by-question with instant feedback and explanations.
- 🗂 **Theory Cards**: Flip flashcards based on Learning Objectives (LOs), filterable by chapter and K-levels (K1, K2, K3).
- 📝 **Mock Exam**: Realistic 40-question simulator with a 60-minute timer, scoring against the official 65% (26/40) pass threshold, and per-question reviews.

## Tech Stack
- **Backend**: Python + Flask
- **Database**: SQLite (`data/istqb.db`)
- **Frontend**: Vanilla HTML5, CSS3, Modern JavaScript (No build step)
- **Testing**: Playwright end-to-end tests

## Quick Start

### 1. Install dependencies
```bash
# Python dependencies
pip install -r requirements.txt

# Node dependencies (for Playwright tests)
npm install
```

### 2. Build / Initialize the database
```bash
python3 ingestion/build_db.py
```

### 3. Run the application
```bash
python3 backend/app.py
```
Open **http://localhost:5050** in your browser.

## Running Tests
```bash
npx playwright test
```
