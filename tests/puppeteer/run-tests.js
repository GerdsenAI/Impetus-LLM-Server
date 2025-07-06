#!/usr/bin/env node

/**
 * IMPETUS Test Suite Runner
 * 
 * Simple script to run tests and provide summary
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

console.log('🚀 IMPETUS Comprehensive Test Suite');
console.log('=====================================\n');

// Check prerequisites
function checkPrerequisites() {
  console.log('🔍 Checking prerequisites...');
  
  // Check if IMPETUS app exists
  const appPath = '/Applications/Impetus.app';
  if (!fs.existsSync(appPath)) {
    console.error('❌ IMPETUS app not found at', appPath);
    console.error('   Please install IMPETUS before running tests');
    process.exit(1);
  }
  
  console.log('✅ IMPETUS app found');
  
  // Check Node.js version
  const nodeVersion = process.version;
  const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
  if (majorVersion < 18) {
    console.error('❌ Node.js 18+ required, found', nodeVersion);
    process.exit(1);
  }
  
  console.log('✅ Node.js version:', nodeVersion);
  
  // Check if dependencies are installed
  if (!fs.existsSync(path.join(__dirname, 'node_modules'))) {
    console.log('📦 Installing dependencies...');
    try {
      execSync('npm install', { stdio: 'inherit', cwd: __dirname });
    } catch (error) {
      console.error('❌ Failed to install dependencies');
      process.exit(1);
    }
  }
  
  console.log('✅ Dependencies ready\n');
}

// Run test suites
function runTests() {
  const testSuites = [
    {
      name: 'App Lifecycle',
      command: 'npm run test:app',
      description: 'Tests app launch, startup, and shutdown'
    },
    {
      name: 'API Endpoints', 
      command: 'npm run test:api',
      description: 'Tests OpenAI API compatibility'
    },
    {
      name: 'Cline Integration',
      command: 'npm run test:cline', 
      description: 'Tests VS Code extension compatibility'
    },
    {
      name: 'Performance',
      command: 'npm run test:performance',
      description: 'Tests load and performance characteristics'
    },
    {
      name: 'Web Interface',
      command: 'npm run test -- --testPathPattern=web-interface',
      description: 'Tests UI/UX functionality'
    }
  ];
  
  const results = [];
  
  for (const suite of testSuites) {
    console.log(`🧪 Running ${suite.name} Tests`);
    console.log(`   ${suite.description}`);
    console.log(`   Command: ${suite.command}\n`);
    
    const startTime = Date.now();
    
    try {
      execSync(suite.command, { 
        stdio: 'inherit', 
        cwd: __dirname,
        timeout: 300000 // 5 minutes per suite
      });
      
      const duration = Date.now() - startTime;
      results.push({
        name: suite.name,
        status: 'PASSED',
        duration: Math.round(duration / 1000)
      });
      
      console.log(`✅ ${suite.name} tests PASSED (${Math.round(duration / 1000)}s)\n`);
      
    } catch (error) {
      const duration = Date.now() - startTime;
      results.push({
        name: suite.name,
        status: 'FAILED',
        duration: Math.round(duration / 1000)
      });
      
      console.log(`❌ ${suite.name} tests FAILED (${Math.round(duration / 1000)}s)\n`);
    }
  }
  
  return results;
}

// Print summary
function printSummary(results) {
  console.log('\n📊 Test Suite Summary');
  console.log('====================\n');
  
  const passed = results.filter(r => r.status === 'PASSED').length;
  const failed = results.filter(r => r.status === 'FAILED').length;
  const total = results.length;
  
  results.forEach(result => {
    const icon = result.status === 'PASSED' ? '✅' : '❌';
    console.log(`${icon} ${result.name}: ${result.status} (${result.duration}s)`);
  });
  
  console.log('\n' + '='.repeat(50));
  console.log(`Total Suites: ${total}`);
  console.log(`Passed: ${passed}`);
  console.log(`Failed: ${failed}`);
  console.log(`Success Rate: ${Math.round((passed / total) * 100)}%`);
  
  if (failed === 0) {
    console.log('\n🎉 All tests PASSED! IMPETUS is working correctly.');
    console.log('   - App lifecycle: ✅ Working');
    console.log('   - API compatibility: ✅ Working'); 
    console.log('   - VS Code integration: ✅ Working');
    console.log('   - Performance: ✅ Acceptable');
    console.log('   - Web interface: ✅ Functional');
  } else {
    console.log(`\n⚠️  ${failed} test suite(s) failed.`);
    console.log('   Check the output above for details.');
    console.log('   See tests/puppeteer/README.md for troubleshooting.');
  }
  
  console.log('\n📸 Screenshots saved to: tests/puppeteer/screenshots/');
  console.log('📄 Detailed report: test-report.html');
  
  return failed === 0;
}

// Main execution
async function main() {
  try {
    checkPrerequisites();
    const results = runTests();
    const success = printSummary(results);
    
    process.exit(success ? 0 : 1);
    
  } catch (error) {
    console.error('\n❌ Test runner failed:', error.message);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { main, checkPrerequisites, runTests, printSummary };
