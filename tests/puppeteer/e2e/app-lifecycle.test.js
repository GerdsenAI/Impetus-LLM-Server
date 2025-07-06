const { AppController } = require('../utils/app-controller');
const { ApiClient } = require('../utils/api-client');
const { ScreenshotHelper } = require('../utils/screenshot-helper');

describe('IMPETUS App Lifecycle Tests', () => {
  let appController;
  let apiClient;
  let screenshot;

  beforeAll(async () => {
    appController = new AppController();
    apiClient = new ApiClient();
    screenshot = new ScreenshotHelper();
  });

  afterAll(async () => {
    await screenshot.close();
    await appController.terminate();
  });

  describe('App Launch and Startup', () => {
    test('should launch IMPETUS app successfully', async () => {
      console.log('🚀 Testing IMPETUS app launch...');
      
      // Launch the app
      await appController.launch();
      
      // Verify app is running
      const status = appController.getStatus();
      expect(status.isRunning).toBe(true);
      expect(status.appPath).toBe('/Applications/Impetus.app');
      
      console.log('✅ IMPETUS app launched successfully');
    }, 60000);

    test('should have server responding on localhost:8080', async () => {
      console.log('🔍 Testing server health...');
      
      // Wait a bit for server to fully start
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      // Check if server is ready
      const isReady = await appController.isServerReady();
      expect(isReady).toBe(true);
      
      // Test health endpoint
      const healthResponse = await apiClient.healthCheck();
      expect(healthResponse.success).toBe(true);
      expect(healthResponse.status).toBe(200);
      expect(healthResponse.data).toHaveProperty('status', 'healthy');
      
      console.log('✅ Server is healthy and responding');
    }, 30000);

    test('should have web interface accessible', async () => {
      console.log('🌐 Testing web interface...');
      
      // Initialize browser
      await screenshot.init({ headless: false });
      
      // Navigate to the web interface
      await screenshot.navigate('http://localhost:8080');
      
      // Take screenshot of the interface
      await screenshot.screenshot('web-interface-home');
      
      // Check if page loaded successfully
      const title = await screenshot.getTitle();
      expect(title).toBeTruthy();
      
      // Check for basic page structure
      const hasBody = await screenshot.elementExists('body');
      expect(hasBody).toBe(true);
      
      console.log(`✅ Web interface accessible with title: "${title}"`);
    }, 30000);
  });

  describe('API Endpoints Availability', () => {
    test('should have all OpenAI compatible endpoints available', async () => {
      console.log('🔌 Testing API endpoints...');
      
      // Test models endpoint
      const modelsResponse = await apiClient.getModels();
      expect(modelsResponse.success).toBe(true);
      expect(modelsResponse.data).toHaveProperty('object', 'list');
      expect(modelsResponse.data).toHaveProperty('data');
      expect(Array.isArray(modelsResponse.data.data)).toBe(true);
      
      console.log(`✅ Models endpoint working: ${modelsResponse.data.data.length} models available`);
      
      // Test hardware info endpoint
      const hardwareResponse = await apiClient.getHardwareInfo();
      expect(hardwareResponse.success).toBe(true);
      
      console.log('✅ Hardware info endpoint working');
      
      // Test loaded models endpoint
      const loadedModelsResponse = await apiClient.getLoadedModels();
      expect(loadedModelsResponse.success).toBe(true);
      
      console.log('✅ Loaded models endpoint working');
    });

    test('should handle basic chat completion request', async () => {
      console.log('💬 Testing basic chat completion...');
      
      const testMessage = [
        { role: 'user', content: 'Hello, this is a test message. Please respond briefly.' }
      ];
      
      const chatResponse = await apiClient.chatCompletion(testMessage, {
        max_tokens: 50,
        temperature: 0.7
      });
      
      expect(chatResponse.success).toBe(true);
      expect(chatResponse.data).toHaveProperty('choices');
      expect(Array.isArray(chatResponse.data.choices)).toBe(true);
      expect(chatResponse.data.choices.length).toBeGreaterThan(0);
      
      const choice = chatResponse.data.choices[0];
      expect(choice).toHaveProperty('message');
      expect(choice.message).toHaveProperty('role', 'assistant');
      expect(choice.message).toHaveProperty('content');
      expect(typeof choice.message.content).toBe('string');
      
      console.log(`✅ Chat completion working, response: "${choice.message.content.substring(0, 100)}..."`);
    }, 45000);
  });

  describe('App Termination', () => {
    test('should terminate app gracefully', async () => {
      console.log('🛑 Testing app termination...');
      
      // Terminate the app
      await appController.terminate();
      
      // Verify app is no longer running
      const status = appController.getStatus();
      expect(status.isRunning).toBe(false);
      
      // Wait a bit and verify server is no longer responding
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      const isReady = await appController.isServerReady();
      expect(isReady).toBe(false);
      
      console.log('✅ App terminated gracefully');
    });
  });

  describe('App Restart', () => {
    test('should restart app successfully', async () => {
      console.log('🔄 Testing app restart...');
      
      // Restart the app
      await appController.restart();
      
      // Verify app is running again
      const status = appController.getStatus();
      expect(status.isRunning).toBe(true);
      
      // Verify server is responding
      const isReady = await appController.isServerReady();
      expect(isReady).toBe(true);
      
      // Test a quick API call
      const healthResponse = await apiClient.healthCheck();
      expect(healthResponse.success).toBe(true);
      
      console.log('✅ App restarted successfully');
    }, 60000);
  });
});
