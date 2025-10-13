/**
 * Enhance user message with tool usage hints
 * @param originalMessage - The user's original message
 * @param selectedTools - Array of selected tool keys
 * @returns Enhanced message with tool hints
 */
export function enhanceMessageWithToolHints(
  originalMessage: string,
  selectedTools: string[],
): string {
  if (selectedTools.length === 0) {
    return originalMessage;
  }

  const toolNames = selectedTools
    .map((key) => key.replace(/_/g, " "))
    .join(", ");
  const hint = `\n\nPlease use ${toolNames} to help answer this question.`;

  return originalMessage + hint;
}
