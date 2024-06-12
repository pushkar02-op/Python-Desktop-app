# Flask SQL Database Interface

This project is a Python Flask application that connects to an SQL database. The application can be packaged into an executable using PyInstaller, allowing users to input the SQL `DB_HOST` and `DB_PASSWORD` through a GUI.

## Prerequisites

- Python 3.6+
- MySQL database
- Virtual Environment (optional but recommended)

## Setup Instructions

### 1. Clone the Repository

```sh
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name
```

### 2. Create and Activate a Virtual Environment

### Windows:

```sh
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

### 4. Install PyInstaller

```sh
pip install pyinstaller
```

### Running the Application

### 1. Update Database Configuration

### Edit the main.py file to configure the default database parameters.

### 2. Run the Flask Application

```sh
python main.py <DB_HOST> <DB_PASSWORD>
```

### 3. Package the Application with PyInstaller

```sh
pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" gui.py main.py
```

### 4. Run the Executable

Navigate to the dist directory and run the executable:

Windows:

```sh
dist\main.exe
```

### Application Usage

When running the executable, a GUI will prompt you to input the DB_HOST and DB_PASSWORD. These values will be passed to the Flask application.

### Project Structure

css
Copy code
.
├── templates
│ └── main.html
├── static
│ └── style.css
├── main.py
├── requirements.txt
├── README.md
└── main.spec

### Run

```sh
python main.py  localhost Pushk@r121
```
