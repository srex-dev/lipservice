import React, { useState, useEffect } from 'react';
import { PostHog } from 'posthog-js';

interface LipServiceAppProps {
  posthog: PostHog;
}

interface CostSavingsData {
  totalLogs: number;
  sampledLogs: number;
  costSavings: number;
  savingsPercentage: number;
  patternsDetected: number;
  policyVersion: number;
}

interface SamplingPolicy {
  version: number;
  globalRate: number;
  severityRates: Record<string, number>;
  patternRates: Record<string, number>;
  anomalyBoost: number;
  reasoning: string;
  createdAt: string;
}

const LipServiceApp: React.FC<LipServiceAppProps> = ({ posthog }) => {
  const [costSavings, setCostSavings] = useState<CostSavingsData | null>(null);
  const [samplingPolicy, setSamplingPolicy] = useState<SamplingPolicy | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<any[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Get app configuration
      const config = posthog.getAppConfig();
      const lipserviceUrl = config.lipservice_url;
      const apiKey = config.api_key;
      const serviceName = config.service_name;

      if (!lipserviceUrl || !apiKey || !serviceName) {
        throw new Error('LipService configuration is incomplete');
      }

      // Fetch cost savings data
      const savingsResponse = await fetch(`${lipserviceUrl}/api/v1/services/${serviceName}/cost-savings`, {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
      });

      if (savingsResponse.ok) {
        const savingsData = await savingsResponse.json();
        setCostSavings(savingsData);
      }

      // Fetch sampling policy
      const policyResponse = await fetch(`${lipserviceUrl}/api/v1/policies/${serviceName}`, {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
      });

      if (policyResponse.ok) {
        const policyData = await policyResponse.json();
        setSamplingPolicy(policyData);
      }

      // Fetch recent logs
      const logsResponse = await fetch(`${lipserviceUrl}/api/v1/services/${serviceName}/logs`, {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
      });

      if (logsResponse.ok) {
        const logsData = await logsResponse.json();
        setLogs(logsData.logs || []);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <div>Loading LipService data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', color: '#e74c3c' }}>
        <h3>Error</h3>
        <p>{error}</p>
        <button onClick={loadData} style={{ marginTop: '10px', padding: '8px 16px' }}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ color: '#2c3e50', marginBottom: '10px' }}>
          🎙️ LipService Cost Optimizer
        </h1>
        <p style={{ color: '#7f8c8d', fontSize: '16px' }}>
          AI-powered intelligent log sampling reducing your PostHog costs by 50-80%
        </p>
      </div>

      {/* Cost Savings Overview */}
      {costSavings && (
        <div style={{ 
          backgroundColor: '#f8f9fa', 
          padding: '20px', 
          borderRadius: '8px', 
          marginBottom: '30px',
          border: '1px solid #e9ecef'
        }}>
          <h2 style={{ color: '#2c3e50', marginBottom: '20px' }}>
            💰 Cost Savings Overview
          </h2>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#27ae60' }}>
                {formatCurrency(costSavings.costSavings)}
              </div>
              <div style={{ color: '#7f8c8d' }}>Monthly Savings</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#3498db' }}>
                {costSavings.savingsPercentage.toFixed(1)}%
              </div>
              <div style={{ color: '#7f8c8d' }}>Cost Reduction</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#e74c3c' }}>
                {formatNumber(costSavings.totalLogs)}
              </div>
              <div style={{ color: '#7f8c8d' }}>Total Logs/Day</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f39c12' }}>
                {formatNumber(costSavings.sampledLogs)}
              </div>
              <div style={{ color: '#7f8c8d' }}>Sampled Logs/Day</div>
            </div>
          </div>
        </div>
      )}

      {/* Sampling Policy */}
      {samplingPolicy && (
        <div style={{ 
          backgroundColor: '#fff', 
          padding: '20px', 
          borderRadius: '8px', 
          marginBottom: '30px',
          border: '1px solid #e9ecef'
        }}>
          <h2 style={{ color: '#2c3e50', marginBottom: '20px' }}>
            🤖 AI Sampling Policy
          </h2>
          
          <div style={{ marginBottom: '15px' }}>
            <strong>Policy Version:</strong> {samplingPolicy.version}
          </div>
          
          <div style={{ marginBottom: '15px' }}>
            <strong>Global Sampling Rate:</strong> {(samplingPolicy.globalRate * 100).toFixed(1)}%
          </div>
          
          <div style={{ marginBottom: '15px' }}>
            <strong>Anomaly Boost:</strong> {samplingPolicy.anomalyBoost}x
          </div>
          
          {samplingPolicy.reasoning && (
            <div style={{ 
              backgroundColor: '#e8f4fd', 
              padding: '15px', 
              borderRadius: '4px',
              borderLeft: '4px solid #3498db'
            }}>
              <strong>AI Reasoning:</strong> {samplingPolicy.reasoning}
            </div>
          )}
          
          <div style={{ marginTop: '20px' }}>
            <h3 style={{ color: '#2c3e50', marginBottom: '10px' }}>Severity-Based Sampling</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px' }}>
              {Object.entries(samplingPolicy.severityRates).map(([severity, rate]) => (
                <div key={severity} style={{ 
                  padding: '10px', 
                  backgroundColor: '#f8f9fa', 
                  borderRadius: '4px',
                  textAlign: 'center'
                }}>
                  <div style={{ fontWeight: 'bold' }}>{severity}</div>
                  <div style={{ color: '#7f8c8d' }}>{(rate * 100).toFixed(1)}%</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Recent Logs */}
      <div style={{ 
        backgroundColor: '#fff', 
        padding: '20px', 
        borderRadius: '8px',
        border: '1px solid #e9ecef'
      }}>
        <h2 style={{ color: '#2c3e50', marginBottom: '20px' }}>
          📊 Recent Log Activity
        </h2>
        
        {logs.length > 0 ? (
          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8f9fa' }}>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #dee2e6' }}>
                    Timestamp
                  </th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #dee2e6' }}>
                    Level
                  </th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #dee2e6' }}>
                    Message
                  </th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #dee2e6' }}>
                    Sampled
                  </th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #dee2e6' }}>
                    Rate
                  </th>
                </tr>
              </thead>
              <tbody>
                {logs.slice(0, 50).map((log, index) => (
                  <tr key={index} style={{ borderBottom: '1px solid #f1f3f4' }}>
                    <td style={{ padding: '10px' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td style={{ padding: '10px' }}>
                      <span style={{
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        backgroundColor: log.level === 'ERROR' ? '#e74c3c' : 
                                        log.level === 'WARNING' ? '#f39c12' : 
                                        log.level === 'INFO' ? '#3498db' : '#95a5a6',
                        color: 'white'
                      }}>
                        {log.level}
                      </span>
                    </td>
                    <td style={{ padding: '10px', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {log.message}
                    </td>
                    <td style={{ padding: '10px' }}>
                      <span style={{
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        backgroundColor: log.sampled ? '#27ae60' : '#95a5a6',
                        color: 'white'
                      }}>
                        {log.sampled ? 'YES' : 'NO'}
                      </span>
                    </td>
                    <td style={{ padding: '10px' }}>
                      {(log.sampling_rate * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', color: '#7f8c8d', padding: '40px' }}>
            No recent logs found. Start logging to see activity here.
          </div>
        )}
      </div>

      {/* Integration Instructions */}
      <div style={{ 
        backgroundColor: '#e8f5e8', 
        padding: '20px', 
        borderRadius: '8px', 
        marginTop: '30px',
        border: '1px solid #c3e6c3'
      }}>
        <h2 style={{ color: '#2c3e50', marginBottom: '15px' }}>
          🚀 Get Started with LipService
        </h2>
        
        <div style={{ marginBottom: '15px' }}>
          <strong>1. Install LipService SDK:</strong>
        </div>
        <div style={{ 
          backgroundColor: '#2c3e50', 
          color: 'white', 
          padding: '10px', 
          borderRadius: '4px',
          fontFamily: 'monospace',
          marginBottom: '15px'
        }}>
          npm install @lipservice/sdk
        </div>
        
        <div style={{ marginBottom: '15px' }}>
          <strong>2. Configure with PostHog:</strong>
        </div>
        <div style={{ 
          backgroundColor: '#2c3e50', 
          color: 'white', 
          padding: '10px', 
          borderRadius: '4px',
          fontFamily: 'monospace',
          marginBottom: '15px',
          fontSize: '12px',
          overflow: 'auto'
        }}>
{`import { configureAdaptiveLogging, getLogger } from '@lipservice/sdk';

await configureAdaptiveLogging({
  serviceName: 'my-api',
  lipserviceUrl: 'https://lipservice.company.com',
  posthogApiKey: 'phc_xxx',
  posthogTeamId: '12345',
});

const logger = getLogger('my-module');
await logger.info('user_login', { user_id: 123 });`}
        </div>
        
        <div style={{ color: '#27ae60', fontWeight: 'bold' }}>
          ✅ That's it! Your logs are now intelligently sampled and sent to PostHog.
        </div>
      </div>
    </div>
  );
};

export default LipServiceApp;
