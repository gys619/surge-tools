// Variables used by Scriptable.
// These must be at the very top of the file. Do not edit.
// icon-color: deep-green; icon-glyph: cloud-upload-alt;

// GitHub configuration
const GITHUB_TOKEN = 'github的Token';
const GITHUB_REPO = 'gys619/surge-tools';
const GITHUB_BRANCH = 'main';

// 模块配置
const MODULE_CONFIGS = [
  {
    name: "蜜雪冰城",
    url: "http://script.hub/file/_start_/https://gist.githubusercontent.com/Sliverkiss/865c82e42a5730bb696f6700ebb94cee/raw/mxbc.js/_end_/mxbc.sgmodule?n=%E8%9C%9C%E9%9B%AA%E5%86%B0%E5%9F%8E%E7%AD%BE%E5%88%B0&type=qx-rewrite&target=surge-module&del=true"
  },
  {
    name: "夸克网盘",
    url: "http://script.hub/file/_start_/https://gist.githubusercontent.com/Sliverkiss/1589f69e675019b0b685a57a89de9ea5/raw/quarkV2.js/_end_/quarkV2.sgmodule?type=qx-rewrite&target=surge-module&del=true"
  }
  // 可以继续添加更多模块配置
];

// 用于自定义发送请求的请求头
const reqHeaders = {
  headers: {
    'User-Agent': 'script-hub/1.0.0',
  },
}

async function delay(milliseconds) {
  return new Promise(resolve => {
    Timer.schedule(milliseconds / 1000, false, () => {
      resolve();
    });
  });
}

function convertToValidFileName(str) {
  const invalidCharsRegex = /[\/:*?"<>|]/g
  const validFileName = str.replace(invalidCharsRegex, '_')
  const multipleDotsRegex = /\.{2,}/g
  const fileNameWithoutMultipleDots = validFileName.replace(multipleDotsRegex, '.')
  const leadingTrailingDotsSpacesRegex = /^[\s.]+|[\s.]+$/g
  const finalFileName = fileNameWithoutMultipleDots.replace(leadingTrailingDotsSpacesRegex, '')
  return finalFileName
}

async function uploadToGitHub(filename, content) {
  const encodedPath = encodeURIComponent(`modules/${filename}`)
  const message = `Update ${filename}`
  const url = `https://api.github.com/repos/${GITHUB_REPO}/contents/${encodedPath}`
  
  console.log(`Uploading to: ${url}`);
  
  let sha
  try {
    const checkReq = new Request(url)
    checkReq.headers = {
      'Authorization': `Bearer ${GITHUB_TOKEN}`,
      'Content-Type': 'application/json',
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'Scriptable'
    }
    const checkRes = await checkReq.loadJSON()
    sha = checkRes.sha
  } catch (e) {
    console.log(`Check file exists error: ${e.message}`);
  }

  const req = new Request(url)
  req.method = 'PUT'
  req.headers = {
    'Authorization': `Bearer ${GITHUB_TOKEN}`,
    'Content-Type': 'application/json',
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'Scriptable'
  }
  
  const body = {
    message: message,
    content: Data.fromString(content).toBase64String(),
    branch: GITHUB_BRANCH
  }
  
  if (sha) {
    body.sha = sha
  }
  
  req.body = JSON.stringify(body)
  
  try {
    const res = await req.loadJSON()
    console.log(`Upload response: ${JSON.stringify(res)}`);
    return true
  } catch (e) {
    console.error(`Upload failed: ${e.message}`);
    console.error(`Response: ${req.response?.statusCode} ${req.response?.statusText}`);
    console.error(`Body: ${req.response?.body}`);
    return false
  }
}

async function processModule(moduleConfig) {
  try {
    const req = new Request(moduleConfig.url)
    req.timeoutInterval = 10
    req.method = 'GET'
    req.headers = reqHeaders.headers
    let res = await req.loadString()
    
    if (!res) {
      throw new Error('未获取到模块内容')
    }

    const nameMatched = res.match(/^#\!name\s*?=\s*?\s*(.*?)\s*(\n|$)/im)
    if (!nameMatched) {
      throw new Error('不是合法的模块内容')
    }
    
    const name = nameMatched[1] || moduleConfig.name
    if (!name) {
      throw new Error('模块无名称字段')
    }

    const subscribed = `#SUBSCRIBED ${moduleConfig.url}`
    res = res.replace(/^(#SUBSCRIBED|# 🔗 模块链接)(.*?)(\n|$)/gim, '')
    res = `${res}\n\n# 🔗 模块链接\n${subscribed}\n`
    
    res = res.replace(/^#\!desc\s*?=\s*/im, `#!desc=🔗 [${new Date().toLocaleString()}] `)

    const fileName = `${convertToValidFileName(name)}.sgmodule`
    
    const uploaded = await uploadToGitHub(fileName, res)
    
    if (uploaded) {
      console.log(`✅ 成功处理并上传: ${fileName}`)
      return true
    } else {
      throw new Error('GitHub上传失败')
    }
    
  } catch (e) {
    console.error(`❌ 处理失败: ${moduleConfig.name}: ${e.message}`)
    return false
  }
}

async function main() {
  if (!GITHUB_TOKEN || !GITHUB_REPO) {
    console.error('请先配置 GITHUB_TOKEN 和 GITHUB_REPO');
    return;
  }

  let success = 0
  let fail = 0
  
  for (const moduleConfig of MODULE_CONFIGS) {
    if (await processModule(moduleConfig)) {
      success++
    } else {
      fail++
    }
    await delay(1000)
  }

  let alert = new Alert()
  alert.title = '处理完成'
  alert.message = `✅ 成功: ${success}\n❌ 失败: ${fail}`
  // alert.addAction('重载 Surge')
  // alert.addAction('打开 Surge')
  alert.addCancelAction('关闭')
  
  const idx = await alert.presentAlert()
  if (idx === 0) {
    const req = new Request('http://script.hub/reload')
    req.timeoutInterval = 10
    req.method = 'GET'
    await req.loadString()
  } else if (idx === 1) {
    Safari.open('surge://')
  }
}

await main() 