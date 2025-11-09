use std::{sync::Arc, time::Duration};

use async_openai::{
    Client as AsyncOpenAIClient,
    config::OpenAIConfig,
    types::{
        ChatCompletionRequestAssistantMessage, ChatCompletionRequestAssistantMessageContent,
        ChatCompletionRequestMessage, ChatCompletionRequestMessageContentPartImage,
        ChatCompletionRequestMessageContentPartText, ChatCompletionRequestSystemMessage,
        ChatCompletionRequestSystemMessageContent, ChatCompletionRequestUserMessage,
        ChatCompletionRequestUserMessageContent, ChatCompletionRequestUserMessageContentPart,
        CreateChatCompletionRequest, CreateImageRequestArgs, Image, ImageDetail, ImageQuality,
        ImageResponseFormat, ImageSize, ImageStyle, ImageUrl, ListModelResponse, Stop,
    },
};
use cached::proc_macro::cached;

use base64::{Engine as _, engine::general_purpose::STANDARD as BASE64};
use model::{
    Model, ModelIO, ModelOutput, ModelTask, ModelTaskKind, ModelType,
    common::{
        async_trait::async_trait,
        eyre::{Result, bail, eyre},
        inflector::Inflector,
        itertools::Itertools,
        tracing,
    },
    schema::{ImageObject, InstructionAttachment, MessagePart, MessageRole},
    secrets,
};
use reqwest::{Client as HttpClient, multipart};
use serde::{Deserialize, Serialize};

/// The name of the env var or secret for the API key
const API_KEY: &str = "OPENAI_API_KEY";

/// A model running on OpenAI
pub struct OpenAIModel {
    /// The OpenAI name for a model including any tag e.g. "llama2:13b"
    ///
    /// Used as the required `model` parameter in each request to `POST /api/generate`
    /// (along with `prompt`).
    model: String,

    /// The context length of the model
    context_length: usize,

    /// The type of input that the model consumes
    inputs: Vec<ModelIO>,

    /// The type of output that the model generates
    outputs: Vec<ModelIO>,
}

impl OpenAIModel {
    /// Create an OpenAI-based model
    fn new(
        model: String,
        context_length: usize,
        inputs: Vec<ModelIO>,
        outputs: Vec<ModelIO>,
    ) -> Self {
        Self {
            model,
            context_length,
            inputs,
            outputs,
        }
    }
}

#[async_trait]
impl Model for OpenAIModel {
    fn id(&self) -> String {
        format!("openai/{}", self.model)
    }

    fn r#type(&self) -> ModelType {
        ModelType::Remote
    }

    fn provider(&self) -> String {
        "OpenAI".to_string()
    }

    fn name(&self) -> String {
        if self.model.starts_with("gpt") {
            "GPT".to_string()
        } else if self.model.starts_with("tts") {
            "TTS".to_string()
        } else if self.model.starts_with("dall-e") {
            "DALL·E".to_string()
        } else {
            let name = self
                .model
                .split_once('-')
                .map(|(name, ..)| name)
                .unwrap_or(self.model.as_str());
            name.to_title_case()
        }
    }

    fn version(&self) -> String {
        let model = if self.model.starts_with("dall-e") {
            self.model.replace("dall-e", "dall_e")
        } else {
            self.model.clone()
        };
        let version = model
            .split_once('-')
            .map(|(.., version)| version)
            .unwrap_or_default();
        version.to_string()
    }

    fn context_length(&self) -> usize {
        self.context_length
    }

    fn supported_inputs(&self) -> &[ModelIO] {
        &self.inputs
    }

    fn supported_outputs(&self) -> &[ModelIO] {
        &self.outputs
    }

    async fn perform_task(&self, task: &ModelTask) -> Result<ModelOutput> {
        match task.kind {
            ModelTaskKind::MessageGeneration => self.message_generation(task).await,
            ModelTaskKind::ImageGeneration => self.image_generation(task).await,
        }
    }
}

impl OpenAIModel {
    /// Create a client with the correct API key
    fn client() -> Result<AsyncOpenAIClient<OpenAIConfig>> {
        let api_key = secrets::env_or_get(API_KEY)?;
        Ok(AsyncOpenAIClient::with_config(
            OpenAIConfig::new().with_api_key(api_key),
        ))
    }

    fn should_upload_attachment(attachment: &InstructionAttachment) -> bool {
        match attachment.file.media_type.as_deref() {
            Some(media_type) if media_type.eq_ignore_ascii_case("application/pdf") => true,
            Some(media_type) if media_type.starts_with("image/") => true,
            Some(media_type) if media_type.starts_with("audio/") => true,
            Some(media_type) if media_type.starts_with("video/") => true,
            _ => false,
        }
    }

    fn should_retry_with_vision(model: &str, error_body: &str) -> bool {
        (model.starts_with("gpt-5") || model.starts_with("gpt-4.1"))
            && (error_body.contains("Invalid input") && error_body.contains("context stuffing")
                || error_body.contains("does not support image inputs"))
    }

    fn map_to_vision_model(model: &str) -> Option<String> {
        if model.starts_with("gpt-5") {
            Some("gpt-4.1-mini".to_string())
        } else if model.starts_with("gpt-4.1") {
            Some("gpt-4o-mini".to_string())
        } else {
            None
        }
    }

    #[tracing::instrument(skip_all)]
    async fn message_generation(&self, task: &ModelTask) -> Result<ModelOutput> {
        if let Some(attachments) = task
            .attachments
            .as_ref()
            .filter(|attachments| !attachments.is_empty())
        {
            if !self.supports_attachments() {
                bail!(
                    "Model `{}` does not yet support file attachments. Select an OpenAI `gpt-5*` model or remove attachments.",
                    self.id()
                );
            }

            if task.dry_run {
                return ModelOutput::empty(self);
            }

            return self.responses_message_generation(task, attachments).await;
        }

        tracing::debug!("Sending chat completion request");

        let messages = task
            .messages
            .iter()
            .map(|message| match message.role.unwrap_or_default() {
                MessageRole::System => {
                    ChatCompletionRequestMessage::System(ChatCompletionRequestSystemMessage {
                        content: ChatCompletionRequestSystemMessageContent::Text(
                            message
                                .parts
                                .iter()
                                .filter_map(|part| match part {
                                    MessagePart::Text(text) => Some(text.to_value_string()),
                                    _ => {
                                        tracing::warn!(
                                            "System message part `{part}` is ignored by model `{}`",
                                            self.id()
                                        );
                                        None
                                    }
                                })
                                .join("\n\n"),
                        ),
                        ..Default::default()
                    })
                }
                MessageRole::User => {
                    let content = message
                        .parts
                        .iter()
                        .filter_map(|part| match part {
                            MessagePart::Text(text) => {
                                Some(ChatCompletionRequestUserMessageContentPart::Text(
                                    ChatCompletionRequestMessageContentPartText {
                                        text: text.to_value_string(),
                                    },
                                ))
                            }
                            MessagePart::ImageObject(ImageObject { content_url, .. }) => {
                                Some(ChatCompletionRequestUserMessageContentPart::ImageUrl(
                                    ChatCompletionRequestMessageContentPartImage {
                                        image_url: ImageUrl {
                                            url: content_url.clone(),
                                            detail: Some(ImageDetail::Auto),
                                        },
                                    },
                                ))
                            }
                            _ => {
                                tracing::warn!(
                                    "User message part `{part}` is ignored by model `{}`",
                                    self.id()
                                );
                                None
                            }
                        })
                        .collect_vec();

                    ChatCompletionRequestMessage::User(ChatCompletionRequestUserMessage {
                        content: ChatCompletionRequestUserMessageContent::Array(content),
                        ..Default::default()
                    })
                }
                MessageRole::Model => {
                    let content = ChatCompletionRequestAssistantMessageContent::Text(
                        message
                            .parts
                            .iter()
                            .filter_map(|part| match part {
                                MessagePart::Text(text) => Some(text.to_value_string()),
                                _ => {
                                    tracing::warn!(
                                        "Assistant message part `{part}` is ignored by model `{}`",
                                        self.id()
                                    );
                                    None
                                }
                            })
                            .join(""),
                    );

                    ChatCompletionRequestMessage::Assistant(ChatCompletionRequestAssistantMessage {
                        content: Some(content),
                        ..Default::default()
                    })
                }
            })
            .collect();

        // Create the request
        let request = CreateChatCompletionRequest {
            model: self.model.clone(),
            messages,
            presence_penalty: task.repeat_penalty,
            temperature: task.temperature,
            seed: task.seed.map(|seed| seed as i64),
            max_completion_tokens: task.max_tokens.map(|tokens| tokens as u32),
            top_p: task.top_p,
            stop: task.stop.clone().map(Stop::String),
            ..Default::default()
        };

        // Warn about ignored task options
        macro_rules! ignore_option {
            ($name:ident) => {
                if task.$name.is_some() {
                    tracing::warn!(
                        "Option `{}` is ignored by model `{}` for chat completion",
                        stringify!($name),
                        self.name()
                    )
                }
            };
            ($($name:ident),*) => {
                $( ignore_option!($name); )*
            }
        }
        ignore_option!(
            mirostat,
            mirostat_eta,
            mirostat_tau,
            num_ctx,
            num_gqa,
            num_gpu,
            num_thread,
            repeat_last_n,
            tfs_z,
            top_k
        );

        if task.dry_run {
            return ModelOutput::empty(self);
        }

        // Send the request
        let client = Self::client()?;
        let mut response = client.chat().create(request).await?;

        // Get the content of the first message
        let text = response
            .choices
            .pop()
            .and_then(|choice| choice.message.content)
            .unwrap_or_default();

        ModelOutput::from_text(self, &task.format, text).await
    }

    fn supports_attachments(&self) -> bool {
        self.inputs.contains(&ModelIO::Image)
            || self.inputs.contains(&ModelIO::Audio)
            || self.inputs.contains(&ModelIO::Video)
    }

    #[tracing::instrument(skip_all)]
    async fn responses_message_generation(
        &self,
        task: &ModelTask,
        attachments: &[InstructionAttachment],
    ) -> Result<ModelOutput> {
        tracing::debug!("Sending responses request with attachments");

        let api_key = secrets::env_or_get(API_KEY)?;
        let http_client = HttpClient::builder()
            .timeout(Duration::from_secs(120))
            .build()?;

        let mut uploaded = Vec::new();
        let mut attempted_upload = false;
        for attachment in attachments {
            if !Self::should_upload_attachment(attachment) {
                tracing::debug!(
                    "Skipping upload for attachment `{}` with media type {:?}",
                    attachment.alias,
                    attachment.file.media_type
                );
                continue;
            }

            attempted_upload = true;
            match self
                .upload_attachment(&http_client, &api_key, attachment)
                .await
            {
                Ok(uploaded_attachment) => uploaded.push(uploaded_attachment),
                Err(error) => {
                    tracing::warn!(
                        "Failed to upload attachment `{}`: {error}",
                        attachment.alias
                    );
                }
            }
        }

        let mut messages = self.messages_to_response_input(task);

        if attempted_upload && uploaded.is_empty() {
            bail!("No attachments were uploaded successfully.");
        }

        if let Some(position) = messages.iter().rposition(|message| message.role == "user") {
            if !uploaded.is_empty() {
                for attachment in &uploaded {
                    messages[position].content.extend(attachment.to_contents());
                }
            }
        } else if !uploaded.is_empty() {
            messages.push(ResponseMessage {
                role: "user".to_string(),
                content: uploaded
                    .iter()
                    .flat_map(UploadedAttachment::to_contents)
                    .collect(),
            });
        }

        let mut request = ResponsesRequest {
            model: self.model.clone(),
            input: messages,
            temperature: task.temperature,
            top_p: task.top_p,
            stop: task.stop.as_ref().map(|stop| vec![stop.clone()]),
            seed: task.seed,
            max_output_tokens: task.max_tokens,
        };

        let response = http_client
            .post("https://api.openai.com/v1/responses")
            .bearer_auth(&api_key)
            .header("OpenAI-Beta", "assistants=v2")
            .json(&request)
            .send()
            .await?;

        let response = if response.status().is_success() {
            response.json::<ResponsesResponse>().await?
        } else {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            tracing::warn!("OpenAI responses API returned {status}: {body}");

            if Self::should_retry_with_vision(&self.model, &body) {
                if let Some(mapped) = Self::map_to_vision_model(&self.model) {
                    tracing::info!(
                        "Retrying attachment request with vision-capable model `{}`",
                        mapped
                    );
                    request.model = mapped;

                    let retry = http_client
                        .post("https://api.openai.com/v1/responses")
                        .bearer_auth(&api_key)
                        .header("OpenAI-Beta", "assistants=v2")
                        .json(&request)
                        .send()
                        .await?;

                    if retry.status().is_success() {
                        retry.json::<ResponsesResponse>().await?
                    } else {
                        let retry_status = retry.status();
                        let retry_body = retry.text().await.unwrap_or_default();
                        bail!(
                            "OpenAI responses API returned {retry_status} after vision retry: {retry_body}"
                        );
                    }
                } else {
                    bail!("OpenAI responses API returned {status}: {body}");
                }
            } else {
                bail!("OpenAI responses API returned {status}: {body}");
            }
        };

        let mut text_segments = Vec::new();
        for item in response.output {
            for content in item.content {
                match content {
                    ResponseOutputContent::OutputText { text } => text_segments.push(text),
                    ResponseOutputContent::SummaryText { text } => text_segments.push(text),
                    _ => {}
                }
            }
        }

        let text = text_segments.join("\n").trim().to_string();

        if text.is_empty() {
            bail!("OpenAI response did not contain output text");
        }

        ModelOutput::from_text(self, &task.format, text).await
    }

    #[tracing::instrument(skip_all)]
    async fn upload_attachment(
        &self,
        client: &HttpClient,
        api_key: &str,
        attachment: &InstructionAttachment,
    ) -> Result<UploadedAttachment> {
        let bytes = attachment_bytes(attachment)?;
        let filename = if attachment.file.name.trim().is_empty() {
            format!("{}.bin", attachment.alias)
        } else {
            attachment.file.name.clone()
        };
        let media_type = attachment
            .file
            .media_type
            .clone()
            .unwrap_or_else(|| "application/octet-stream".to_string());

        tracing::debug!(
            "Uploading attachment `{}` ({} bytes, {})",
            attachment.alias,
            bytes.len(),
            media_type
        );

        let part = multipart::Part::bytes(bytes)
            .file_name(filename.clone())
            .mime_str(&media_type)?;

        let form = multipart::Form::new()
            .text("purpose", "assistants")
            .part("file", part);

        let response = client
            .post("https://api.openai.com/v1/files")
            .bearer_auth(&api_key)
            .header("OpenAI-Beta", "assistants=v2")
            .multipart(form)
            .send()
            .await?;

        let response = if response.status().is_success() {
            response.json::<UploadFileResponse>().await?
        } else {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            bail!("OpenAI file upload returned {status}: {body}");
        };

        Ok(UploadedAttachment {
            alias: attachment.alias.clone(),
            file_id: response.id,
            media_type,
        })
    }

    fn messages_to_response_input(&self, task: &ModelTask) -> Vec<ResponseMessage> {
        task.messages
            .iter()
            .map(|message| {
                let role = match message.role.unwrap_or_default() {
                    MessageRole::System => "system",
                    MessageRole::User => "user",
                    MessageRole::Model => "assistant",
                }
                .to_string();

                let content = message
                    .parts
                    .iter()
                    .filter_map(|part| match part {
                        MessagePart::Text(text) => {
                            if role == "assistant" {
                                Some(ResponseContent::OutputText {
                                    text: text.to_value_string(),
                                })
                            } else {
                                Some(ResponseContent::InputText {
                                    text: text.to_value_string(),
                                })
                            }
                        }
                        MessagePart::ImageObject(ImageObject { content_url, .. }) => Some(
                            ResponseContent::InputImage {
                                file_id: None,
                                image_url: Some(content_url.clone()),
                            },
                        ),
                        other => {
                            tracing::warn!(
                                "Message part `{other}` is currently unsupported by OpenAI Responses API"
                            );
                            None
                        }
                    })
                    .collect();

                ResponseMessage { role, content }
            })
            .collect()
    }

    #[tracing::instrument(skip_all)]
    async fn image_generation(&self, task: &ModelTask) -> Result<ModelOutput> {
        tracing::debug!("Sending image generation request");

        // Create a prompt from the last message (assumed to be a user message)
        let prompt = task
            .messages
            .last()
            .map(|message| {
                message
                    .parts
                    .iter()
                    .flat_map(|part| match part {
                        MessagePart::Text(text) => Some(text.to_value_string()),
                        _ => {
                            tracing::warn!(
                                "Message part `{part}` is ignored by model `{}`",
                                self.id()
                            );
                            None
                        }
                    })
                    .join("")
            })
            .unwrap_or_default();

        // Create the request
        let mut request = CreateImageRequestArgs::default();
        let request = request
            .prompt(prompt)
            .response_format(ImageResponseFormat::Url);

        if let Some((w, h)) = task.image_size {
            match (w, h) {
                (256, 256) => {
                    request.size(ImageSize::S256x256);
                }
                (512, 512) => {
                    request.size(ImageSize::S512x512);
                }
                (1024, 1024) => {
                    request.size(ImageSize::S1024x1024);
                }
                (1024, 1792) => {
                    request.size(ImageSize::S1024x1792);
                }
                (1792, 1024) => {
                    request.size(ImageSize::S1792x1024);
                }
                _ => bail!("Unsupported image size `{w}x{h}`"),
            };
        }

        if let Some(quality) = &task.image_quality {
            match quality.to_lowercase().as_str() {
                "std" | "standard" => {
                    request.quality(ImageQuality::Standard);
                }
                "hd" | "high-definition" => {
                    request.quality(ImageQuality::HD);
                }
                _ => bail!("Unsupported image quality `{quality}`"),
            };
        }

        if let Some(style) = &task.image_style {
            match style.to_lowercase().as_str() {
                "nat" | "natural" => {
                    request.style(ImageStyle::Natural);
                }
                "viv" | "vivid" => {
                    request.style(ImageStyle::Vivid);
                }
                _ => bail!("Unsupported image style `{style}`"),
            };
        }

        let request = request.build()?;

        // Warn about ignored task options
        macro_rules! ignore_option {
            ($name:ident) => {
                if task.$name.is_some() {
                    tracing::warn!(
                        "Option `{}` is ignored by model `{}` for text-to-image generation",
                        stringify!($name),
                        self.name()
                    )
                }
            };
            ($($name:ident),*) => {
                $( ignore_option!($name); )*
            }
        }
        ignore_option!(
            mirostat,
            mirostat_eta,
            mirostat_tau,
            num_ctx,
            num_gqa,
            num_gpu,
            num_thread,
            repeat_last_n,
            repeat_penalty,
            temperature,
            seed,
            stop,
            max_tokens,
            tfs_z,
            top_k,
            top_p
        );

        if task.dry_run {
            return ModelOutput::empty(self);
        }

        // Send the request
        let client = Self::client()?;
        let mut response = client.images().create(request).await?;

        // Get the output
        if response.data.is_empty() {
            bail!("Response data is unexpectedly empty")
        }
        let image = response.data.remove(0);

        match image.as_ref() {
            Image::Url { url, .. } => {
                ModelOutput::from_url(self, "image/png", url.to_string()).await
            }
            _ => bail!("Unexpected image type"),
        }
    }
}

fn attachment_bytes(attachment: &InstructionAttachment) -> Result<Vec<u8>> {
    let Some(content) = attachment.file.content.as_ref() else {
        bail!(
            "Attachment `{}` does not have any inline content to upload.",
            attachment.alias
        );
    };

    if attachment
        .file
        .options
        .transfer_encoding
        .as_deref()
        .map(|encoding| encoding.eq_ignore_ascii_case("base64"))
        .unwrap_or(false)
    {
        BASE64.decode(content.as_bytes()).map_err(|error| {
            eyre!(
                "Attachment `{}` content is invalid base64: {error}",
                attachment.alias
            )
        })
    } else {
        Ok(content.as_bytes().to_vec())
    }
}

#[derive(Debug, Deserialize)]
struct UploadFileResponse {
    id: String,
}

#[derive(Debug)]
struct UploadedAttachment {
    alias: String,
    file_id: String,
    media_type: String,
}

impl UploadedAttachment {
    fn to_contents(&self) -> Vec<ResponseContent> {
        let mut contents = vec![ResponseContent::InputText {
            text: format!("Attachment `{}`", self.alias),
        }];

        if self.media_type.starts_with("image/") {
            contents.push(ResponseContent::InputImage {
                file_id: Some(self.file_id.clone()),
                image_url: None,
            });
        } else {
            contents.push(ResponseContent::InputFile {
                file_id: self.file_id.clone(),
            });
        }

        contents
    }
}

#[derive(Debug, Serialize)]
struct ResponsesRequest {
    model: String,
    input: Vec<ResponseMessage>,
    #[serde(skip_serializing_if = "Option::is_none")]
    temperature: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    top_p: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    stop: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    seed: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    max_output_tokens: Option<u16>,
}

#[derive(Debug, Serialize)]
struct ResponseMessage {
    role: String,
    content: Vec<ResponseContent>,
}

#[derive(Debug, Serialize)]
#[serde(tag = "type", rename_all = "snake_case")]
enum ResponseContent {
    InputText {
        text: String,
    },
    OutputText {
        text: String,
    },
    InputFile {
        file_id: String,
    },
    InputImage {
        #[serde(skip_serializing_if = "Option::is_none")]
        file_id: Option<String>,
        #[serde(skip_serializing_if = "Option::is_none")]
        image_url: Option<String>,
    },
}

#[derive(Debug, Deserialize)]
struct ResponsesResponse {
    output: Vec<ResponseOutput>,
}

#[derive(Debug, Deserialize)]
struct ResponseOutput {
    #[allow(unused)]
    role: Option<String>,
    content: Vec<ResponseOutputContent>,
}

#[derive(Debug, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
enum ResponseOutputContent {
    OutputText {
        text: String,
    },
    SummaryText {
        text: String,
    },
    #[serde(other)]
    Other,
}

/// Get a list of all available OpenAI models
///
/// If the OpenAI API key is not available returns an empty list.
/// Lists the models available for the account in lexical order.
///
/// This mapping of model name to context_length and input/output types will need to be
/// updated periodically based on https://platform.openai.com/docs/models/.
///
/// Memoized for two minutes to avoid loading from disk cache too frequently
/// but allowing user to set API key while process is running.
#[cached(time = 120, result = true)]
pub async fn list() -> Result<Vec<Arc<dyn Model>>> {
    // Check for API key before calling IO cached function so that we never cache an empty list
    // and allow for users to set key, and then get list, while process is running
    if secrets::env_or_get(API_KEY).is_err() {
        tracing::trace!("The environment variable or secret `{API_KEY}` is not available");
        return Ok(vec![]);
    };

    let models: Vec<Arc<dyn Model>> = list_openai_models(0)
        .await?
        .data
        .into_iter()
        .sorted_by(|a, b| a.id.cmp(&b.id))
        .filter_map(|model| {
            let name = model.id;

            // Exclude model names that are not versioned
            if name == "gpt-3.5-turbo"
                || name == "gpt-3.5-turbo-instruct"
                || name == "gpt-4"
                || name == "gpt-4-turbo"
                || name == "gpt-4o"
                || name == "gpt-4o-mini"
                || name == "o1"
                || name == "o1-mini"
                || name == "tts-1"
                || name == "tts-1-hd"
            {
                return None;
            }

            let context_length =
                if name.starts_with("gpt-4-1106") || name.starts_with("gpt-4-vision") {
                    128_000
                } else if name.contains("-32k") {
                    32_768
                } else if name.contains("-16k") || name == "gpt-3.5-turbo-1106" {
                    16_385
                } else if name.starts_with("gpt-4") {
                    8_192
                } else if name.starts_with("dall-e-2") {
                    // Note: This seems to be characters, not tokens?
                    1_000
                } else {
                    4_096
                };

            use ModelIO::*;
            let (inputs, outputs) = if name.contains("vision")
                || name.starts_with("gpt-4o")
                || name.starts_with("o1")
                || name.starts_with("gpt-5")
                || name.starts_with("gpt-4.1")
            {
                (vec![Text, Image], vec![Text])
            } else if name.starts_with("gpt-4") || name.starts_with("gpt-3.5") {
                (vec![Text], vec![Text])
            } else if name.starts_with("dall-e") {
                (vec![Text], vec![Image])
            } else if name.starts_with("tts") {
                (vec![Text], vec![Audio])
            } else if name.starts_with("whisper") {
                (vec![Audio], vec![Text])
            } else {
                // Other models are assumed to be text-text only
                (vec![Text], vec![Text])
            };

            Some(
                Arc::new(OpenAIModel::new(name, context_length, inputs, outputs)) as Arc<dyn Model>,
            )
        })
        .collect();

    Ok(models)
}

/// Fetch the list of models
///
/// In-memory cached for six hours to reduce requests to remote API.
#[cached(time = 21_600, result = true)]
async fn list_openai_models(_unused: u8) -> Result<ListModelResponse> {
    Ok(OpenAIModel::client()?.models().list().await?)
}

#[cfg(test)]
mod tests {
    use super::*;
    use model::{common::tokio, schema::File, test_task_repeat_word};

    #[tokio::test]
    async fn list_models() -> Result<()> {
        let list = list().await?;

        if secrets::env_or_get(API_KEY).is_err() {
            assert_eq!(list.len(), 0)
        } else {
            assert!(!list.is_empty())
        }

        Ok(())
    }

    #[tokio::test]
    async fn perform_task() -> Result<()> {
        if secrets::env_or_get(API_KEY).is_err() {
            return Ok(());
        }

        let list = list().await?;
        let model = list
            .iter()
            .find(|model| model.name().starts_with("GPT"))
            .expect("model should exists");
        let output = model.perform_task(&test_task_repeat_word()).await?;

        assert_eq!(output.content.trim(), "HELLO".to_string());

        Ok(())
    }

    #[tokio::test]
    async fn perform_task_with_attachment() -> Result<()> {
        if secrets::env_or_get(API_KEY).is_err() {
            return Ok(());
        }

        let list = list().await?;
        let model = match list.into_iter().find(|model| {
            let id = model.id();
            id.starts_with("openai/gpt-5")
                || id.starts_with("openai/gpt-4.1")
                || id.starts_with("openai/gpt-4o")
        }) {
            Some(model) => model,
            None => return Ok(()),
        };

        let mut task = test_task_repeat_word();
        let mut file = File::new("notes.txt".into(), "notes.txt".into());
        file.media_type = Some("text/plain".into());
        file.content = Some("These are the attached notes for the task.".into());

        task.attachments = Some(vec![InstructionAttachment {
            alias: "notes".into(),
            file,
            ..Default::default()
        }]);

        let output = model.perform_task(&task).await?;

        assert!(
            !output.content.trim().is_empty(),
            "Expected attachment-enabled response to include text output"
        );

        Ok(())
    }
}
