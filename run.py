#!/usr/bin/env python3
"""
Quick start script for AI Admission Inquiry Assistant
Run this script to start both backend and frontend servers
"""

import os
import sys
import subprocess
import threading
import time
import webbrowser
import signal
from pathlib import Path

class QuickStart:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / 'backend'
        self.frontend_dir = self.project_root / 'frontend'
        self.processes = []
        self.running = True
        
    def check_setup(self):
        """Check if the project is properly set up"""
        print("🔍 Checking project setup...")
        
        # Check if virtual environment exists
        venv_path = self.backend_dir / 'venv'
        if not venv_path.exists():
            print("❌ Backend virtual environment not found. Run setup.py first.")
            return False
        
        # Check if node_modules exists
        node_modules = self.frontend_dir / 'node_modules'
        if not node_modules.exists():
            print("❌ Frontend dependencies not installed. Run setup.py first.")
            return False
        
        # Check if .env exists
        env_file = self.backend_dir / '.env'
        if not env_file.exists():
            print("⚠️  Backend .env file not found. Using default configuration.")
        
        print("✅ Project setup looks good!")
        return True
    
    def start_backend(self):
        """Start the backend server"""
        print("🐍 Starting backend server...")
        
        os.chdir(self.backend_dir)
        
        if os.name == 'nt':  # Windows
            activate_script = 'venv\\Scripts\\activate'
            cmd = f'{activate_script} && python app.py'
            process = subprocess.Popen(cmd, shell=True)
        else:  # Unix/Linux/macOS
            activate_script = 'venv/bin/activate'
            cmd = f'source {activate_script} && python app.py'
            process = subprocess.Popen(cmd, shell=True, executable='/bin/bash')
        
        self.processes.append(('backend', process))
        
        # Wait for backend to start
        print("⏳ Waiting for backend to start...")
        for i in range(30):  # Wait up to 30 seconds
            try:
                import urllib.request
                urllib.request.urlopen('http://localhost:5000/health')
                print("✅ Backend server started successfully!")
                break
            except:
                time.sleep(1)
        else:
            print("⚠️  Backend server might not have started properly")
        
        return process
    
    def start_frontend(self):
        """Start the frontend development server"""
        print("⚛️  Starting frontend server...")
        
        os.chdir(self.frontend_dir)
        
        process = subprocess.Popen(['npm', 'run', 'dev'])
        self.processes.append(('frontend', process))
        
        # Wait for frontend to start
        print("⏳ Waiting for frontend to start...")
        for i in range(30):  # Wait up to 30 seconds
            try:
                import urllib.request
                urllib.request.urlopen('http://localhost:3000')
                print("✅ Frontend server started successfully!")
                break
            except:
                time.sleep(1)
        else:
            print("⚠️  Frontend server might not have started properly")
        
        return process
    
    def open_browser(self):
        """Open the application in the default browser"""
        time.sleep(2)  # Wait a bit more to ensure servers are ready
        try:
            webbrowser.open('http://localhost:3000')
            print("🌐 Opened application in browser: http://localhost:3000")
        except:
            print("🌐 Please open http://localhost:3000 in your browser")
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n\n🛑 Shutting down servers...")
        self.running = False
        
        for name, process in self.processes:
            print(f"   Stopping {name} server...")
            try:
                if os.name == 'nt':  # Windows
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], 
                                 capture_output=True)
                else:  # Unix/Linux/macOS
                    process.terminate()
                    process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        print("✅ All servers stopped. Goodbye!")
        sys.exit(0)
    
    def show_status(self):
        """Show server status and useful information"""
        print("\n" + "="*60)
        print("🚀 AI Admission Inquiry Assistant - Running")
        print("="*60)
        print("📱 Frontend (React):     http://localhost:3000")
        print("🔧 Backend (Flask):      http://localhost:5000")
        print("📊 API Health Check:     http://localhost:5000/health")
        print("📈 Analytics:            http://localhost:3000 (Analytics tab)")
        print("="*60)
        print("💡 Tips:")
        print("   • Use the Chat tab for text conversations")
        print("   • Use the Voice tab for speech interaction")
        print("   • Check Analytics for usage insights")
        print("   • Press Ctrl+C to stop both servers")
        print("="*60)
    
    def run(self):
        """Main run method"""
        print("🚀 AI Admission Inquiry Assistant - Quick Start")
        print("="*60)
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Check if project is set up
        if not self.check_setup():
            print("\n💡 Run 'python setup.py' first to set up the project.")
            return
        
        try:
            # Start backend in a separate thread
            backend_thread = threading.Thread(target=self.start_backend)
            backend_thread.daemon = True
            backend_thread.start()
            
            time.sleep(5)  # Give backend time to start
            
            # Start frontend
            self.start_frontend()
            
            time.sleep(3)  # Give frontend time to start
            
            # Open browser
            browser_thread = threading.Thread(target=self.open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            # Show status
            self.show_status()
            
            # Keep main thread alive and monitor processes
            while self.running:
                # Check if processes are still running
                for name, process in self.processes:
                    if process.poll() is not None:
                        print(f"⚠️  {name} server stopped unexpectedly")
                
                time.sleep(1)
        
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
        except Exception as e:
            print(f"❌ Error: {e}")
            self.signal_handler(signal.SIGINT, None)

def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("""
AI Admission Inquiry Assistant - Quick Start

Usage:
    python run.py              Start both backend and frontend servers
    python run.py --help       Show this help message

This script will:
1. Check if the project is properly set up
2. Start the Flask backend server on http://localhost:5000
3. Start the React frontend server on http://localhost:3000  
4. Open the application in your default browser
5. Show server status and useful information

Press Ctrl+C to stop both servers gracefully.

If you haven't set up the project yet, run 'python setup.py' first.
            """)
            return
    
    quick_start = QuickStart()
    quick_start.run()

if __name__ == '__main__':
    main()