export default {
  testDir:'${REPO_ROOT}/web/tests-e2e',
  outputDir:'${EVIDENCE_ROOT}/offline-catalog-e2e-results',
  fullyParallel:false,workers:2,retries:0,
  reporter:[['json',{outputFile:'${EVIDENCE_ROOT}/offline-catalog-e2e-receipt.json'}],['list']],
  use:{baseURL:'http://127.0.0.1:43922',trace:'retain-on-failure',
    launchOptions:{executablePath:'${CHROMIUM_EXECUTABLE}'}},
  projects:[{name:'desktop',use:{viewport:{width:1440,height:900}}},
    {name:'mobile',use:{viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:2}}],
  webServer:{command:'npm run preview -- --host 127.0.0.1 --port 43922 --strictPort',
    cwd:'${REPO_ROOT}/web',url:'http://127.0.0.1:43922',reuseExistingServer:false,timeout:60000}
};
