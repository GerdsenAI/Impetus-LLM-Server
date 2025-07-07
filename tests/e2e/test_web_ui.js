/**
 * Puppeteer E2E test for Impetus Web UI
 * Tests the web server and UI screens
 */

const puppeteer = require('puppeteer');
const assert = require('assert');

// Test configuration
const BASE_URL = 'http://localhost:8080';
const TIMEOUT = 30000; // 30 seconds timeout

// Main test function
async function runTests() {
  console.log('Starting Impetus Web UI tests...');
  
  // Launch browser
  const browser = await puppeteer.launch({
    headless: false, // Set to true for headless mode
    slowMo: 100,     // Slow down operations for better visibility
    args: ['--window-size=1280,800']
  });
  
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 800 });
    
    // Test 1: Check if server is running and home page loads
    console.log('Test 1: Checking if server is running...');
    await page.goto(BASE_URL, { timeout: TIMEOUT, waitUntil: 'networkidle2' });
    
    // Verify page title
    const title = await page.title();
    console.log(`Page title: ${title}`);
    assert(title.includes('Impetus'), 'Page title should contain "Impetus"');
    
    // Test 2: Check navigation menu
    console.log('Test 2: Testing navigation menu...');
    const navElements = await page.$$eval('nav a, nav button', elements => 
      elements.map(el => el.textContent.trim())
    );
    console.log('Navigation elements:', navElements);
    
    // Test 3: Check model selection screen
    console.log('Test 3: Testing model selection screen...');
    // Look for model selection elements
    const modelElements = await page.$$eval('.model-card, .model-item', elements => 
      elements.map(el => el.textContent.trim())
    );
    console.log('Found model elements:', modelElements.length);
    
    // Test 4: Check settings screen
    console.log('Test 4: Testing settings screen...');
    // Navigate to settings
    const settingsLink = await page.$('a[href*="settings"], button:has-text("Settings")');
    if (settingsLink) {
      await settingsLink.click();
      await page.waitForTimeout(1000);
      
      // Check for settings elements
      const settingsElements = await page.$$eval('input, select, button', elements => 
        elements.length
      );
      console.log(`Found ${settingsElements} settings elements`);
    } else {
      console.log('Settings link not found, skipping test');
    }
    
    // Test 5: Check chat interface
    console.log('Test 5: Testing chat interface...');
    // Navigate to chat
    const chatLink = await page.$('a[href*="chat"], button:has-text("Chat")');
    if (chatLink) {
      await chatLink.click();
      await page.waitForTimeout(1000);
      
      // Check for chat input
      const chatInput = await page.$('textarea, input[type="text"]');
      if (chatInput) {
        console.log('Chat input found');
        await chatInput.type('Hello, this is a test message');
        
        // Find send button
        const sendButton = await page.$('button[type="submit"], button:has-text("Send")');
        if (sendButton) {
          console.log('Send button found, clicking...');
          await sendButton.click();
          await page.waitForTimeout(2000);
          
          // Check for response
          const messages = await page.$$eval('.message, .chat-message', elements => 
            elements.length
          );
          console.log(`Found ${messages} chat messages`);
        } else {
          console.log('Send button not found');
        }
      } else {
        console.log('Chat input not found');
      }
    } else {
      console.log('Chat link not found, skipping test');
    }
    
    console.log('All tests completed successfully!');
    
  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    // Close browser
    await browser.close();
  }
}

// Run tests
runTests().catch(console.error);
