import React, { useState } from 'react';
import axios from 'axios';
import { Pie } from 'react-chartjs-2';
import 'chart.js/auto';
import './App.css';

const STOCKS = {
  AAPL: "Apple",
  TSLA: "Tesla",
  MSFT: "Microsoft",
  GOOG: "Google",
  AMZN: "Amazon"
};

function App() {
  const [assets, setAssets] = useState([{ symbol: '', quantity: '' }]);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState('');

  const handleAssetChange = (index, field, value) => {
    const updated = [...assets];
    updated[index][field] = value;
    setAssets(updated);
  };

  const addAssetRow = () => {
    setAssets([...assets, { symbol: '', quantity: '' }]);
  };

  const analyzePortfolio = async () => {
    try {
      setError('');
      setAnalysis(null);
      const validAssets = assets.filter(a => a.symbol && parseFloat(a.quantity) > 0);
      if (!validAssets.length) return setError("Please enter at least one valid asset.");

      const res = await axios.post('http://localhost:8000/analyze', { assets: validAssets });
      setAnalysis(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Analysis failed.");
    }
  };

  return (
    <div className="container">
      <h1 className="title">PortPuls</h1>
      <p className="subtitle">Visualize and understand your stock portfolio in real-time</p>

      {assets.map((asset, index) => (
        <div key={index} className="asset-row">
          <select
            value={asset.symbol}
            onChange={(e) => handleAssetChange(index, 'symbol', e.target.value)}
          >
            <option value="">Symbol</option>
            {Object.keys(STOCKS).map((symbol) => (
              <option key={symbol} value={symbol}>{symbol}</option>
            ))}
          </select>

          <input
            type="number"
            placeholder="Quantity"
            value={asset.quantity}
            onChange={(e) => handleAssetChange(index, 'quantity', e.target.value)}
          />
        </div>
      ))}

      <div className="buttons">
        <button onClick={addAssetRow}>Add Asset</button>
        <button onClick={analyzePortfolio}>Analyze</button>
      </div>

      {error && <p className="error">{error}</p>}

      {analysis && (
        <div className="results-grid">
          <div className="chart-container">
            <Pie
              data={{
                labels: analysis.breakdown.map(item => item.symbol),
                datasets: [{
                  data: analysis.breakdown.map(item => item.value),
                  backgroundColor: ['#4caf50', '#2196f3', '#ff9800', '#f44336', '#9c27b0'],
                }],
              }}
            />
          </div>

          <div className="insight-container">
            <h2 className="section-title">Total Value: ₹{analysis.total_value.toFixed(2)}</h2>
            <ul>
              {analysis.breakdown.map((item, idx) => (
                <li key={idx}>
                  <strong>{item.symbol}</strong>: {item.quantity} × ₹{item.price} = ₹{item.value.toFixed(2)} |
                  {` ${item.percentage.toFixed(2)}% — Risk: `}
                  <span className={`risk ${item.risk.toLowerCase()}`}>{item.risk}</span>
                </li>
              ))}
            </ul>

            {analysis.ai_insight && (
              <div className="ai-insight">
                <h3>AI Insight</h3>
                <p>{analysis.ai_insight}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
