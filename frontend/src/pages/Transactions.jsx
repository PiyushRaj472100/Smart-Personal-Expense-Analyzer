import { useState, useEffect } from 'react';
import { transactionsAPI } from '../services/api';
import { Plus, Trash2, MessageSquare, X, Check, AlertCircle, Lightbulb, RefreshCw } from 'lucide-react';
import { format } from 'date-fns';

const Transactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showSMSModal, setShowSMSModal] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    amount: '',
    date: new Date().toISOString().split('T')[0],
    category: '',
    source: 'manual',
  });
  const [smsText, setSmsText] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [categories, setCategories] = useState([]);
  const [showCategoryFeedback, setShowCategoryFeedback] = useState(null);
  const [categorySuggestions, setCategorySuggestions] = useState([]);
  const [customCategory, setCustomCategory] = useState('');
  const [showAllCategories, setShowAllCategories] = useState(false);
  const [categoriesWithUsage, setCategoriesWithUsage] = useState([]);

  useEffect(() => {
    fetchTransactions();
  }, []);

  const fetchTransactions = async () => {
    try {
      const response = await transactionsAPI.getAll();
      setTransactions(response.data.transactions || []);
      setError('');
    } catch (err) {
      setError('Failed to load transactions');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddTransaction = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      const data = {
        ...formData,
        amount: parseFloat(formData.amount),
      };

      const response = await transactionsAPI.add(data);

      // Check if categorization feedback is needed
      if (response.data.categorization_feedback) {
        setShowCategoryFeedback({
          ...response.data.categorization_feedback,
          transactionId: response.data.transaction_id,
          title: formData.title,
          currentCategory: response.data.category
        });
      }

      if (response.data.alert) {
        setSuccess(`Transaction added! ${response.data.alert}`);
      } else {
        setSuccess('Transaction added successfully!');
      }

      setFormData({
        title: '',
        amount: '',
        date: new Date().toISOString().split('T')[0],
        category: '',
        source: 'manual',
      });
      setShowAddModal(false);
      fetchTransactions();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add transaction');
    }
  };

  const handleAddFromSMS = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      const response = await transactionsAPI.addFromSMS({ message: smsText });

      if (response.data.alert) {
        setSuccess(`Transaction added from SMS! ${response.data.alert}`);
      } else {
        setSuccess('Transaction added from SMS successfully!');
      }

      setSmsText('');
      setShowSMSModal(false);
      fetchTransactions();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to parse SMS');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this transaction?')) {
      return;
    }

    try {
      await transactionsAPI.delete(id);
      setSuccess('Transaction deleted successfully!');
      fetchTransactions();
    } catch (err) {
      setError('Failed to delete transaction');
    }
  };

  const handleCategoryFeedback = async (correctCategory) => {
    try {
      await transactionsAPI.provideFeedback({
        transaction_id: showCategoryFeedback.transactionId,
        correct_category: correctCategory
      });
      setSuccess('Category feedback recorded! The system will learn from this.');
      setShowCategoryFeedback(null);
      setCustomCategory('');
      fetchTransactions();
    } catch (err) {
      setError('Failed to record feedback');
    }
  };

  const handleOtherCategorySelected = async (title) => {
    // When user selects "Other", show adaptive learning modal
    setShowCategoryFeedback({
      title: title,
      currentCategory: 'Other',
      confidence: 0.25,
      reason: 'User selected "Other" - please help us categorize this better',
      ask_user: true,
      suggestions: categoriesWithUsage.slice(0, 6).map(cat => cat.name),
      transactionId: null, // Will be set after transaction is created
      isOtherSelection: true
    });
  };

  const handleCustomCategorySubmit = async () => {
    if (!customCategory.trim()) {
      setError('Please enter a category name');
      return;
    }
    
    try {
      if (showCategoryFeedback.isOtherSelection) {
        // Create transaction first with custom category
        const data = {
          title: showCategoryFeedback.title,
          amount: 0, // User will need to update this
          date: new Date().toISOString().split('T')[0],
          category: customCategory.trim(),
          source: 'manual',
        };
        
        const response = await transactionsAPI.add(data);
        setSuccess(`Transaction created with custom category "${customCategory}"!`);
        setShowCategoryFeedback(null);
        setCustomCategory('');
        fetchCategories();
        fetchTransactions();
        // Open edit modal for amount
        setFormData({
          title: showCategoryFeedback.title,
          amount: '',
          date: new Date().toISOString().split('T')[0],
          category: customCategory.trim(),
          source: 'manual',
        });
        setShowAddModal(true);
      } else {
        // Normal feedback for existing transaction
        await transactionsAPI.provideFeedback({
          transaction_id: showCategoryFeedback.transactionId,
          correct_category: customCategory.trim()
        });
        setSuccess(`Custom category "${customCategory}" created and saved! The system will learn from this.`);
        setShowCategoryFeedback(null);
        setCustomCategory('');
        fetchCategories();
        fetchTransactions();
      }
    } catch (err) {
      setError('Failed to save custom category');
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await transactionsAPI.getCategories();
      const categoriesData = response.data.categories;
      
      // Convert to array with usage info and sort by usage frequency
      const categoriesArray = Object.entries(categoriesData).map(([name, data]) => ({
        name,
        ...data
      }));
      
      // Sort by usage count (highest first), then by name
      categoriesArray.sort((a, b) => {
        if (b.usage_count !== a.usage_count) {
          return b.usage_count - a.usage_count;
        }
        return a.name.localeCompare(b.name);
      });
      
      setCategoriesWithUsage(categoriesArray);
      setCategories(Object.keys(categoriesData));
    } catch (err) {
      console.error('Failed to fetch categories:', err);
    }
  };

  const suggestCategory = async (title) => {
    try {
      const response = await transactionsAPI.suggestCategory({ title });
      setCategorySuggestions(response.data.suggestions || []);
    } catch (err) {
      console.error('Failed to get category suggestion:', err);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);


  const sources = [
    { value: 'manual', label: 'Manual Entry' },
    { value: 'cash', label: 'Cash' },
    { value: 'upi', label: 'UPI' },
    { value: 'card', label: 'Card' },
    { value: 'netbanking', label: 'Net Banking' },
  ];

  const normalizeCategory = (value) => {
    if (value && typeof value === 'object') {
      return value.category || value.name || 'Other';
    }
    if (typeof value === 'string' && value.trim()) {
      return value.trim();
    }
    return 'Other';
  };

  const normalizeSource = (value) => {
    if (value && typeof value === 'object') {
      return value.source || value.name || 'manual';
    }
    if (typeof value === 'string' && value.trim()) {
      return value.trim();
    }
    return 'manual';
  };

  const normalizeAmount = (value) => {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  };

  const normalizeDate = (value) => {
    const date = value ? new Date(value) : new Date();
    return Number.isNaN(date.getTime()) ? new Date() : date;
  };

  return (
    <div className="space-y-6 flex-1">
      {/* Header */}
      <div className="glass-card w-full">
        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">

          <div className="w-full md:w-auto">
            <p className="pill-soft">Control every rupee</p>
            <h1 className="text-3xl font-extrabold text-ink mt-1">Transactions</h1>
            <p className="muted">Log, review, and parse SMS without touching the backend.</p>
          </div>

          <div className="w-full md:w-auto flex flex-col sm:flex-row flex-wrap gap-3">

            <button
              onClick={() => setShowSMSModal(true)}
              className="w-full sm:w-auto btn-secondary inline-flex items-center justify-center"
            >
              <MessageSquare className="mr-2 w-4 h-4" />
              Parse SMS
            </button>

            <button
              onClick={() => setShowAddModal(true)}
              className="w-full sm:w-auto btn-primary inline-flex items-center justify-center"
            >
              <Plus className="mr-2 w-4 h-4" />
              Add Transaction
            </button>

          </div>

        </div>
      </div>


      {/* Messages */}
      {error && (
        <div className="card border-2 border-red-400 bg-red-50">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}
      {success && (
        <div className="card border-2 border-green-500 bg-green-50">
          <p className="text-green-800 text-sm">{success}</p>
        </div>
      )}

      {/* Transactions List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
        </div>
      ) : transactions.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-ink/70 mb-4">No transactions yet</p>
          <button onClick={() => setShowAddModal(true)} className="btn-primary">
            Add Your First Transaction
          </button>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-ink/10">
              <thead className="bg-paper">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-bold text-ink uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-ink uppercase tracking-wider">
                    Title
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-ink uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-ink uppercase tracking-wider">
                    Source
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-ink uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-bold text-ink uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-ink/10">
                {transactions.map((transaction) => {
                  const category = normalizeCategory(transaction.category);
                  const source = normalizeSource(transaction.source);
                  const amount = normalizeAmount(transaction.amount);
                  const date = normalizeDate(transaction.date);

                  return (
                  <tr key={transaction._id} className="hover:bg-primary-50/50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-ink font-semibold">
                      {format(date, 'MMM dd, yyyy')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-ink">
                      {transaction.title}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className="badge-outline bg-accent-teal/20 border-ink">
                        {category}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-ink/80">
                      {source}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-extrabold text-ink">
                      ₹{amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleDelete(transaction._id)}
                        className="text-red-600 hover:text-red-900 p-2 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                );})}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add Transaction Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">Add Transaction</h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddTransaction} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => {
                    setFormData({ ...formData, title: e.target.value });
                    if (e.target.value.length > 2) {
                      suggestCategory(e.target.value);
                    }
                  }}
                  className="input-field"
                  required
                  placeholder="e.g., Grocery Shopping"
                />
                {categorySuggestions.length > 0 && (
                  <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-xs text-blue-700 font-medium mb-1">Suggested categories:</p>
                    <div className="flex flex-wrap gap-1">
                      {categorySuggestions.map((cat, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => setFormData({ ...formData, category: cat })}
                          className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                        >
                          {cat}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Amount (₹)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  className="input-field"
                  required
                  placeholder="0.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date
                </label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className="input-field"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category (optional - will auto-detect)
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => {
                    const selectedCategory = e.target.value;
                    setFormData({ ...formData, category: selectedCategory });
                    
                    // If user selects "Other", trigger adaptive learning
                    if (selectedCategory === 'Other' && formData.title) {
                      handleOtherCategorySelected(formData.title);
                    }
                  }}
                  className="input-field"
                >
                  <option value="">Auto-detect</option>
                  {categoriesWithUsage.slice(0, showAllCategories ? categoriesWithUsage.length : 8).map((cat) => (
                    <option key={cat.name} value={cat.name}>
                      {cat.name} {cat.usage_count > 0 && `(${cat.usage_count})`}
                    </option>
                  ))}
                  {categoriesWithUsage.length > 8 && (
                    <option value="" disabled>
                      {showAllCategories ? '--- Show Less ---' : '--- Show More ---'}
                    </option>
                  )}
                </select>
                {categoriesWithUsage.length > 8 && (
                  <button
                    type="button"
                    onClick={() => setShowAllCategories(!showAllCategories)}
                    className="text-xs text-blue-600 hover:text-blue-800 mt-1"
                  >
                    {showAllCategories ? 'Show Less Categories' : `Show ${categoriesWithUsage.length - 8} More Categories`}
                  </button>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Payment Source
                </label>
                <select
                  value={formData.source}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                  className="input-field"
                  required
                >
                  {sources.map((src) => (
                    <option key={src.value} value={src.value}>
                      {src.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary flex-1 inline-flex items-center justify-center">
                  <Check className="mr-2 w-4 h-4" />
                  Add
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* SMS Parser Modal */}
      {showSMSModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">Parse SMS Transaction</h2>
              <button
                onClick={() => setShowSMSModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddFromSMS} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  SMS Message
                </label>
                <textarea
                  value={smsText}
                  onChange={(e) => setSmsText(e.target.value)}
                  className="input-field min-h-[150px]"
                  required
                  placeholder="Paste your banking SMS here..."
                />
                <p className="mt-1 text-xs text-gray-500">
                  Example: "INR 500.00 debited at GROCERY STORE on 01-01-2024"
                </p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowSMSModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary flex-1 inline-flex items-center justify-center">
                  <MessageSquare className="mr-2 w-4 h-4" />
                  Parse & Add
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Category Feedback Modal */}
      {showCategoryFeedback && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6">
            <div className="flex items-center mb-4">
              <Lightbulb className="w-5 h-5 text-yellow-500 mr-2" />
              <h2 className="text-xl font-bold text-gray-900">
                {showCategoryFeedback.isOtherSelection ? 'Create Better Category' : 'Help Improve Categorization'}
              </h2>
            </div>
            
            <div className="mb-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                <p className="text-sm text-blue-800">
                  <span className="font-semibold">{showCategoryFeedback.title}</span> was categorized as 
                  <span className="font-semibold"> {showCategoryFeedback.currentCategory}</span> with {showCategoryFeedback.confidence * 100}% confidence.
                </p>
                <p className="text-xs text-blue-600 mt-1">{showCategoryFeedback.reason}</p>
              </div>
              
              <p className="text-sm text-gray-700 mb-3">
                Is this categorization correct? Your feedback helps the system learn!
              </p>
              
              <div className="space-y-3">
                <button
                  onClick={() => handleCategoryFeedback(showCategoryFeedback.currentCategory)}
                  className="w-full btn-primary inline-flex items-center justify-center"
                >
                  <Check className="mr-2 w-4 h-4" />
                  Yes, {showCategoryFeedback.currentCategory} is correct
                </button>
                
                <div className="grid grid-cols-2 gap-2">
                  {categories.filter(cat => cat !== showCategoryFeedback.currentCategory).slice(0, 4).map((cat) => (
                    <button
                      key={cat}
                      onClick={() => handleCategoryFeedback(cat)}
                      className="btn-secondary text-sm"
                    >
                      Change to {cat}
                    </button>
                  ))}
                </div>
                
                {/* Custom Category Input */}
                <div className="border-t pt-3">
                  <p className="text-sm font-medium text-gray-700 mb-2">Or create a custom category:</p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={customCategory}
                      onChange={(e) => setCustomCategory(e.target.value)}
                      placeholder="Enter custom category..."
                      className="flex-1 input-field text-sm"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          handleCustomCategorySubmit();
                        }
                      }}
                    />
                    <button
                      onClick={handleCustomCategorySubmit}
                      className="btn-primary text-sm px-3 py-2"
                    >
                      Create
                    </button>
                  </div>
                </div>
                
                <button
                  onClick={() => setShowCategoryFeedback(null)}
                  className="w-full text-gray-500 hover:text-gray-700 text-sm py-2"
                >
                  Skip for now
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Transactions;

