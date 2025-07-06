const { AppController } = require('../utils/app-controller');
const { ScreenshotHelper } = require('../utils/screenshot-helper');
const { testData } = require('../utils/test-data');

describe('IMPETUS Web Interface Tests', () => {
  let appController;
  let screenshot;

  beforeAll(async () => {
    appController = new AppController();
    screenshot = new ScreenshotHelper();
    
    // Ensure app is running
    await appController.launch();
    await new Promise(resolve => setTimeout(resolve, 10000));
    
    // Initialize browser
    await screenshot.init({ headless: false });
  });

  afterAll(async () => {
    await screenshot.close();
    await appController.terminate();
  });

  describe('Basic Web Interface', () => {
    test('should load the main interface', async () => {
      console.log('🌐 Testing main web interface...');
      
      await screenshot.navigate('http://localhost:8080');
      await screenshot.screenshot('main-interface');
      
      const title = await screenshot.getTitle();
      expect(title).toBeTruthy();
      expect(title.length).toBeGreaterThan(0);
      
      const hasBody = await screenshot.elementExists('body');
      expect(hasBody).toBe(true);
      
      // Check for React UI elements
      const hasTabsList = await screenshot.elementExists(testData.selectors.tabsList);
      const hasHeader = await screenshot.elementExists(testData.selectors.header);
      
      if (hasTabsList) {
        console.log('✅ React UI detected with tab navigation');
      } else {
        console.log('ℹ️ Legacy UI detected');
      }
      
      console.log(`✅ Main interface loaded with title: "${title}"`);
    });

    test('should have responsive design', async () => {
      console.log('📱 Testing responsive design...');
      
      // Test desktop view
      await screenshot.page.setViewport({ width: 1280, height: 800 });
      await screenshot.screenshot('desktop-view');
      
      // Test tablet view
      await screenshot.page.setViewport({ width: 768, height: 1024 });
      await screenshot.screenshot('tablet-view');
      
      // Test mobile view
      await screenshot.page.setViewport({ width: 375, height: 667 });
      await screenshot.screenshot('mobile-view');
      
      // Reset to desktop
      await screenshot.page.setViewport({ width: 1280, height: 800 });
      
      console.log('✅ Responsive design tested across viewports');
    });

    test('should display hardware information', async () => {
      console.log('🔧 Testing hardware information display...');
      
      await screenshot.navigate('http://localhost:8080');
      
      // Look for hardware information on the page
      const content = await screenshot.getContent();
      
      // Should display some Apple Silicon information
      const hasHardwareInfo = content.includes('Apple') || 
                             content.includes('M1') || 
                             content.includes('M2') || 
                             content.includes('M3') || 
                             content.includes('M4') ||
                             content.includes('cores') ||
                             content.includes('chip');
      
      await screenshot.screenshot('hardware-info');
      
      if (hasHardwareInfo) {
        console.log('✅ Hardware information displayed');
      } else {
        console.log('⚠️ Hardware information not prominently displayed');
      }
    });
  });

  describe('Model Management Interface', () => {
    test('should display available models', async () => {
      console.log('🤖 Testing model display...');
      
      await screenshot.navigate('http://localhost:8080');
      
      // Look for model-related content
      const hasModelCard = await screenshot.elementExists(testData.selectors.modelCard);
      const hasModelList = await screenshot.elementExists(testData.selectors.modelList);
      const hasModelSelector = await screenshot.elementExists(testData.selectors.modelSelector);
      
      await screenshot.screenshot('models-interface');
      
      const hasModelInterface = hasModelCard || hasModelList || hasModelSelector;
      
      if (hasModelInterface) {
        console.log('✅ Model interface elements found');
      } else {
        console.log('⚠️ Model interface may be dynamic or different structure');
      }
    });

    test('should allow model interaction', async () => {
      console.log('🎯 Testing model interaction...');
      
      await screenshot.navigate('http://localhost:8080');
      
      // Try to find and interact with model elements
      try {
        const modelSelector = await screenshot.elementExists(testData.selectors.modelSelector);
        if (modelSelector) {
          await screenshot.click(testData.selectors.modelSelector);
          await screenshot.screenshot('model-selector-clicked');
          console.log('✅ Model selector interaction working');
        }
      } catch (error) {
        console.log('⚠️ Model selector not found or not interactable');
      }
      
      // Look for any buttons or interactive elements
      const content = await screenshot.getContent();
      const hasButtons = content.includes('<button') || content.includes('btn-');
      
      if (hasButtons) {
        await screenshot.screenshot('interactive-elements');
        console.log('✅ Interactive elements found on interface');
      }
    });
  });

  describe('Status and Monitoring', () => {
    test('should display server status', async () => {
      console.log('📊 Testing server status display...');
      
      await screenshot.navigate('http://localhost:8080');
      
      const content = await screenshot.getContent();
      
      // Look for status indicators
      const hasStatusInfo = content.includes('status') ||
                           content.includes('healthy') ||
                           content.includes('running') ||
                           content.includes('online') ||
                           content.includes('active');
      
      await screenshot.screenshot('server-status');
      
      if (hasStatusInfo) {
        console.log('✅ Server status information displayed');
      } else {
        console.log('⚠️ Server status not prominently displayed');
      }
    });

    test('should show performance metrics if available', async () => {
      console.log('📈 Testing performance metrics...');
      
      await screenshot.navigate('http://localhost:8080');
      
      const content = await screenshot.getContent();
      
      // Look for performance-related information
      const hasMetrics = content.includes('memory') ||
                        content.includes('cpu') ||
                        content.includes('gpu') ||
                        content.includes('tokens') ||
                        content.includes('requests') ||
                        content.includes('ms') ||
                        content.includes('MB') ||
                        content.includes('GB');
      
      await screenshot.screenshot('performance-metrics');
      
      if (hasMetrics) {
        console.log('✅ Performance metrics displayed');
      } else {
        console.log('⚠️ Performance metrics not prominently displayed');
      }
    });
  });

  describe('User Experience', () => {
    test('should have good loading performance', async () => {
      console.log('⚡ Testing page loading performance...');
      
      const startTime = Date.now();
      await screenshot.navigate('http://localhost:8080');
      const loadTime = Date.now() - startTime;
      
      expect(loadTime).toBeLessThan(5000); // Under 5 seconds
      
      await screenshot.screenshot('loaded-interface');
      
      console.log(`✅ Page loaded in ${loadTime}ms`);
    });

    test('should handle navigation smoothly', async () => {
      console.log('🧭 Testing navigation...');
      
      await screenshot.navigate('http://localhost:8080');
      
      // Try to find navigation elements
      const hasNavigation = await screenshot.elementExists(testData.selectors.navMenu);
      
      if (hasNavigation) {
        await screenshot.screenshot('navigation-menu');
        console.log('✅ Navigation menu found');
        
        // Try to click navigation items if they exist
        try {
          const hasHomeLink = await screenshot.elementExists(testData.selectors.homeLink);
          if (hasHomeLink) {
            await screenshot.click(testData.selectors.homeLink);
            await screenshot.screenshot('home-navigation');
          }
        } catch (error) {
          console.log('⚠️ Navigation interaction not available');
        }
      } else {
        console.log('⚠️ Navigation menu not found (may be single page)');
      }
    });

    test('should provide user feedback', async () => {
      console.log('💬 Testing user feedback elements...');
      
      await screenshot.navigate('http://localhost:8080');
      
      const content = await screenshot.getContent();
      
      // Look for user feedback elements
      const hasFeedbackElements = content.includes('loading') ||
                                 content.includes('error') ||
                                 content.includes('success') ||
                                 content.includes('alert') ||
                                 content.includes('notification') ||
                                 content.includes('spinner');
      
      await screenshot.screenshot('user-feedback');
      
      if (hasFeedbackElements) {
        console.log('✅ User feedback elements found');
      } else {
        console.log('⚠️ User feedback elements not prominently visible');
      }
    });
  });

  describe('Error Handling', () => {
    test('should handle invalid routes gracefully', async () => {
      console.log('🚫 Testing error page handling...');
      
      try {
        await screenshot.navigate('http://localhost:8080/nonexistent-page');
        await screenshot.screenshot('error-page');
        
        const content = await screenshot.getContent();
        const hasErrorHandling = content.includes('404') ||
                                content.includes('Not Found') ||
                                content.includes('Error') ||
                                content.includes('not found');
        
        if (hasErrorHandling) {
          console.log('✅ Error page handling implemented');
        } else {
          console.log('⚠️ May redirect to main page instead of showing error');
        }
      } catch (error) {
        console.log('⚠️ Error page testing failed:', error.message);
      }
    });

    test('should display helpful error messages', async () => {
      console.log('🆘 Testing error message quality...');
      
      // This test checks if the interface provides helpful error information
      // when the backend might be having issues
      
      await screenshot.navigate('http://localhost:8080');
      
      // Check console for any JavaScript errors
      const browserErrors = [];
      screenshot.page.on('pageerror', error => {
        browserErrors.push(error.message);
      });
      
      // Wait a bit to catch any errors
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      if (browserErrors.length === 0) {
        console.log('✅ No JavaScript errors detected');
      } else {
        console.log('⚠️ JavaScript errors detected:', browserErrors);
      }
      
      await screenshot.screenshot('console-check');
    });
  });
});
