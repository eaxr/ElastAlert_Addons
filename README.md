ElastAlert Rules: rules/test_rule.yaml

Custom Telegram Module:

alert:

"elastalert_modules.telegram_alerter_module.TelegramAlerter" Options:

telegram_use_markdown: "custom" - Use telegram Markdown for ElastAlert rules "https://core.telegram.org/bots/api#markdown-style"

telegram_limit_option: "elasticsearch" - creates an index "elastalert_status_test" and loads a message from ElastAlert into it if the message was cropped according to telegram limits
