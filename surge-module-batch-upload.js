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
    // 链接填Script-hub转换的链接
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

// 添加一个队列来存储待上传的文件
let uploadQueue = [];

async function batchUploadToGitHub() {
  if (uploadQueue.length === 0) return true;
  
  try {
    // 1. 获取当前分支的引用
    const refUrl = `https://api.github.com/repos/${GITHUB_REPO}/git/refs/heads/${GITHUB_BRANCH}`;
    const refReq = new Request(refUrl);
    refReq.headers = {
      'Authorization': `token ${GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'Scriptable'
    };
    const refData = await refReq.loadJSON();
    const latestCommitSha = refData.object.sha;
    console.log(`Current commit SHA: ${latestCommitSha}`);

    // 2. 获取当前提交
    const commitUrl = `https://api.github.com/repos/${GITHUB_REPO}/git/commits/${latestCommitSha}`;
    const commitReq = new Request(commitUrl);
    commitReq.headers = refReq.headers;
    const commitData = await commitReq.loadJSON();
    const baseTreeSha = commitData.tree.sha;
    console.log(`Base tree SHA: ${baseTreeSha}`);

    // 3. 创建新的 blobs
    const blobs = await Promise.all(uploadQueue.map(async ({ filename, content }) => {
      const blobUrl = `https://api.github.com/repos/${GITHUB_REPO}/git/blobs`;
      const blobReq = new Request(blobUrl);
      blobReq.method = 'POST';
      blobReq.headers = refReq.headers;
      blobReq.body = JSON.stringify({
        content: content,
        encoding: 'utf-8'
      });
      const blobData = await blobReq.loadJSON();
      return {
        path: `modules/${filename}`,
        mode: '100644',
        type: 'blob',
        sha: blobData.sha
      };
    }));

    // 4. 创建新的树
    const treeUrl = `https://api.github.com/repos/${GITHUB_REPO}/git/trees`;
    const treeReq = new Request(treeUrl);
    treeReq.method = 'POST';
    treeReq.headers = refReq.headers;
    treeReq.body = JSON.stringify({
      base_tree: baseTreeSha,
      tree: blobs
    });
    const treeData = await treeReq.loadJSON();
    console.log(`New tree SHA: ${treeData.sha}`);

    // 5. 创建新的提交
    const newCommitUrl = `https://api.github.com/repos/${GITHUB_REPO}/git/commits`;
    const newCommitReq = new Request(newCommitUrl);
    newCommitReq.method = 'POST';
    newCommitReq.headers = refReq.headers;
    newCommitReq.body = JSON.stringify({
      message: `Batch update ${uploadQueue.length} modules\n\nFiles:\n${uploadQueue.map(f => `- ${f.filename}`).join('\n')}`,
      tree: treeData.sha,
      parents: [latestCommitSha]
    });
    const newCommitData = await newCommitReq.loadJSON();
    console.log(`New commit SHA: ${newCommitData.sha}`);

    // 6. 更新分支引用
    const updateRefReq = new Request(refUrl);
    updateRefReq.method = 'PATCH';
    updateRefReq.headers = refReq.headers;
    updateRefReq.body = JSON.stringify({
      sha: newCommitData.sha,
      force: true
    });
    await updateRefReq.loadJSON();

    console.log(`Successfully created commit with ${uploadQueue.length} files`);
    uploadQueue = [];
    return true;

  } catch (e) {
    console.error(`Batch upload failed: ${e.message}`);
    if (e.response) {
      console.error(`Status: ${e.response.statusCode}`);
      console.error(`Response: ${e.response.body}`);
    }
    return false;
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
    
    // 不直接上传，而是加入队列
    uploadQueue.push({
      filename: fileName,
      content: res
    });
    
    console.log(`✅ 成功处理: ${fileName}`);
    return true;
    
  } catch (e) {
    console.error(`❌ 处理失败: ${moduleConfig.name}: ${e.message}`);
    return false;
  }
}

async function main() {
  if (!GITHUB_TOKEN || !GITHUB_REPO) {
    console.error('请先配置 GITHUB_TOKEN 和 GITHUB_REPO');
    return;
  }

  let success = 0;
  let fail = 0;
  
  // 先处理所有模块
  for (const moduleConfig of MODULE_CONFIGS) {
    if (await processModule(moduleConfig)) {
      success++;
    } else {
      fail++;
    }
    await delay(1000);
  }

  // 最后进行批量上传
  if (uploadQueue.length > 0) {
    const uploaded = await batchUploadToGitHub();
    if (!uploaded) {
      console.error('批量上传失败');
      fail += uploadQueue.length;
      success = 0;
    }
  }

  let alert = new Alert();
  alert.title = '处理完成';
  alert.message = `✅ 成功: ${success}\n❌ 失败: ${fail}`;
  alert.addCancelAction('关闭');
  await alert.presentAlert();
}

await main(); 