import { useState, useEffect } from 'react';
import { dashboardAPI } from '../services/api';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  IndianRupee,
  AlertTriangle,
  Lightbulb,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import { format } from 'date-fns';
import { Link } from 'react-router-dom';

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await dashboardAPI.getDashboard();
      setData(response.data);
      setError('');
    } catch (err) {
      setError('Failed to load dashboard data');
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

  if (error || !data) {
    return (
      <div className="card text-center py-12">
        <p className="text-red-600">{error || 'No data available'}</p>
      </div>
    );
  }

  const getHealthScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <div className="space-y-6">
      {/* Hero Header */}
      <div className="glass-card">
        <div className="section-title">
          <div>
            <p className="pill-soft">Live finances</p>
            <h1 className="text-3xl font-extrabold mt-2 text-ink">Dashboard</h1>
            <p className="muted mt-1">Bold, honest money overview powered by your real data.</p>
          </div>
          <Link to="/transactions" className="btn-primary inline-flex items-center">
            Add Transaction
            <ArrowUpRight className="ml-2 w-4 h-4" />
          </Link>
        </div>

        <div className="divider" />

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">

          <div className="card bg-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="muted">Monthly Income</p>
                <p className="text-3xl font-bold text-ink mt-1">
                  ₹{data.income?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) || 0}
                </p>
              </div>
              <div className="p-3 bg-primary-100 rounded-brutal border-2 border-ink shadow-brutal-sm">
                <TrendingUp className="w-6 h-6 text-primary-700" />
              </div>
            </div>
          </div>

          <div className="card bg-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="muted">Total Expenses</p>
                <p className="text-3xl font-bold text-red-600 mt-1">
                  ₹{data.expenses?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) || 0}
                </p>
              </div>
              <div className="p-3 bg-accent-pink/30 rounded-brutal border-2 border-ink shadow-brutal-sm">
                <TrendingDown className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </div>

          <div className="card bg-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="muted">Savings</p>
                <p className={`text-3xl font-bold ${data.savings >= 0 ? 'text-green-600' : 'text-red-600'} mt-1`}>
                  ₹{Math.abs(data.savings || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </p>
                <p className="text-xs text-ink/70 mt-1">
                  {data.savings_percentage?.toFixed(1) || 0}% of income
                </p>
              </div>
              <div className={`p-3 rounded-brutal border-2 border-ink shadow-brutal-sm ${data.savings >= 0 ? 'bg-green-100' : 'bg-red-50'}`}>
                <IndianRupee className={`w-6 h-6 ${data.savings >= 0 ? 'text-green-700' : 'text-red-600'}`} />
              </div>

            </div>
          </div>

          <div className="card bg-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="muted">Health Score</p>
                <p className={`text-3xl font-bold ${getHealthScoreColor(data.health_score || 0).split(' ')[0]} mt-1`}>
                  {data.health_score || 0}/100
                </p>
              </div>
              <div className={`p-3 rounded-brutal border-2 border-ink shadow-brutal-sm ${data.savings >= 0 ? 'bg-green-100' : 'bg-red-50'}`}>
                <IndianRupee className={`w-6 h-6 ${data.savings >= 0 ? 'text-green-700' : 'text-red-600'}`} />
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Top Categories & Recent Transactions */}
      <div className="section-grid">
        {/* Top Categories */}
        <div className="card">
          <div className="section-title">
            <h2 className="text-lg font-bold text-ink">Top Categories</h2>
            <span className="badge-outline">Where money is loudest</span>
          </div>
          {data.top_categories && data.top_categories.length > 0 ? (
            <div className="space-y-4">
              {data.top_categories.map((category, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-semibold text-ink">{category.name}</span>
                      <span className="text-sm font-bold text-ink">
                        ₹{category.amount.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                      </span>
                    </div>
                    <div className="w-full bg-ink/10 rounded-full h-2">
                      <div
                        className="bg-primary-500 h-2 rounded-full"
                        style={{
                          width: `${(category.amount / data.expenses) * 100}%`,
                          maxWidth: '100%',
                        }}
                      ></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-ink/60 text-center py-4">No categories yet</p>
          )}
        </div>

        {/* Recent Transactions */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="muted">Latest activity</p>
              <h2 className="text-lg font-bold text-ink">Recent Transactions</h2>
            </div>
            <Link to="/transactions" className="text-sm font-semibold text-primary-700 hover:text-primary-800 underline">
              View all
            </Link>
          </div>
          {data.recent_transactions && data.recent_transactions.length > 0 ? (
            <div className="space-y-3">
              {data.recent_transactions.map((transaction) => (
                <div
                  key={transaction._id}
                  className="flex items-center justify-between p-3 bg-paper rounded-brutal border-2 border-ink/10 hover:border-ink/40 transition-colors"
                >
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-ink">{transaction.title}</p>
                    <p className="text-xs text-ink/70">
                      {transaction.category} • {format(new Date(transaction.date), 'MMM dd, yyyy')}
                    </p>
                  </div>
                  <p className="text-sm font-bold text-ink">
                    ₹{transaction.amount.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-ink/60 text-center py-4">No transactions yet</p>
          )}
        </div>
      </div>

      {/* Alerts */}
      {data.alerts && data.alerts.length > 0 && (
        <div className="card border-2 border-yellow-400 bg-yellow-50">
          <div className="flex items-start">
            <AlertTriangle className="w-5 h-5 text-yellow-700 mt-0.5 mr-3 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-sm font-bold text-yellow-900 mb-2">Alerts</h3>
              <div className="space-y-2">
                {data.alerts.map((alert, index) => (
                  <p key={index} className="text-sm text-yellow-800">
                    {alert.message}
                  </p>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tips */}
      {data.tips && data.tips.length > 0 && (
        <div className="card bg-gradient-to-br from-primary-50 to-accent-teal/20 border-primary-200">
          <div className="flex items-start">
            <Lightbulb className="w-5 h-5 text-primary-700 mt-0.5 mr-3 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-sm font-bold text-ink mb-3">Financial Tips</h3>
              <div className="space-y-2">
                {data.tips.map((tip, index) => (
                  <p key={index} className="text-sm text-ink/80">
                    {tip}
                  </p>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;

