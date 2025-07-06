import React, { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader } from "lucide-react";

/**
 * PerformanceDashboard
 * Displays real-time server and model performance metrics.
 * To be integrated into the main UI dashboard.
 */
const PerformanceDashboard = ({ serverUrl = "http://localhost:8080" }) => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch metrics from backend API (to be implemented)
  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    fetch(`${serverUrl}/api/system/optimization`)
      .then((res) => res.json())
      .then((data) => {
        if (isMounted) {
          setMetrics(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError("Failed to fetch performance metrics");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [serverUrl]);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Performance Dashboard</CardTitle>
      </CardHeader>
      <CardContent>
        {loading && (
          <div className="flex items-center gap-2 text-gray-500">
            <Loader className="h-4 w-4 animate-spin" />
            Loading metrics...
          </div>
        )}
        {error && (
          <div className="text-red-600">{error}</div>
        )}
        {metrics && (
          <div className="space-y-2">
            <div>
              <span className="font-medium">CPU Usage:</span>{" "}
              {metrics.cpu_usage != null ? `${metrics.cpu_usage}%` : "N/A"}
            </div>
            <div>
              <span className="font-medium">GPU Usage:</span>{" "}
              {metrics.gpu_usage != null ? `${metrics.gpu_usage}%` : "N/A"}
            </div>
            <div>
              <span className="font-medium">Memory Usage:</span>{" "}
              {metrics.memory_usage != null ? `${metrics.memory_usage} MB` : "N/A"}
            </div>
            <div>
              <span className="font-medium">Tokens/sec:</span>{" "}
              {metrics.tokens_per_sec != null ? metrics.tokens_per_sec : "N/A"}
            </div>
            <div>
              <span className="font-medium">Thermal State:</span>{" "}
              {metrics.thermal_state || "N/A"}
            </div>
            {/* Add more metrics as backend provides */}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default PerformanceDashboard;
