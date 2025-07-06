# IMPETUS Comprehensive Test Suite

A complete end-to-end testing framework for the IMPETUS LLM Server using Puppeteer, Jest, and browser automation.

## 🎯 Overview

This test suite provides comprehensive validation of the IMPETUS application including:

- **App Lifecycle Testing** - Launch, startup, shutdown, and restart scenarios
- **API Compatibility Testing** - Full OpenAI API compatibility validation
- **VS Code/Cline Integration** - Simulated extension workflow testing
- **Performance Testing** - Load testing, concurrent requests, memory usage
- **Web Interface Testing** - UI functionality and user experience
- **Screenshot Documentation** - Visual validation and debugging

## 🏗️ Test Architecture

```
tests/puppeteer/
├── package.json              # Dependencies and scripts
├── setup/
│   └── jest.setup.js         # Global test configuration
├── utils/
│   ├── app-controller.js     # IMPETUS app lifecycle management
│   ├── api-client.js         # OpenAI API testing utilities
│   ├── screenshot-helper.js  # Browser automation and screenshots
│   └── test-data.js          # Test scenarios and mock data
├── e2e/
│   ├── app-lifecycle.test.js # App launch/shutdown testing
│   ├── api-endpoints.test.js # API compatibility validation
│   ├── cline-simulation.test.js # VS Code extension simulation
│   └── web-interface.test.js # UI/UX testing
├── performance/
│   └── performance.test.js   # Load and performance testing
└── screenshots/              # Generated screenshots
```

## 🚀 Quick Start

### Prerequisites

1. **IMPETUS App Installed**: App must be available at `/Applications/Impetus.app`
2. **Node.js**: Version 18+ required
3. **Chrome/Chromium**: For Puppeteer browser automation

### Installation

```bash
cd tests/puppeteer
npm install
```

### Running Tests

```bash
# Run all tests
npm test

# Run specific test suites
npm run test:e2e              # End-to-end tests only
npm run test:performance      # Performance tests only
npm run test:app              # App lifecycle tests only
npm run test:api              # API endpoint tests only
npm run test:cline            # Cline simulation tests only

# Run with coverage
npm run test:coverage

# Watch mode for development
npm run test:watch
```

## 📋 Test Categories

### 1. App Lifecycle Tests (`app-lifecycle.test.js`)

**Purpose**: Validate IMPETUS application startup, health, and shutdown processes.

**Key Tests**:
- ✅ App launches successfully from `/Applications/Impetus.app`
- ✅ Server responds on `localhost:8080` within 30 seconds
- ✅ Web interface is accessible and functional
- ✅ Health endpoints return proper status
- ✅ App terminates gracefully
- ✅ App restart functionality works

**Expected Results**:
- App starts within 60 seconds
- Server health check passes
- Web interface loads without errors
- Clean shutdown with no hanging processes

### 2. API Endpoints Tests (`api-endpoints.test.js`)

**Purpose**: Comprehensive OpenAI API compatibility validation.

**Key Tests**:
- ✅ `/v1/models` endpoint returns proper format
- ✅ `/v1/chat/completions` handles all message types
- ✅ Streaming responses work correctly
- ✅ Error handling for invalid requests
- ✅ Authentication and CORS headers
- ✅ Response format matches OpenAI specification

**Expected Results**:
- 100% OpenAI API format compatibility
- Streaming responses in proper SSE format
- Appropriate error codes (400, 401, 500)
- Valid JSON responses for all endpoints

### 3. Cline Simulation Tests (`cline-simulation.test.js`)

**Purpose**: Simulate real VS Code Cline extension workflows.

**Key Tests**:
- ✅ File creation requests (typical Cline scenario)
- ✅ Code review and improvement suggestions
- ✅ Multi-turn conversations with context
- ✅ Real-time streaming for user feedback
- ✅ Refactoring and debugging assistance
- ✅ Performance under rapid request scenarios

**Expected Results**:
- Responses contain relevant code suggestions
- Streaming works for real-time feedback
- Multi-turn context is maintained
- Performance suitable for interactive use

### 4. Performance Tests (`performance.test.js`)

**Purpose**: Validate performance characteristics under various loads.

**Key Tests**:
- ✅ Response time benchmarks (health, models, chat)
- ✅ Concurrent request handling (5-50 simultaneous)
- ✅ Memory leak detection over time
- ✅ Streaming performance validation
- ✅ Stress testing with high request volumes
- ✅ Performance consistency over time

**Expected Results**:
- Health check: < 1 second
- Models endpoint: < 2 seconds  
- Chat completion: < 30 seconds
- 80%+ success rate under load
- No memory leaks during extended use

### 5. Web Interface Tests (`web-interface.test.js`)

**Purpose**: Validate user interface functionality and experience.

**Key Tests**:
- ✅ Main interface loads and renders properly
- ✅ Responsive design across device sizes
- ✅ Hardware information display
- ✅ Model management interface
- ✅ Status and monitoring displays
- ✅ Navigation and user interaction
- ✅ Error handling and user feedback

**Expected Results**:
- Interface loads within 5 seconds
- No JavaScript console errors
- Responsive design works on mobile/tablet/desktop
- Interactive elements function properly

## 🖼️ Screenshot Documentation

The test suite automatically captures screenshots for:

- **Interface States**: Main page, model selection, error pages
- **Responsive Views**: Desktop, tablet, mobile layouts
- **Test Validation**: Visual confirmation of functionality
- **Debugging**: Error states and unexpected behaviors

Screenshots are saved to `tests/puppeteer/screenshots/` with timestamps.

## 📊 Test Results and Reports

### Jest HTML Reports

After running tests, view detailed results:

```bash
open test-report.html
```

The report includes:
- ✅ Pass/fail status for all tests
- ⏱️ Execution times and performance metrics
- 🖼️ Screenshot links for visual validation
- 📝 Detailed error messages and stack traces

### Coverage Reports

```bash
npm run test:coverage
open coverage/lcov-report/index.html
```

## 🔧 Configuration

### Environment Variables

Create `.env` file in the test directory:

```env
IMPETUS_APP_PATH=/Applications/Impetus.app
IMPETUS_BASE_URL=http://localhost:8080
IMPETUS_API_KEY=sk-dev-gerdsen-ai-local-development-key
TEST_TIMEOUT=60000
HEADLESS_BROWSER=false
```

### Jest Configuration

Key settings in `package.json`:

```json
{
  "jest": {
    "testEnvironment": "node",
    "testTimeout": 60000,
    "setupFilesAfterEnv": ["<rootDir>/setup/jest.setup.js"]
  }
}
```

## 🚨 Troubleshooting

### Common Issues

**1. App Not Found**
```
Error: IMPETUS app not found at /Applications/Impetus.app
```
**Solution**: Ensure IMPETUS is properly installed and accessible.

**2. Server Startup Timeout**
```
Error: Server failed to start within 30000ms
```
**Solution**: Check if port 8080 is available, increase timeout, or restart IMPETUS.

**3. Browser Launch Failure**
```
Error: Failed to launch browser
```
**Solution**: Install Chrome/Chromium or set `HEADLESS_BROWSER=true`.

**4. API Authentication Errors**
```
Error: Request failed with status code 401
```
**Solution**: Verify API key in test configuration matches server settings.

### Debug Mode

Run tests in debug mode with visible browser:

```bash
HEADLESS_BROWSER=false npm test
```

View detailed logging:

```bash
DEBUG=puppeteer:* npm test
```

## 🎯 Success Criteria

### MVP Testing Goals

For IMPETUS to pass MVP validation, the following must succeed:

- ✅ **App Lifecycle**: Launch, health check, basic API access
- ✅ **OpenAI Compatibility**: `/v1/models` and `/v1/chat/completions` work
- ✅ **Cline Integration**: Basic chat completion with proper format
- ✅ **Performance**: Reasonable response times for interactive use

### Production Testing Goals

For production readiness, additional requirements:

- ✅ **Load Testing**: Handle 50+ concurrent requests
- ✅ **Error Handling**: Graceful degradation under stress
- ✅ **UI Testing**: Full interface functionality
- ✅ **Memory Management**: No leaks during extended use

## 🔄 Continuous Integration

### GitHub Actions Example

```yaml
name: IMPETUS Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install IMPETUS
        run: # Install IMPETUS app
      - name: Run Test Suite
        run: |
          cd tests/puppeteer
          npm install
          npm test
      - name: Upload Screenshots
        uses: actions/upload-artifact@v3
        with:
          name: test-screenshots
          path: tests/puppeteer/screenshots/
```

## 🤝 Contributing

### Adding New Tests

1. **Create Test File**: Add to appropriate directory (`e2e/`, `performance/`)
2. **Follow Patterns**: Use existing utilities (`AppController`, `ApiClient`)
3. **Add Screenshots**: Capture key states for debugging
4. **Update Documentation**: Document new test scenarios

### Test Guidelines

- **Descriptive Names**: Clear test descriptions and console output
- **Proper Cleanup**: Always terminate apps and close browsers
- **Realistic Scenarios**: Test actual user workflows
- **Performance Aware**: Set appropriate timeouts for operations
- **Screenshot Everything**: Visual validation is crucial

## 📚 Additional Resources

- [Puppeteer Documentation](https://pptr.dev/)
- [Jest Testing Framework](https://jestjs.io/)
- [OpenAI API Specification](https://platform.openai.com/docs/api-reference)
- [VS Code Cline Extension](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev)

---

**Status**: ✅ Production Ready - Complete test coverage for IMPETUS LLM Server

**Last Updated**: July 6, 2025

**Maintainer**: GerdsenAI Development Team
