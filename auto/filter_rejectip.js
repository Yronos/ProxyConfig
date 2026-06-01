// auto/filter_rejectip.js
import fs from "fs";
import https from "https";
import { contains, exclude, merge } from "fast-cidr-tools";

const CHINA_IPV4_URL =
  "https://raw.githubusercontent.com/SukkaLab/ruleset.skk.moe/refs/heads/master/Clash/ip/china_ip.txt";
const CHINA_IPV6_URL =
  "https://raw.githubusercontent.com/SukkaLab/ruleset.skk.moe/refs/heads/master/Clash/ip/china_ip_ipv6.txt";

const CLOUD_PROVIDERS = [
  {
    name: "sukka reject ip",
    url: "https://ruleset.skk.moe/List/ip/reject.conf",
  },
];

const OUTPUT_DIR = "rules/RejectIP";

async function fetchText(url) {
  return new Promise((resolve, reject) => {
    https
      .get(url, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          const lines = data
            .split("\n")
            .map((l) => l.trim())
            .filter((l) => l && !l.startsWith("#") && !l.startsWith("//"));
          resolve(lines);
        });
      })
      .on("error", reject);
  });
}

async function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

async function main() {
  console.log("🚀 开始获取中国 IP 列表...");
  const [chinaIPv4, chinaIPv6] = await Promise.all([
    fetchText(CHINA_IPV4_URL),
    fetchText(CHINA_IPV6_URL),
  ]);

  console.log(`中国 IPv4: ${chinaIPv4.length} 条`);
  console.log(`中国 IPv6: ${chinaIPv6.length} 条`);

  await ensureDir(OUTPUT_DIR);

  for (const provider of CLOUD_PROVIDERS) {
    console.log(`\n📥 处理 ${provider.name} (${provider.url})`);

    const raw = await fetchText(provider.url);

    const ipv4List = raw.filter((ip) => !ip.includes(":"));
    const ipv6List = raw.filter((ip) => ip.includes(":"));

    console.log(
      `原始数据 → IPv4: ${ipv4List.length} | IPv6: ${ipv6List.length}`,
    );

    // 保留中国 IP 部分
    let filteredIPv4 = contains(ipv4List, chinaIPv4);
    let filteredIPv6 = contains(ipv6List, chinaIPv6);

    // 合并优化（推荐用于代理规则）
    filteredIPv4 = merge(filteredIPv4);
    filteredIPv6 = merge(filteredIPv6);

    // 输出文件
    const basePath = `${OUTPUT_DIR}/${provider.name}_contain_china`;

    fs.writeFileSync(`${basePath}.txt`, filteredIPv4.join("\n"));
    console.log(
      `✅ ${provider.name}_contain_china.txt → ${filteredIPv4.length} 条 IPv4`,
    );

    if (filteredIPv6.length > 0) {
      fs.writeFileSync(`${basePath}_ipv6.txt`, filteredIPv6.join("\n"));
      console.log(
        `✅ ${provider.name}_contain_china_ipv6.txt → ${filteredIPv6.length} 条 IPv6`,
      );
    }
  }

  console.log("\n🎉 全部处理完成！");
}

main().catch((err) => {
  console.error("❌ 执行失败:", err);
  process.exit(1);
});
