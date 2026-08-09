# How did i created this project

- Step1 - Created boilerplate files
    - main.py (entry file of the project)
    - requirements.txt (this is like package.json for node -- keeps dependency list)
    - .env (contains environment variable for secrets)
    - .gitignore (list of files to be ignored to be committed)
    - README.md
- Step 2 - Create environment for this python project
    - python3 -m venv venv
    - source venv/bin/activate 
- Step 3 - Install dependencies
    - pip install fastapi uvicorn anthropic python-dotenv
- Step 4 - Register installed dependency in requirements.txt
    - pip freeze > requirements.txt
- Step 5 - Run the project locally
    - uvicorn main:app --reload