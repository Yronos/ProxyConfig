// ip-api.com for Quantumult X
if ($response.statusCode != 200) {
  $done(null);
}

// 默认值
const DEFAULTS = {
  city: "未知位置",
  isp: "未知 ISP",
  timezone: "未知时区",
};

// IPv4 下标数字映射
const SUBSCRIPT_MAP = {
  0: "₀",
  1: "₁",
  2: "₂",
  3: "₃",
  4: "₄",
  5: "₅",
  6: "₆",
  7: "₇",
  8: "₈",
  9: "₉",
  ".": ".",
};

// 动态生成国旗 Emoji + TW 强制显示 CN 国旗
function getFlagEmoji(countryCode) {
  if (
    !countryCode ||
    typeof countryCode !== "string" ||
    countryCode.length !== 2
  ) {
    return "🏳️";
  }

  const code = countryCode.toUpperCase();

  // 特殊处理：TW 返回 CN 国旗
  if (code === "TW") {
    return "🇨🇳";
  }

  // 动态 Unicode 生成国旗
  const codePoints = code.split("").map((char) => 127397 + char.charCodeAt(0));

  return String.fromCodePoint(...codePoints);
}

// IP 转下标（IPv4 美化，IPv6 保持原样）
function toSubscript(str) {
  if (!str) return "N/A";
  if (str.indexOf(":") !== -1) return str; // IPv6
  return str
    .toString()
    .split("")
    .map((c) => SUBSCRIPT_MAP[c] || c)
    .join("");
}

// ==================== 主逻辑 ====================
var body = $response.body;
var obj = JSON.parse(body);

// 提取数据（适配 ip-api.com 结构）
var country = obj.country || "Unknown";
var countryCode = obj.countryCode || "";
var city = obj.city || DEFAULTS.city;
var ip = obj.query || "N/A";
var isp = obj.isp || obj.org || obj.as || DEFAULTS.isp;
var timezone = obj.timezone || DEFAULTS.timezone;

// 动态国旗（已包含 TW→CN 逻辑）
var flag = getFlagEmoji(countryCode);

// 格式化输出
var title = flag + " " + city + " " + toSubscript(ip);
var subtitle = isp + " | " + timezone;
var description = country + "\n" + city + "\n" + isp + "\n" + timezone;

// 严格遵循官方格式
$done({ title, subtitle, ip, description });
