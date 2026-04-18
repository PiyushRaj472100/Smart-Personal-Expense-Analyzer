import { useState, useEffect } from 'react';
import { analyticsAPI } from '../services/api';
import { BarChart3, TrendingUp, PieChart } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';

const Analytics = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('monthly');
  const [error, setError] = useState('');

  const COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

  useEffect(() => {
    fetchAnalytics();
  }, [period]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await analyticsAPI.getAnalytics(period);
      setData(response.data);
      setError('');
    } catch (err) {
      setError('Failed to load analytics data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error || !data || data.message) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="mt-1 text-sm text-gray-600">Detailed spending insights</p>
        </div>
        <div className="card text-center py-12">
          <p className="text-gray-600">{error || data?.message || 'No analytics data available'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-card">
        <div className="section-title">
          <div>
            <p className="pill-soft">Story of your spend</p>
            <h1 className="text-3xl font-extrabold text-ink mt-1">Analytics</h1>
            <p className="muted">Clean charts powered by live transactions, no filler data.</p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <span className="badge-outline">Period: {period}</span>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="input-field w-full sm:w-auto"
            >
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </select>
          </div>
        </div>
        {data.ai_summary && (
          <>
            <div className="divider" />
            <div className="card bg-gradient-to-br from-primary-50 via-white to-accent-yellow/30 border-primary-200">
              <div className="flex items-start">
                <BarChart3 className="w-5 h-5 text-primary-700 mt-0.5 mr-3 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="text-sm font-bold text-ink mb-2">AI Analysis</h3>
                  <p className="text-sm text-ink/80">{data.ai_summary}</p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Category Analysis */}
      {data.category_analysis && data.category_analysis.length > 0 && (
        <div className="section-grid">
          {/* Category Bar Chart */}
          <div className="card">
            <div className="flex items-center mb-4">
              <BarChart3 className="w-5 h-5 text-primary-700 mr-2" />
              <h2 className="text-lg font-bold text-ink">Spending by Category</h2>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.category_analysis}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip
                  formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, 'Amount']}
                />
                <Bar dataKey="amount" fill="#f97316" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Category Pie Chart */}
          <div className="card">
            <div className="flex items-center mb-4">
              <PieChart className="w-5 h-5 text-primary-700 mr-2" />
              <h2 className="text-lg font-bold text-ink">Category Distribution</h2>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <RechartsPieChart>
                <Pie
                  data={data.category_analysis}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ category, percent }) =>
                    `${category}: ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={90}
                  fill="#8884d8"
                  dataKey="amount"
                >
                  {data.category_analysis.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, 'Amount']}
                />
              </RechartsPieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Time Trend */}
      {data.time_trend && data.time_trend.length > 0 && (
        <div className="card">
          <div className="flex items-center mb-4">
            <TrendingUp className="w-5 h-5 text-primary-700 mr-2" />
            <h2 className="text-lg font-bold text-ink">Spending Trend</h2>
          </div>
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={data.time_trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip
                formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, 'Amount']}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="amount"
                stroke="#f97316"
                strokeWidth={3}
                dot={{ fill: '#111827', r: 4 }}
                activeDot={{ r: 6, fill: '#f97316' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Source Analysis */}
      {data.source_analysis && data.source_analysis.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-bold text-ink mb-4">Spending by Payment Source</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {data.source_analysis.map((source, index) => (
              <div
                key={index}
                className="p-4 bg-paper rounded-brutal border-2 border-ink/20 shadow-brutal-sm"
              >
                <p className="text-sm text-ink/70 mb-1">{source.source}</p>
                <p className="text-xl font-extrabold text-ink">
                  ₹{source.amount.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics;

