/**
 * MaxMind GeoIP2
 * 适用于 Quantumult X
 *
 * 功能：
 * - 智能数据降级（城市 -> 州/省 -> 国家）
 * - ISP 信息降级（ISP -> Organization -> Network）
 * - 完善的空值处理
 * - 兼容旧版 JavaScript
 *
 */

// ========== 状态检查 ==========
if ($response.statusCode != 200) {
  $done(null);
}

// ========== 工具函数 ==========

/**
 * 将 IP 地址转换为下标数字格式
 * 例如：192.168.1.1 -> ₁₉₂.₁₆₈.₁.₁
 */
function toSubscript(str) {
  const map = {
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
  return str
    .split("")
    .map(function (c) {
      return map[c] || c;
    })
    .join("");
}

/**
 * 动态生成国旗 Emoji
 * 根据 ISO 3166-1 alpha-2 国家代码生成
 */
function getFlag(code) {
  if (!code || code.length !== 2) return "��";

  return String.fromCodePoint.apply(
    null,
    code
      .toUpperCase()
      .split("")
      .map(function (c) {
        return 127397 + c.charCodeAt(0);
      }),
  );
}

/**
 * 从多语言名称对象中获取值
 * 优先级：zh-CN > en > 其他
 *
 * @param {Object} namesObj - MaxMind 的 names 对象
 * @returns {String|null} - 名称或 null
 */
function getName(namesObj) {
  if (!namesObj) return null;

  // 优先中文
  if (namesObj["zh-CN"]) {
    return namesObj["zh-CN"].trim();
  }

  // 其次英文
  if (namesObj["en"]) {
    return namesObj["en"].trim();
  }

  // 最后尝试其他语言
  var keys = Object.keys(namesObj);
  if (keys.length > 0) {
    var value = namesObj[keys[0]];
    if (value && typeof value === "string") {
      return value.trim();
    }
  }

  return null;
}

// ========== 数据解析 ==========

var obj = JSON.parse($response.body);

// IP 地址
var ip = (obj.traits && obj.traits.ip_address) || "N/A";

// 国家代码和国旗
var countryCode = (obj.country && obj.country.iso_code) || "";
var flag = getFlag(countryCode);

// 位置信息（降级策略）
var city = obj.city && obj.city.names ? getName(obj.city.names) : null;

var region =
  obj.subdivisions && obj.subdivisions[0] && obj.subdivisions[0].names
    ? getName(obj.subdivisions[0].names)
    : null;

var country =
  obj.country && obj.country.names ? getName(obj.country.names) : null;

var location = city || region || country || "未知位置";

// ISP 信息（降级策略）
var isp = null;
if (obj.traits) {
  isp =
    obj.traits.isp ||
    obj.traits.organization ||
    obj.traits.autonomous_system_organization ||
    null;
}

// ASN 编号
var asn =
  obj.traits && obj.traits.autonomous_system_number
    ? "AS" + obj.traits.autonomous_system_number
    : null;

// 网络段（兜底显示）
var network = (obj.traits && obj.traits.network) || null;

// 时区
var timezone = (obj.location && obj.location.time_zone) || null;

// ========== 构建输出 ==========

// 第一行：国旗 + 位置 + IP
var title = flag + " " + location + " " + toSubscript(ip);

// 第二行：ISP/网络 + 时区
var subtitleParts = [];

if (isp) {
  // 最佳情况：有 ISP 名称
  var ispInfo = isp;
  if (asn) {
    ispInfo += " (" + asn + ")";
  }
  subtitleParts.push(ispInfo);
} else if (network) {
  // 次优情况：显示网络段
  subtitleParts.push(network);
}

if (timezone) {
  subtitleParts.push(timezone);
}

// 如果什么数据都没有
var subtitle =
  subtitleParts.length > 0 ? subtitleParts.join(" | ") : "数据不足";

// ========== 输出结果 ==========

$done({
  title: title,
  subtitle: subtitle,
  ip: ip,
});
