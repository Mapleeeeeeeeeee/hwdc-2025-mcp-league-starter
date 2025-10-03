"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

import type { ConversationRole } from "@/features/conversation";

type MessageContentProps = {
  content: string;
  role: ConversationRole;
};

export function MessageContent({ content, role }: MessageContentProps) {
  // User messages are plain text, assistant and system messages support markdown
  if (role === "user") {
    return <p className="whitespace-pre-wrap break-words">{content}</p>;
  }

  return (
    <div className="prose prose-invert prose-sm max-w-none break-words">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // Headings
          h1: ({ children }) => (
            <h1 className="mb-4 mt-6 text-2xl font-bold text-white">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="mb-3 mt-5 text-xl font-bold text-white">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="mb-2 mt-4 text-lg font-semibold text-white">
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 className="mb-2 mt-3 text-base font-semibold text-white/90">
              {children}
            </h4>
          ),

          // Paragraphs
          p: ({ children }) => (
            <p className="mb-3 leading-relaxed text-white/90">{children}</p>
          ),

          // Lists
          ul: ({ children }) => (
            <ul className="mb-3 ml-6 list-disc space-y-1 text-white/90">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-3 ml-6 list-decimal space-y-1 text-white/90">
              {children}
            </ol>
          ),
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,

          // Links
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-400 underline decoration-emerald-400/30 underline-offset-2 transition-colors hover:text-emerald-300 hover:decoration-emerald-300/50"
            >
              {children}
            </a>
          ),

          // Code blocks
          code: ({ className, children, ...props }) => {
            const inline = !className;
            if (inline) {
              return (
                <code
                  className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-sm text-emerald-300"
                  {...props}
                >
                  {children}
                </code>
              );
            }

            return (
              <code
                className={`${className ?? ""} block overflow-x-auto rounded-lg bg-neutral-900/80 p-4 font-mono text-sm leading-relaxed`}
                {...props}
              >
                {children}
              </code>
            );
          },

          pre: ({ children }) => (
            <pre className="mb-4 overflow-x-auto rounded-lg bg-neutral-900/80 p-0">
              {children}
            </pre>
          ),

          // Blockquotes
          blockquote: ({ children }) => (
            <blockquote className="mb-3 border-l-4 border-emerald-400/50 pl-4 italic text-white/70">
              {children}
            </blockquote>
          ),

          // Horizontal rule
          hr: () => <hr className="my-6 border-t border-white/10" />,

          // Tables
          table: ({ children }) => (
            <div className="mb-4 overflow-x-auto">
              <table className="min-w-full border-collapse border border-white/10">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-white/5">{children}</thead>
          ),
          tbody: ({ children }) => <tbody>{children}</tbody>,
          tr: ({ children }) => (
            <tr className="border-b border-white/10">{children}</tr>
          ),
          th: ({ children }) => (
            <th className="border border-white/10 px-4 py-2 text-left font-semibold text-white">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-white/10 px-4 py-2 text-white/90">
              {children}
            </td>
          ),

          // Strong and emphasis
          strong: ({ children }) => (
            <strong className="font-bold text-white">{children}</strong>
          ),
          em: ({ children }) => <em className="italic">{children}</em>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
