// Variables used by Scriptable.
// These must be at the very top of the file. Do not edit.
// always-run-in-app: true; icon-color: deep-green;
// icon-glyph: magic;
const GITHUB_TOKEN = 'github token';
const GITHUB_REPO = 'gys619/surge-tools';
const GITHUB_BRANCH = 'main';

// 模块配置 (增加 `folder` 字段)
const MODULE_CONFIGS = [
  {
    name: "去广告规则",
    url: "http://script.hub/file/_start_/https://raw.githubusercontent.com/fmz200/wool_scripts/main/Loon/rule/rejectAd.list/_end_/rejectAd.list?type=rule-set&target=surge-rule-set&del=true",
    folder: "rules"
  },
  {
    name: "夸克网盘",
    url: "http://script.hub/file/_start_/https://gist.githubusercontent.com/Sliverkiss/1589f69e675019b0b685a57a89de9ea5/raw/quarkV2.js/_end_/quarkV2.sgmodule?type=qx-rewrite&target=surge-module&del=true",
    folder: "modules"
  },
  {
    name: "广告拦截&净化合集",
    url: "http://script.hub/file/_start_/https://github.com/fmz200/wool_scripts/raw/main/Loon/plugin/blockAds.plugin/_end_/blockAds.sgmodule?type=loon-plugin&target=surge-module&del=true",
    folder: "adblock"
  },{
    name: "广告拦截&净化合集规则",
    url: "http://script.hub/file/_start_/https://github.com/fmz200/wool_scripts/raw/main/Loon/rule/rejectAd.list/_end_/rejectAd.list?type=rule-set&target=surge-rule-set&del=true",
    folder: "rules"
  },{
    name: "抖音",
    url: "http://script.hub/file/_start_/https://github.com/blackmatrix7/ios_rule_script/raw/master/rule/QuantumultX/DouYin/DouYin.list/_end_/DouYin.list?type=rule-set&target=surge-rule-set&del=true",
    folder: "rules"
  },{
    name: "可莉去广告合集",
    url: "http://script.hub/file/_start_/https://kelee.one/Tool/Loon/Plugin/Remove_ads_by_keli.plugin/_end_/Remove_ads_by_keli.sgmodule?type=loon-plugin&target=surge-module&del=true",
    folder: "modules"
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

// MD5 hash calculation function
function calculateMD5(str) {
  function rotateLeft(lValue, iShiftBits) {
    return (lValue << iShiftBits) | (lValue >>> (32 - iShiftBits));
  }

  function addUnsigned(lX, lY) {
    const lX8 = lX & 0x80000000;
    const lY8 = lY & 0x80000000;
    const lX4 = lX & 0x40000000;
    const lY4 = lY & 0x40000000;
    const lResult = (lX & 0x3FFFFFFF) + (lY & 0x3FFFFFFF);
    if (lX4 & lY4) return lResult ^ 0x80000000 ^ lX8 ^ lY8;
    if (lX4 | lY4) {
      if (lResult & 0x40000000) return lResult ^ 0xC0000000 ^ lX8 ^ lY8;
      else return lResult ^ 0x40000000 ^ lX8 ^ lY8;
    } else return lResult ^ lX8 ^ lY8;
  }

  function F(x, y, z) { return (x & y) | ((~x) & z); }
  function G(x, y, z) { return (x & z) | (y & (~z)); }
  function H(x, y, z) { return x ^ y ^ z; }
  function I(x, y, z) { return y ^ (x | (~z)); }

  function FF(a, b, c, d, x, s, ac) {
    a = addUnsigned(a, addUnsigned(addUnsigned(F(b, c, d), x), ac));
    return addUnsigned(rotateLeft(a, s), b);
  }

  function GG(a, b, c, d, x, s, ac) {
    a = addUnsigned(a, addUnsigned(addUnsigned(G(b, c, d), x), ac));
    return addUnsigned(rotateLeft(a, s), b);
  }

  function HH(a, b, c, d, x, s, ac) {
    a = addUnsigned(a, addUnsigned(addUnsigned(H(b, c, d), x), ac));
    return addUnsigned(rotateLeft(a, s), b);
  }

  function II(a, b, c, d, x, s, ac) {
    a = addUnsigned(a, addUnsigned(addUnsigned(I(b, c, d), x), ac));
    return addUnsigned(rotateLeft(a, s), b);
  }

  function convertToWordArray(str) {
    let wordCount;
    const messageLength = str.length;
    wordCount = (messageLength + 8 >> 6) * 16 + 14;
    const wordArray = Array(wordCount - 1);
    let bytePosition = 0;
    let byteCount = 0;
    while (byteCount < messageLength) {
      const currentWordCount = (byteCount - (byteCount % 4)) / 4;
      const currentBytePosition = (byteCount % 4) * 8;
      wordArray[currentWordCount] = (wordArray[currentWordCount] || 0) | (str.charCodeAt(byteCount) << currentBytePosition);
      byteCount++;
    }
    const finalWordCount = (byteCount - (byteCount % 4)) / 4;
    const finalBytePosition = (byteCount % 4) * 8;
    wordArray[finalWordCount] = wordArray[finalWordCount] | (0x80 << finalBytePosition);
    wordArray[wordCount - 14] = messageLength * 8;
    return wordArray;
  }

  function wordToHex(lValue) {
    let WordToHexValue = "", WordToHexValue_temp = "", lByte, lCount;
    for (lCount = 0; lCount <= 3; lCount++) {
      lByte = (lValue >>> (lCount * 8)) & 255;
      WordToHexValue_temp = "0" + lByte.toString(16);
      WordToHexValue = WordToHexValue + WordToHexValue_temp.substr(WordToHexValue_temp.length - 2, 2);
    }
    return WordToHexValue;
  }

  const x = convertToWordArray(str);
  let a = 0x67452301;
  let b = 0xEFCDAB89;
  let c = 0x98BADCFE;
  let d = 0x10325476;

  for (let k = 0; k < x.length; k += 16) {
    const AA = a;
    const BB = b;
    const CC = c;
    const DD = d;

    a = FF(a, b, c, d, x[k + 0], 7, 0xD76AA478);
    d = FF(d, a, b, c, x[k + 1], 12, 0xE8C7B756);
    c = FF(c, d, a, b, x[k + 2], 17, 0x242070DB);
    b = FF(b, c, d, a, x[k + 3], 22, 0xC1BDCEEE);
    a = FF(a, b, c, d, x[k + 4], 7, 0xF57C0FAF);
    d = FF(d, a, b, c, x[k + 5], 12, 0x4787C62A);
    c = FF(c, d, a, b, x[k + 6], 17, 0xA8304613);
    b = FF(b, c, d, a, x[k + 7], 22, 0xFD469501);
    a = FF(a, b, c, d, x[k + 8], 7, 0x698098D8);
    d = FF(d, a, b, c, x[k + 9], 12, 0x8B44F7AF);
    c = FF(c, d, a, b, x[k + 10], 17, 0xFFFF5BB1);
    b = FF(b, c, d, a, x[k + 11], 22, 0x895CD7BE);
    a = FF(a, b, c, d, x[k + 12], 7, 0x6B901122);
    d = FF(d, a, b, c, x[k + 13], 12, 0xFD987193);
    c = FF(c, d, a, b, x[k + 14], 17, 0xA679438E);
    b = FF(b, c, d, a, x[k + 15], 22, 0x49B40821);

    a = GG(a, b, c, d, x[k + 1], 5, 0xF61E2562);
    d = GG(d, a, b, c, x[k + 6], 9, 0xC040B340);
    c = GG(c, d, a, b, x[k + 11], 14, 0x265E5A51);
    b = GG(b, c, d, a, x[k + 0], 20, 0xE9B6C7AA);
    a = GG(a, b, c, d, x[k + 5], 5, 0xD62F105D);
    d = GG(d, a, b, c, x[k + 10], 9, 0x2441453);
    c = GG(c, d, a, b, x[k + 15], 14, 0xD8A1E681);
    b = GG(b, c, d, a, x[k + 4], 20, 0xE7D3FBC8);
    a = GG(a, b, c, d, x[k + 9], 5, 0x21E1CDE6);
    d = GG(d, a, b, c, x[k + 14], 9, 0xC33707D6);
    c = GG(c, d, a, b, x[k + 3], 14, 0xF4D50D87);
    b = GG(b, c, d, a, x[k + 8], 20, 0x455A14ED);
    a = GG(a, b, c, d, x[k + 13], 5, 0xA9E3E905);
    d = GG(d, a, b, c, x[k + 2], 9, 0xFCEFA3F8);
    c = GG(c, d, a, b, x[k + 7], 14, 0x676F02D9);
    b = GG(b, c, d, a, x[k + 12], 20, 0x8D2A4C8A);

    a = HH(a, b, c, d, x[k + 5], 4, 0xFFFA3942);
    d = HH(d, a, b, c, x[k + 8], 11, 0x8771F681);
    c = HH(c, d, a, b, x[k + 11], 16, 0x6D9D6122);
    b = HH(b, c, d, a, x[k + 14], 23, 0xFDE5380C);
    a = HH(a, b, c, d, x[k + 1], 4, 0xA4BEEA44);
    d = HH(d, a, b, c, x[k + 4], 11, 0x4BDECFA9);
    c = HH(c, d, a, b, x[k + 7], 16, 0xF6BB4B60);
    b = HH(b, c, d, a, x[k + 10], 23, 0xBEBFBC70);
    a = HH(a, b, c, d, x[k + 13], 4, 0x289B7EC6);
    d = HH(d, a, b, c, x[k + 0], 11, 0xEAA127FA);
    c = HH(c, d, a, b, x[k + 3], 16, 0xD4EF3085);
    b = HH(b, c, d, a, x[k + 6], 23, 0x4881D05);
    a = HH(a, b, c, d, x[k + 9], 4, 0xD9D4D039);
    d = HH(d, a, b, c, x[k + 12], 11, 0xE6DB99E5);
    c = HH(c, d, a, b, x[k + 15], 16, 0x1FA27CF8);
    b = HH(b, c, d, a, x[k + 2], 23, 0xC4AC5665);

    a = II(a, b, c, d, x[k + 0], 6, 0xF4292244);
    d = II(d, a, b, c, x[k + 7], 10, 0x432AFF97);
    c = II(c, d, a, b, x[k + 14], 15, 0xAB9423A7);
    b = II(b, c, d, a, x[k + 5], 21, 0xFC93A039);
    a = II(a, b, c, d, x[k + 12], 6, 0x655B59C3);
    d = II(d, a, b, c, x[k + 3], 10, 0x8F0CCC92);
    c = II(c, d, a, b, x[k + 10], 15, 0xFFEFF47D);
    b = II(b, c, d, a, x[k + 1], 21, 0x85845DD1);
    a = II(a, b, c, d, x[k + 8], 6, 0x6FA87E4F);
    d = II(d, a, b, c, x[k + 15], 10, 0xFE2CE6E0);
    c = II(c, d, a, b, x[k + 6], 15, 0xA3014314);
    b = II(b, c, d, a, x[k + 13], 21, 0x4E0811A1);
    a = II(a, b, c, d, x[k + 4], 6, 0xF7537E82);
    d = II(d, a, b, c, x[k + 11], 10, 0xBD3AF235);
    c = II(c, d, a, b, x[k + 2], 15, 0x2AD7D2BB);
    b = II(b, c, d, a, x[k + 9], 21, 0xEB86D391);

    a = addUnsigned(a, AA);
    b = addUnsigned(b, BB);
    c = addUnsigned(c, CC);
    d = addUnsigned(d, DD);
  }

  return (wordToHex(a) + wordToHex(b) + wordToHex(c) + wordToHex(d)).toLowerCase();
}

// 从内容中提取现有的哈希值
function extractExistingHash(content) {
  const hashMatch = content.match(/#!HASH=([a-f0-9]{32})/i);
  return hashMatch ? hashMatch[1] : null;
}

// 计算内容的哈希值（排除元数据）
function calculateContentHash(content) {
  // 移除元数据（包括现有的哈希值、订阅链接等）
  let cleanContent = content
    .replace(/#!HASH=[a-f0-9]{32}\n?/gi, '')
    .replace(/^#SUBSCRIBED.*?\n?/gim, '')
    .replace(/^# 🔗.*?\n?/gm, '')
    .replace(/^#!desc=.*?\n?/gim, '')
    .trim();
  
  return calculateMD5(cleanContent);
}

// 从 GitHub 获取文件内容
async function getGitHubFileContent(filePath) {
  try {
    const url = `https://api.github.com/repos/${GITHUB_REPO}/contents/${filePath}?ref=${GITHUB_BRANCH}`;
    const req = new Request(url);
    req.headers = {
      'Authorization': `token ${GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'Scriptable'
    };
    const response = await req.loadJSON();
    if (response.content) {
      // 使用 atob 进行 base64 解码
      const content = atob(response.content.replace(/\n/g, ''));
      return content;
    }
  } catch (e) {
    console.log(`获取 GitHub 文件失败: ${filePath}, 错误: ${e.message}`);
  }
  return null;
}

// 处理模块内容，添加或更新 Hash
function processModuleContent(content, hash, url) {
  let processedText = content;
  
  // 移除旧的订阅链接和哈希值
  processedText = processedText
    .replace(/^(#SUBSCRIBED|# 🔗 模块链接)(.*?)(\n|$)/gim, '')
    .replace(/#!HASH=[a-f0-9]{32}\n?/gi, '');

  const subscribed = `#SUBSCRIBED ${url}`;
  const hashComment = `#!HASH=${hash}`;
  
  // 查找备注头的位置
  const descMatch = processedText.match(/^#!desc=.*$/m);
  
  if (descMatch) {
    // 在备注头后添加 Hash
    const descLine = descMatch[0];
    processedText = processedText.replace(descLine, `${descLine} ${hashComment}`);
  } else {
    // 如果没有备注头，在开头添加 Hash
    processedText = `${hashComment}\n${processedText}`;
  }
  
  // 添加订阅链接到末尾
  processedText = `${processedText.trim()}\n\n# 🔗 模块链接\n${subscribed}\n`;
  
  return processedText;
}

async function processModule(moduleConfig) {
  try {
    const req = new Request(moduleConfig.url);
    req.timeoutInterval = 10;
    req.method = 'GET';
    const responseText = await req.loadString();

    if (!responseText) throw new Error('未获取到模块内容');

    // 生成文件名
    const urlParts = moduleConfig.url.split('/');
    let fileNameFromUrl = urlParts.pop().split('?')[0];
    if (fileNameFromUrl.includes('.')) {
      fileNameFromUrl = fileNameFromUrl.split('.').slice(0, -1).join('.');
    }

    const urlExtension = moduleConfig.url.split('.').pop().split('?')[0];
    const validName = convertToValidFileName(fileNameFromUrl || moduleConfig.name);
    const finalFileName = urlExtension.match(/sgmodule|list/) 
      ? `${validName}.${urlExtension}`
      : `${validName}.sgmodule`;

    const folder = moduleConfig.folder ? `${moduleConfig.folder}/` : "";
    const fileName = `${folder}${finalFileName}`;

    // 计算新内容的哈希值
    const contentHash = calculateContentHash(responseText);
    
    // 尝试从 GitHub 获取现有文件内容，但不影响后续流程
    let shouldUpdate = true;
    try {
      const existingContent = await getGitHubFileContent(fileName);
      if (existingContent) {
        const existingHash = extractExistingHash(existingContent);
        if (existingHash && existingHash === contentHash) {
          console.log(`⏭️ 跳过更新: ${moduleConfig.name} (内容未变化)`);
          shouldUpdate = false;
        }
      }
    } catch (e) {
      console.log(`⚠️ 无法获取 GitHub 文件，将继续更新: ${fileName}`);
    }

    if (shouldUpdate) {
      // 处理内容
      let processedText = processModuleContent(responseText, contentHash, moduleConfig.url);
      
      // 更新时间戳
      processedText = processedText.replace(/^#\!desc\s*?=\s*/im, `#!desc=🔗 [${new Date().toLocaleString()}] `);

      uploadQueue.push({ filename: fileName, content: processedText });
      console.log(`✅ 处理完成: ${fileName} (已更新)`);
    }

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
  let alert = new Alert();
  alert.title = '处理完成';
  alert.message = `✅ 成功: ${success}\n❌ 失败: ${fail}`;
  alert.addCancelAction('关闭');
  await alert.presentAlert();
}

await main();