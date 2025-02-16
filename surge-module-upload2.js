// GitHub 配置
const GITHUB_TOKEN = 'github的token';
const GITHUB_REPO = 'gys619/surge-tools';
const GITHUB_BRANCH = 'main';

// 模块配置 (增加 `folder` 字段)
const MODULE_CONFIGS = [
  {
    name: "达美乐",
    url: "http://script.hub/file/_start_/https://gist.githubusercontent.com/Sliverkiss/6b4da0d367d13790a9fd1d928c82bdf8/raw/dlm.js/_end_/dlm.sgmodule?type=qx-rewrite&target=surge-module&del=true",
    folder: "module"
  },
  {
    name: "夸克网盘",
    url: "http://script.hub/file/_start_/https://gist.githubusercontent.com/Sliverkiss/1589f69e675019b0b685a57a89de9ea5/raw/quarkV2.js/_end_/?type=qx-rewrite&target=surge-module&del=true",
    folder: "modules"
  },
  {
    name: "广告拦截&净化合集",
    url: "http://script.hub/file/_start_/https://github.com/fmz200/wool_scripts/raw/main/Loon/plugin/blockAds.plugin/_end_/blockAds.sgmodule?n=blockAds&type=loon-plugin&target=surge-module&del=true",
    folder: "adblock"
  }
];

// 处理非法文件名字符
function convertToValidFileName(str) {
  return str.replace(/[\/:*?"<>|]/g, '_').replace(/\.{2,}/g, '.').replace(/^[\s.]+|[\s.]+$/g, '');
}

// 延迟函数（适用于 Scriptable）
async function delay(milliseconds) {
  return new Promise(resolve => {
    Timer.schedule(milliseconds / 1000, false, resolve);
  });
}

// 上传队列
let uploadQueue = [];

async function processModule(moduleConfig) {
  try {
    const req = new Request(moduleConfig.url);
    req.timeoutInterval = 10;
    req.method = 'GET';
    const responseText = await req.loadString();

    if (!responseText) throw new Error('未获取到模块内容');

    const nameMatched = responseText.match(/^#\!name\s*?=\s*?\s*(.*?)\s*(\n|$)/im);
    let name = nameMatched ? nameMatched[1] : moduleConfig.name;
    
    if (!name) throw new Error('模块无名称字段');

    // 纠正 `广告拦截&净化合集` 以 `blockAds.sgmodule` 作为文件名
    if (moduleConfig.name === "广告拦截&净化合集") {
      name = "blockAds";
    }

    let processedText = responseText;
    const subscribed = `#SUBSCRIBED ${moduleConfig.url}`;
    processedText = processedText.replace(/^(#SUBSCRIBED|# 🔗 模块链接)(.*?)(\n|$)/gim, '');
    processedText = `${processedText}\n\n# 🔗 模块链接\n${subscribed}\n`;
    processedText = processedText.replace(/^#\!desc\s*?=\s*/im, `#!desc=🔗 [${new Date().toLocaleString()}] `);

    // **确保文件路径正确**
    const folder = moduleConfig.folder ? `${moduleConfig.folder}/` : "";
    const fileName = `${folder}${convertToValidFileName(name)}.sgmodule`;

    uploadQueue.push({ filename: fileName, content: processedText });

    console.log(`✅ 处理完成: ${fileName}`);
    return true;
  } catch (e) {
    console.error(`❌ 处理失败: ${moduleConfig.name}: ${e.message}`);
    return false;
  }
}

// **恢复你的 GitHub 上传逻辑**
async function batchUploadToGitHub() {
  if (uploadQueue.length === 0) return true;

  try {
    const refUrl = `https://api.github.com/repos/${GITHUB_REPO}/git/refs/heads/${GITHUB_BRANCH}`;
    const refReq = new Request(refUrl);
    refReq.headers = {
      'Authorization': `token ${GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'Scriptable'
    };
    const refData = await refReq.loadJSON();
    const latestCommitSha = refData.object.sha;

    const commitUrl = `https://api.github.com/repos/${GITHUB_REPO}/git/commits/${latestCommitSha}`;
    const commitReq = new Request(commitUrl);
    commitReq.headers = refReq.headers;
    const commitData = await commitReq.loadJSON();
    const baseTreeSha = commitData.tree.sha;

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
        path: filename,
        mode: '100644',
        type: 'blob',
        sha: blobData.sha
      };
    }));

    const treeUrl = `https://api.github.com/repos/${GITHUB_REPO}/git/trees`;
    const treeReq = new Request(treeUrl);
    treeReq.method = 'POST';
    treeReq.headers = refReq.headers;
    treeReq.body = JSON.stringify({
      base_tree: baseTreeSha,
      tree: blobs
    });
    const treeData = await treeReq.loadJSON();

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

    const updateRefReq = new Request(refUrl);
    updateRefReq.method = 'PATCH';
    updateRefReq.headers = refReq.headers;
    updateRefReq.body = JSON.stringify({
      sha: newCommitData.sha,
      force: true
    });
    await updateRefReq.loadJSON();

    console.log(`✅ 成功上传 ${uploadQueue.length} 个文件`);
    uploadQueue = [];
    return true;

  } catch (e) {
    console.error(`❌ 上传失败: ${e.message}`);
    return false;
  }
}

// 主函数
async function main() {
  let success = 0, fail = 0;
  
  for (const moduleConfig of MODULE_CONFIGS) {
    if (await processModule(moduleConfig)) {
      success++;
    } else {
      fail++;
    }
    await delay(1000);
  }

  if (uploadQueue.length > 0) {
    const uploaded = await batchUploadToGitHub();
    if (!uploaded) fail += uploadQueue.length;
  }

  console.log(`✅ 成功: ${success}, ❌ 失败: ${fail}`);
}

await main();