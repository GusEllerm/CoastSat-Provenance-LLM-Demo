// Generated file; do not edit. See `schema-gen` crate.

use crate::prelude::*;

use super::file::File;
use super::string::String;

/// An attachment that can be provided to an instruction for model context.
#[skip_serializing_none]
#[serde_as]
#[derive(Debug, SmartDefault, Clone, PartialEq, Serialize, Deserialize, ProbeNode, StripNode, WalkNode, WriteNode, ReadNode, PatchNode, DomCodec, HtmlCodec, JatsCodec, LatexCodec, MarkdownCodec, TextCodec)]
#[serde(rename_all = "camelCase", crate = "common::serde")]
#[derive(derive_more::Display)]
#[display("InstructionAttachment")]
pub struct InstructionAttachment {
    /// The type of this item.
    pub r#type: MustBe!("InstructionAttachment"),

    /// The identifier for this item.
    #[strip(metadata)]
    #[html(attr = "id")]
    pub id: Option<String>,

    /// A short name for referring to the attachment within prompts.
    pub alias: String,

    /// The file to attach.
    #[walk]
    pub file: File,

    /// A unique identifier for a node within a document
    #[serde(skip)]
    pub uid: NodeUid
}

impl InstructionAttachment {
    const NICK: [u8; 3] = *b"iat";
    
    pub fn node_type(&self) -> NodeType {
        NodeType::InstructionAttachment
    }

    pub fn node_id(&self) -> NodeId {
        NodeId::new(&Self::NICK, &self.uid)
    }
    
    pub fn new(alias: String, file: File) -> Self {
        Self {
            alias,
            file,
            ..Default::default()
        }
    }
}
