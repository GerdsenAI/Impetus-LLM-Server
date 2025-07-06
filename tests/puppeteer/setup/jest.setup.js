// Jest setup for IMPETUS Puppeteer tests
const { AppController } = require('../utils/app-controller');

// Global test configuration
global.IMPETUS_APP_PATH = '/Applications/Impetus.app';
global.IMPETUS_BASE_URL = 'http://localhost:8080';
global.TEST_TIMEOUT = 60000;

// Global setup before all tests
beforeAll(async () => {
  console.log('🚀 Starting IMPETUS test suite setup...');
  
  // Verify app exists
  const fs = require('fs');
  if (!fs.existsSync(global.IMPETUS_APP_PATH)) {
    throw new Error(`IMPETUS app not found at ${global.IMPETUS_APP_PATH}`);
  }
  
  console.log('✅ IMPETUS app found at', global.IMPETUS_APP_PATH);
}, global.TEST_TIMEOUT);

// Global cleanup after all tests
afterAll(async () => {
  console.log('🧹 Cleaning up IMPETUS test suite...');
  
  try {
    // Ensure any running IMPETUS processes are terminated
    await AppController.cleanup();
    console.log('✅ Test cleanup completed');
  } catch (error) {
    console.warn('⚠️  Cleanup warning:', error.message);
  }
}, 10000);

// Enhanced expect matchers
expect.extend({
  toBeValidOpenAIResponse(received) {
    const pass = received && 
                 typeof received === 'object' &&
                 (received.object === 'list' || received.choices || received.data);
    
    return {
      message: () => `Expected ${received} to be a valid OpenAI API response`,
      pass
    };
  },
  
  toHaveValidStreamingData(received) {
    const pass = received && 
                 received.startsWith('data: ') &&
                 received.includes('"object":');
    
    return {
      message: () => `Expected ${received} to be valid streaming data`,
      pass
    };
  }
});
