# image-config.md

## Status

Image generation is an **optional extension**. Do not execute image generation unless the user explicitly enables it in this conversation.

- **用户未要求配图**：静默跳过，不输出任何提示，继续文章写作流程。
- **用户明确要求配图，但本配置文件缺失或字段不完整**：停止配图流程，向用户输出中文提示："配图配置（image-config.md）尚未设置，无法生成图片。请填写 provider、api_key_env 等必填字段后重试。"

## Design Goal

After outline and article drafting, analyze paragraph semantics, generate high-quality text-to-image prompts, call an external image generation API, save images to `workspace/images/`, and insert Markdown image references into the article.

## Configuration Fields

```yaml
provider: ""           # e.g. openai, stability, replicate
api_base_url: ""       # API endpoint base URL
api_key_env: ""        # Name of the environment variable holding the API key (never hardcode)
model: ""              # e.g. dall-e-3, stable-diffusion-xl
image_size: ""         # e.g. 1024x1024, 1792x1024
style_preset: ""       # Optional style hint passed to the API
output_dir: "workspace/images"
insert_policy: "after_section"  # after_section | end_of_article | manual
```

## Safety Rules

- Never hardcode API keys. Read keys from environment variables only.
- If `api_key_env` is not set in the environment and the user explicitly requested images, stop and prompt the user in Chinese: "环境变量 {api_key_env} 未设置，无法调用图片生成 API，请先配置后重试。"
- If image generation fails at runtime, continue article writing without images and notify the user in Chinese.
