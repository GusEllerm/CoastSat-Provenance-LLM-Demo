// Generated file; do not edit. See https://github.com/stencila/stencila/tree/main/rust/schema-gen

import { Entity } from "./Entity.js";
import { File } from "./File.js";

/**
 * An attachment that can be provided to an instruction for model context.
 */
export class InstructionAttachment extends Entity {
  // @ts-expect-error 'not assignable to the same property in base type'
  type: "InstructionAttachment";

  /**
   * A short name for referring to the attachment within prompts.
   */
  alias: string;

  /**
   * The file to attach.
   */
  file: File;

  constructor(alias: string, file: File, options?: Partial<InstructionAttachment>) {
    super();
    this.type = "InstructionAttachment";
    if (options) Object.assign(this, options);
    this.alias = alias;
    this.file = file;
  }
}

/**
* Create a new `InstructionAttachment`
*/
export function instructionAttachment(alias: string, file: File, options?: Partial<InstructionAttachment>): InstructionAttachment {
  return new InstructionAttachment(alias, file, options);
}
