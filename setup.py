#!/usr/bin/env python3
"""
Setup script for AI Admission Inquiry Assistant
This script automates the setup process for the project.
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

class SetupManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / 'backend'
        self.frontend_dir = self.project_root / 'frontend'
        self.python_version = sys.version_info
        
    def check_prerequisites(self):
        """Check if all prerequisites are installed"""
        print("🔍 Checking prerequisites...")
        
        # Check Python version
        if self.python_version < (3, 11):
            print(f"❌ Python 3.11+ required. Found {sys.version}")
            return False
        print(f"✅ Python {sys.version}")
        
        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                node_version = result.stdout.strip()
                print(f"✅ Node.js {node_version}")
            else:
                raise subprocess.CalledProcessError(1, 'node')
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Node.js not found. Please install Node.js 16+ from https://nodejs.org/")
            return False
        
        # Check npm
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                npm_version = result.stdout.strip()
                print(f"✅ npm {npm_version}")
            else:
                raise subprocess.CalledProcessError(1, 'npm')
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ npm not found")
            return False
        
        # Check Git
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                git_version = result.stdout.strip()
                print(f"✅ {git_version}")
            else:
                raise subprocess.CalledProcessError(1, 'git')
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  Git not found (optional)")
        
        return True
    
    def setup_backend(self):
        """Setup backend environment and dependencies"""
        print("\n🐍 Setting up backend...")
        
        os.chdir(self.backend_dir)
        
        # Create virtual environment
        venv_path = self.backend_dir / 'venv'
        if not venv_path.exists():
            print("Creating virtual environment...")
            subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        
        # Activate virtual environment and install dependencies
        if platform.system() == 'Windows':
            pip_path = venv_path / 'Scripts' / 'pip'
            python_path = venv_path / 'Scripts' / 'python'
        else:
            pip_path = venv_path / 'bin' / 'pip'
            python_path = venv_path / 'bin' / 'python'
        
        print("Installing Python dependencies...")
        subprocess.run([str(pip_path), 'install', '--upgrade', 'pip'], check=True)
        subprocess.run([str(pip_path), 'install', '-r', 'requirements.txt'], check=True)
        
        # Setup environment file
        env_file = self.backend_dir / '.env'
        env_example = self.backend_dir / '.env.example'
        if not env_file.exists() and env_example.exists():
            print("Creating .env file from template...")
            shutil.copy(env_example, env_file)
            print("⚠️  Please edit backend/.env with your configuration")
        
        # Create necessary directories
        directories = ['data', 'logs', 'uploads', 'models']
        for dir_name in directories:
            dir_path = self.backend_dir / dir_name
            dir_path.mkdir(exist_ok=True)
        
        # Initialize database and knowledge base
        print("Initializing database and knowledge base...")
        try:
            init_script = f"""
import sys
sys.path.append('{self.backend_dir}')
from utils.database import DatabaseManager
from agents.retrieval_agent import RetrievalAgent

# Initialize database
db = DatabaseManager()
print("Database initialized successfully")

# Initialize retrieval agent and knowledge base
retrieval = RetrievalAgent()
print("Knowledge base initialized successfully")
"""
            
            result = subprocess.run([str(python_path), '-c', init_script], 
                                  capture_output=True, text=True, cwd=self.backend_dir)
            if result.returncode == 0:
                print("✅ Database and knowledge base initialized")
            else:
                print(f"⚠️  Warning: {result.stderr}")
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize database: {e}")
        
        print("✅ Backend setup complete")
    
    def setup_frontend(self):
        """Setup frontend dependencies"""
        print("\n⚛️  Setting up frontend...")
        
        os.chdir(self.frontend_dir)
        
        # Install dependencies
        print("Installing Node.js dependencies...")
        subprocess.run(['npm', 'install'], check=True)
        
        # Setup environment file (optional)
        env_file = self.frontend_dir / '.env.local'
        env_example = self.frontend_dir / '.env.example'
        if not env_file.exists() and env_example.exists():
            shutil.copy(env_example, env_file)
        
        print("✅ Frontend setup complete")
    
    def create_startup_scripts(self):
        """Create convenience startup scripts"""
        print("\n📝 Creating startup scripts...")
        
        # Backend startup script
        if platform.system() == 'Windows':
            backend_script = self.project_root / 'start_backend.bat'
            with open(backend_script, 'w') as f:
                f.write(f"""@echo off
cd /d "{self.backend_dir}"
call venv\\Scripts\\activate
python app.py
pause
""")
            
            frontend_script = self.project_root / 'start_frontend.bat'
            with open(frontend_script, 'w') as f:
                f.write(f"""@echo off
cd /d "{self.frontend_dir}"
npm run dev
pause
""")
        else:
            backend_script = self.project_root / 'start_backend.sh'
            with open(backend_script, 'w') as f:
                f.write(f"""#!/bin/bash
cd "{self.backend_dir}"
source venv/bin/activate
python app.py
""")
            backend_script.chmod(0o755)
            
            frontend_script = self.project_root / 'start_frontend.sh'
            with open(frontend_script, 'w') as f:
                f.write(f"""#!/bin/bash
cd "{self.frontend_dir}"
npm run dev
""")
            frontend_script.chmod(0o755)
        
        print("✅ Startup scripts created")
    
    def run_setup(self):
        """Run the complete setup process"""
        print("🚀 AI Admission Inquiry Assistant Setup")
        print("=" * 50)
        
        if not self.check_prerequisites():
            print("\n❌ Prerequisites check failed. Please install missing requirements.")
            sys.exit(1)
        
        try:
            self.setup_backend()
            self.setup_frontend()
            self.create_startup_scripts()
            
            print("\n🎉 Setup completed successfully!")
            print("\nNext steps:")
            print("1. Edit backend/.env with your email configuration")
            print("2. Start the backend server:")
            if platform.system() == 'Windows':
                print("   - Double-click start_backend.bat")
                print("   - Or run: cd backend && venv\\Scripts\\activate && python app.py")
            else:
                print("   - Run: ./start_backend.sh")
                print("   - Or run: cd backend && source venv/bin/activate && python app.py")
            
            print("3. Start the frontend server (in a new terminal):")
            if platform.system() == 'Windows':
                print("   - Double-click start_frontend.bat")
                print("   - Or run: cd frontend && npm run dev")
            else:
                print("   - Run: ./start_frontend.sh")
                print("   - Or run: cd frontend && npm run dev")
            
            print("4. Open http://localhost:3000 in your browser")
            print("\nFor detailed documentation, see README.md")
            
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Setup failed: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n⚠️  Setup interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            sys.exit(1)

def main():
    setup_manager = SetupManager()
    setup_manager.run_setup()

if __name__ == '__main__':
    main()