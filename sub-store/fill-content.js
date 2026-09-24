$content = $content.replaceAll("{{SING_BOX_LISTEN}}", "127.0.0.1");
$content = $content.replaceAll("{{SING_BOX_API_SECRET}}", "abcdef");
$content = $content.replaceAll("{{SING_BOX_API_CORS_ORIGINS}}", "http://sing-box-dashboard.sagernet.org");
$content = $content.replaceAll("{{EXTERNAL_CONTROLLER}}", "127.0.0.1:9090");
$content = $content.replaceAll("{{CLASH_API_SECRET}}", "abcdef");
$content = $content.replaceAll("{{CLASH_API_CORS_ORIGINS}}", "http://127.0.0.1:1234");
