import React from "react";
import { CheckCircle, Clock } from "lucide-react";
import { ResultItem } from "./ResultItem";

export const ResultsLog = ({ testHistory, isRunningTest }) => {
  return (
    <div className="h-1/2 p-6 flex flex-col overflow-hidden">
      <h2 className="text-sm font-medium text-gray-400 mb-4 flex items-center gap-2">
        <CheckCircle className="w-4 h-4" /> Test Results
      </h2>

      {testHistory.length === 0 && !isRunningTest ? (
        <div className="flex-1 flex flex-col items-center justify-center text-gray-600">
          <Clock className="w-12 h-12 mb-2 opacity-20" />
          <p>No tests run yet.</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto pr-2 space-y-6">
          {testHistory.map((run) => (
            <ResultItem key={run.id} run={run} />
          ))}
        </div>
      )}
    </div>
  );
};
