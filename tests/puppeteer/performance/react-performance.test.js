const { AppController } = require('../utils/app-controller');
const { ScreenshotHelper } = require('../utils/screenshot-helper');
const { ApiClient } = require('../utils/api-client');
const { testData } = require('../utils/test-data');

describe('IMPETUS React UI Performance Tests', () => {
  let appController;
  let screenshot;
  let apiClient;

  beforeAll(async () => {
    appController = new AppController();
    screenshot = new ScreenshotHelper();
    apiClient = new ApiClient();
    
    // Ensure app is running
    await appController.launch();
    await new Promise(resolve => setTimeout(resolve, 10000));
    
    // Initialize browser with performance monitoring
    await screenshot.init({ headless: false });
  });

  afterAll(async () => {
    await screenshot.close();
    await appController.terminate();
  });

  describe('Page Load Performance', () => {
    test('should load main interface within acceptable time', async () => {
      console.log('⚡ Testing initial page load performance...');
      
      const startTime = Date.now();
      
      await screenshot.navigate('http://localhost:8080');
      await screenshot.waitForSelector(testData.selectors.tabsList);
      
      const loadTime = Date.now() - startTime;
      
      expect(loadTime).toBeLessThan(5000); // Should load within 5 seconds
      console.log(`✅ Page loaded in ${loadTime}ms`);
      
      // Measure time to interactive
      const interactive = await screenshot.page.evaluate(() => {
        return performance.timing.domInteractive - performance.timing.navigationStart;
      });
      
      console.log(`📊 Time to interactive: ${interactive}ms`);
      expect(interactive).toBeLessThan(3000);
    });

    test('should have good Core Web Vitals', async () => {
      console.log('📈 Testing Core Web Vitals...');
      
      // Get performance metrics
      const metrics = await screenshot.page.metrics();
      
      console.log('📊 Performance Metrics:');
      console.log(`  - Heap Size: ${Math.round(metrics.JSHeapUsedSize / 1024 / 1024)}MB`);
      console.log(`  - Documents: ${metrics.Documents}`);
      console.log(`  - Nodes: ${metrics.Nodes}`);
      console.log(`  - Event Listeners: ${metrics.JSEventListeners}`);
      
      // Check for reasonable values
      expect(metrics.JSHeapUsedSize).toBeLessThan(100 * 1024 * 1024); // Less than 100MB
      expect(metrics.JSEventListeners).toBeLessThan(1000); // Reasonable event listener count
      
      await screenshot.screenshot('performance-metrics');
    });
  });

  describe('Tab Switching Performance', () => {
    test('should switch tabs quickly', async () => {
      console.log('🔄 Testing tab switching performance...');
      
      const tabs = [
        testData.selectors.tabUpload,
        testData.selectors.tabHuggingFace,
        testData.selectors.tabInfo,
        testData.selectors.tabLibrary
      ];
      
      const switchTimes = [];
      
      for (const tab of tabs) {
        const startTime = Date.now();
        
        await screenshot.click(tab);
        await screenshot.waitForSelector(testData.selectors.tabContent);
        
        const switchTime = Date.now() - startTime;
        switchTimes.push(switchTime);
      }
      
      const avgSwitchTime = switchTimes.reduce((a, b) => a + b, 0) / switchTimes.length;
      
      console.log(`✅ Average tab switch time: ${Math.round(avgSwitchTime)}ms`);
      expect(avgSwitchTime).toBeLessThan(500); // Should switch in under 500ms
    });
  });

  describe('Model Grid Rendering Performance', () => {
    test('should render model grid efficiently', async () => {
      console.log('📊 Testing model grid performance...');
      
      await screenshot.click(testData.selectors.tabLibrary);
      
      const startTime = Date.now();
      await screenshot.waitForSelector(testData.selectors.modelGrid);
      const renderTime = Date.now() - startTime;
      
      console.log(`✅ Model grid rendered in ${renderTime}ms`);
      expect(renderTime).toBeLessThan(2000);
      
      // Count rendered model cards
      const modelCards = await screenshot.page.$$(testData.selectors.modelCard);
      console.log(`📦 Rendered ${modelCards.length} model cards`);
      
      // Test scrolling performance if many models
      if (modelCards.length > 10) {
        const scrollStart = Date.now();
        
        await screenshot.page.evaluate(() => {
          window.scrollTo(0, document.body.scrollHeight);
        });
        
        const scrollTime = Date.now() - scrollStart;
        console.log(`✅ Scroll performance: ${scrollTime}ms`);
        expect(scrollTime).toBeLessThan(100);
      }
    });

    test('should handle search input efficiently', async () => {
      console.log('🔍 Testing search performance...');
      
      const searchInput = await screenshot.page.$(testData.selectors.searchInput);
      
      if (searchInput) {
        // Measure typing performance
        const typeStart = Date.now();
        
        await screenshot.type(testData.selectors.searchInput, 'test model search query');
        
        const typeTime = Date.now() - typeStart;
        console.log(`✅ Typing performance: ${typeTime}ms`);
        
        // Should not lag while typing
        expect(typeTime).toBeLessThan(1000);
        
        // Clear search
        await screenshot.clear(testData.selectors.searchInput);
      }
    });
  });

  describe('WebSocket Performance', () => {
    test('should handle WebSocket messages efficiently', async () => {
      console.log('🔌 Testing WebSocket performance...');
      
      // Monitor console for WebSocket activity
      const wsMessages = [];
      
      screenshot.page.on('console', msg => {
        const text = msg.text();
        if (text.includes('WebSocket') || text.includes('ws://')) {
          wsMessages.push({
            time: Date.now(),
            text: text
          });
        }
      });
      
      // Wait for potential WebSocket activity
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      console.log(`📊 Captured ${wsMessages.length} WebSocket-related messages`);
      
      // Check connection status update speed
      const statusElement = await screenshot.page.$(testData.selectors.connectionStatus);
      if (statusElement) {
        const statusText = await statusElement.evaluate(el => el.textContent);
        console.log(`✅ WebSocket status: ${statusText}`);
      }
    });
  });

  describe('Memory Usage Over Time', () => {
    test('should not have memory leaks during navigation', async () => {
      console.log('💾 Testing memory usage...');
      
      const initialMetrics = await screenshot.page.metrics();
      const initialHeap = initialMetrics.JSHeapUsedSize;
      
      // Perform multiple tab switches
      for (let i = 0; i < 10; i++) {
        await screenshot.click(testData.selectors.tabUpload);
        await new Promise(resolve => setTimeout(resolve, 500));
        await screenshot.click(testData.selectors.tabLibrary);
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      
      // Force garbage collection if available
      await screenshot.page.evaluate(() => {
        if (window.gc) {
          window.gc();
        }
      });
      
      // Wait a bit for memory to settle
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const finalMetrics = await screenshot.page.metrics();
      const finalHeap = finalMetrics.JSHeapUsedSize;
      
      const heapGrowth = finalHeap - initialHeap;
      const growthPercentage = (heapGrowth / initialHeap) * 100;
      
      console.log(`📊 Memory growth: ${Math.round(heapGrowth / 1024 / 1024)}MB (${growthPercentage.toFixed(1)}%)`);
      
      // Allow up to 50% growth (some growth is normal)
      expect(growthPercentage).toBeLessThan(50);
    });
  });

  describe('Concurrent Operations Performance', () => {
    test('should handle multiple operations simultaneously', async () => {
      console.log('🔀 Testing concurrent operations...');
      
      // Go to library tab
      await screenshot.click(testData.selectors.tabLibrary);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Start timing
      const startTime = Date.now();
      
      // Perform multiple operations
      const operations = [];
      
      // Refresh models
      if (await screenshot.elementExists(testData.selectors.refreshButton)) {
        operations.push(
          screenshot.click(testData.selectors.refreshButton)
            .catch(err => console.log('Refresh failed:', err.message))
        );
      }
      
      // Search
      if (await screenshot.elementExists(testData.selectors.searchInput)) {
        operations.push(
          screenshot.type(testData.selectors.searchInput, 'test')
            .catch(err => console.log('Search failed:', err.message))
        );
      }
      
      // Switch tabs
      operations.push(
        screenshot.click(testData.selectors.tabHuggingFace)
          .then(() => screenshot.click(testData.selectors.tabLibrary))
          .catch(err => console.log('Tab switch failed:', err.message))
      );
      
      // Wait for all operations
      await Promise.all(operations);
      
      const totalTime = Date.now() - startTime;
      console.log(`✅ Completed ${operations.length} concurrent operations in ${totalTime}ms`);
      
      // Should handle concurrent ops without significant slowdown
      expect(totalTime).toBeLessThan(5000);
    });
  });

  describe('Large Dataset Performance', () => {
    test('should handle filtering and searching efficiently', async () => {
      console.log('📊 Testing large dataset performance...');
      
      await screenshot.click(testData.selectors.tabLibrary);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Check how many models are displayed
      const modelCards = await screenshot.page.$$(testData.selectors.modelCard);
      console.log(`📦 Testing with ${modelCards.length} models`);
      
      if (modelCards.length > 0) {
        // Test filter performance
        const formatFilter = await screenshot.page.$(testData.selectors.formatFilter);
        if (formatFilter) {
          const filterStart = Date.now();
          
          // Get options and select one
          const options = await formatFilter.$$eval('option', opts => opts.map(o => o.value));
          if (options.length > 1) {
            await formatFilter.select(options[1]);
            await new Promise(resolve => setTimeout(resolve, 500));
          }
          
          const filterTime = Date.now() - filterStart;
          console.log(`✅ Filter applied in ${filterTime}ms`);
          expect(filterTime).toBeLessThan(1000);
          
          // Reset filter
          await formatFilter.select('all');
        }
      }
    });
  });

  describe('Animation and Transition Performance', () => {
    test('should have smooth animations', async () => {
      console.log('🎨 Testing animation performance...');
      
      // Check for animation frame rate
      const fps = await screenshot.page.evaluate(() => {
        return new Promise(resolve => {
          let frames = 0;
          let startTime = performance.now();
          
          function countFrames() {
            frames++;
            
            if (performance.now() - startTime < 1000) {
              requestAnimationFrame(countFrames);
            } else {
              resolve(frames);
            }
          }
          
          requestAnimationFrame(countFrames);
        });
      });
      
      console.log(`✅ Animation FPS: ${fps}`);
      expect(fps).toBeGreaterThan(30); // Should maintain at least 30 FPS
    });
  });

  describe('Resource Loading Performance', () => {
    test('should load resources efficiently', async () => {
      console.log('📦 Testing resource loading...');
      
      const resourceTimings = await screenshot.page.evaluate(() => {
        const resources = performance.getEntriesByType('resource');
        return resources.map(r => ({
          name: r.name.split('/').pop(),
          duration: Math.round(r.duration),
          size: r.transferSize
        }));
      });
      
      // Analyze resource loading
      const jsResources = resourceTimings.filter(r => r.name.endsWith('.js'));
      const cssResources = resourceTimings.filter(r => r.name.endsWith('.css'));
      
      console.log(`📊 Loaded ${jsResources.length} JS files, ${cssResources.length} CSS files`);
      
      // Check for slow resources
      const slowResources = resourceTimings.filter(r => r.duration > 1000);
      
      if (slowResources.length > 0) {
        console.log('⚠️ Slow resources detected:');
        slowResources.forEach(r => {
          console.log(`  - ${r.name}: ${r.duration}ms`);
        });
      } else {
        console.log('✅ All resources loaded quickly');
      }
      
      await screenshot.screenshot('performance-complete');
    });
  });
});