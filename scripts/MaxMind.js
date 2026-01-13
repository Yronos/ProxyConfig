// MaxMind GeoIP2 for Quantumult X
// $response.statusCode, $response.headers, $response.body

if ($response.statusCode != 200) {
  $done(null);
}

// ========== 工具函数 ==========

/**
 * IP 地址格式化
 * IPv4: 转换为下标数字
 * IPv6: 保持原样
 */
function formatIP(ip) {
  // IPv6 直接返回原样
  if (ip.indexOf(":") !== -1) {
    return ip;
  }

  // IPv4 转换为下标
  var map = {
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
  return ip
    .split("")
    .map(function (c) {
      return map[c] || c;
    })
    .join("");
}

function getFlag(code) {
  if (!code || code.length !== 2) return "🌐";
  var codePoints = code
    .toUpperCase()
    .split("")
    .map(function (c) {
      return 127397 + c.charCodeAt(0);
    });
  return String.fromCodePoint.apply(null, codePoints);
}

function getName(namesObj) {
  if (!namesObj) return null;
  if (namesObj["zh-CN"]) return namesObj["zh-CN"].trim();
  if (namesObj["en"]) return namesObj["en"].trim();
  var keys = Object.keys(namesObj);
  if (keys.length > 0 && namesObj[keys[0]]) {
    return String(namesObj[keys[0]]).trim();
  }
  return null;
}

// ========== 解析响应 ==========

var body = $response.body;
var obj = JSON.parse(body);

var ip = (obj.traits && obj.traits.ip_address) || "N/A";
var countryCode = (obj.country && obj.country.iso_code) || "";
var flag = getFlag(countryCode);

// 位置降级：城市 -> 州/省 -> 国家
var city = obj.city && obj.city.names ? getName(obj.city.names) : null;
var region =
  obj.subdivisions && obj.subdivisions[0] && obj.subdivisions[0].names
    ? getName(obj.subdivisions[0].names)
    : null;
var country =
  obj.country && obj.country.names ? getName(obj.country.names) : null;
var location = city || region || country || "未知位置";

// ISP 降级：ISP -> Organization -> ASN Org
var isp = null,
  network = null,
  asn = null;
if (obj.traits) {
  isp =
    obj.traits.isp ||
    obj.traits.organization ||
    obj.traits.autonomous_system_organization ||
    null;
  network = obj.traits.network || null;
  asn = obj.traits.autonomous_system_number
    ? "AS" + obj.traits.autonomous_system_number
    : null;
}

var timezone = (obj.location && obj.location.time_zone) || null;

// ========== 构建输出 ==========

var title = flag + " " + location + " " + formatIP(ip);

var subtitleParts = [];
if (isp) {
  subtitleParts.push(asn ? isp + " (" + asn + ")" : isp);
} else if (asn) {
  subtitleParts.push(asn);
} else if (network) {
  subtitleParts.push(network);
}
if (timezone) subtitleParts.push(timezone);

var subtitle =
  subtitleParts.length > 0 ? subtitleParts.join(" | ") : "数据不足";

// ========== 输出 ==========

$done({
  title: title,
  subtitle: subtitle,
  ip: ip,
});
