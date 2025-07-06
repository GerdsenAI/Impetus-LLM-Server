const { spawn, exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

class AppController {
  constructor() {
    this.appProcess = null;
    this.isRunning = false;
    this.appPath = '/Applications/Impetus.app';
    this.baseUrl = 'http://localhost:8080';
    this.maxStartupTime = 30000; // 30 seconds
  }

  /**
   * Launch the IMPETUS application
   */
  async launch() {
    if (this.isRunning) {
      console.log('📱 IMPETUS app already running');
      return;
    }

    console.log('🚀 Launching IMPETUS app...');
    
    try {
      // Kill any existing instances first
      await this.killExistingProcesses();
      
      // Launch the app using macOS open command
      this.appProcess = spawn('open', [this.appPath], {
        detached: true,
        stdio: 'ignore'
      });

      // Wait for the app to start and server to be ready
      await this.waitForServerReady();
      
      this.isRunning = true;
      console.log('✅ IMPETUS app launched successfully');
      
    } catch (error) {
      console.error('❌ Failed to launch IMPETUS app:', error.message);
      throw error;
    }
  }

  /**
   * Wait for the server to be ready
   */
  async waitForServerReady() {
    const startTime = Date.now();
    const maxWaitTime = this.maxStartupTime;
    
    console.log('⏳ Waiting for server to be ready...');
    
    while (Date.now() - startTime < maxWaitTime) {
      try {
        const response = await fetch(`${this.baseUrl}/api/health`);
        if (response.ok) {
          console.log('✅ Server is ready');
          return;
        }
      } catch (error) {
        // Server not ready yet, continue waiting
      }
      
      // Wait 1 second before next check
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    throw new Error(`Server failed to start within ${maxWaitTime}ms`);
  }

  /**
   * Check if server is responding
   */
  async isServerReady() {
    try {
      const response = await fetch(`${this.baseUrl}/api/health`, {
        method: 'GET',
        timeout: 5000
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  /**
   * Kill existing IMPETUS processes
   */
  async killExistingProcesses() {
    try {
      // Find and kill IMPETUS processes
      const { stdout } = await execAsync('pgrep -f "Impetus.app"');
      const pids = stdout.trim().split('\n').filter(pid => pid);
      
      if (pids.length > 0) {
        console.log(`🔄 Killing ${pids.length} existing IMPETUS processes`);
        for (const pid of pids) {
          try {
            await execAsync(`kill -TERM ${pid}`);
          } catch (error) {
            // Process might already be dead
          }
        }
        
        // Wait a bit for graceful shutdown
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Force kill if still running
        for (const pid of pids) {
          try {
            await execAsync(`kill -KILL ${pid}`);
          } catch (error) {
            // Process already dead
          }
        }
      }
    } catch (error) {
      // No existing processes found
    }
  }

  /**
   * Terminate the IMPETUS application
   */
  async terminate() {
    if (!this.isRunning) {
      console.log('📱 IMPETUS app not running');
      return;
    }

    console.log('🛑 Terminating IMPETUS app...');
    
    try {
      await this.killExistingProcesses();
      
      this.appProcess = null;
      this.isRunning = false;
      
      console.log('✅ IMPETUS app terminated');
      
    } catch (error) {
      console.error('❌ Error terminating IMPETUS app:', error.message);
      throw error;
    }
  }

  /**
   * Restart the application
   */
  async restart() {
    console.log('🔄 Restarting IMPETUS app...');
    await this.terminate();
    await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3 seconds
    await this.launch();
  }

  /**
   * Get application status
   */
  getStatus() {
    return {
      isRunning: this.isRunning,
      appPath: this.appPath,
      baseUrl: this.baseUrl,
      processId: this.appProcess?.pid || null
    };
  }

  /**
   * Cleanup method for test teardown
   */
  static async cleanup() {
    const controller = new AppController();
    await controller.terminate();
  }
}

module.exports = { AppController };
