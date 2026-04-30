"use client";
import { AgentStep } from "@/lib/api";

type Props = { steps: AgentStep[] };

export function AgentTrace({ steps }: Props) {
  if (steps.length === 0) return null;

  return (
    <div className="mb-2 rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm">
      <p className="mb-2 font-semibold text-gray-500 text-xs uppercase tracking-wide">Agent Reasoning</p>
      <div className="space-y-2">
        {steps.map((step, i) => {
          if (step.type === "tool_call") {
            return (
              <div key={i} className="flex items-start gap-2">
                <span className="mt-0.5 text-blue-500">⚙</span>
                <div>
                  <span className="font-medium text-blue-700">Calling: {step.tool}</span>
                  <div className="text-gray-500 text-xs mt-0.5">
                    {Object.entries(step.args).map(([k, v]) => (
                      <span key={k}>{k}: "{v}" </span>
                    ))}
                  </div>
                </div>
              </div>
            );
          }
          if (step.type === "tool_result") {
            return (
              <div key={i} className="flex items-start gap-2">
                <span className="mt-0.5 text-green-500">✓</span>
                <div>
                  <span className="font-medium text-green-700">Result from: {step.tool}</span>
                  <p className="text-gray-500 text-xs mt-0.5 line-clamp-2">{step.content}</p>
                </div>
              </div>
            );
          }
          return null;
        })}
      </div>
    </div>
  );
}
