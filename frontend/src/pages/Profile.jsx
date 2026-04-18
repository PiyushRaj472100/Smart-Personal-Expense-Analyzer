import { useState, useEffect } from 'react';
import { profileAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { User, Save, Mail, DollarSign, Building, MapPin, Users, Heart } from 'lucide-react';

const Profile = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [profile, setProfile] = useState({
    name: '',
    email: '',
    gender: '',
    company: '',
    annual_income: '',
    family_members: 1,
    city: '',
    has_pets: false,
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await profileAPI.get();
      setProfile({
        name: response.data.name || '',
        email: response.data.email || '',
        gender: response.data.gender || '',
        company: response.data.company || '',
        annual_income: response.data.annual_income || '',
        family_members: response.data.family_members || 1,
        city: response.data.city || '',
        has_pets: response.data.has_pets || false,
      });
      setError('');
    } catch (err) {
      setError('Failed to load profile');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const updateData = {
        gender: profile.gender || null,
        company: profile.company || null,
        annual_income: profile.annual_income ? parseFloat(profile.annual_income) : null,
        family_members: profile.family_members || null,
        city: profile.city || null,
        has_pets: profile.has_pets || null,
      };

      await profileAPI.update(updateData);
      setSuccess('Profile updated successfully!');
      
      // Update user context if income changed
      if (updateData.annual_income) {
        const updatedUser = { ...user, annual_income: updateData.annual_income };
        localStorage.setItem('user', JSON.stringify(updatedUser));
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-card">
        <div className="section-title">
          <div>
            <p className="pill-soft">Account</p>
            <h1 className="text-3xl font-extrabold text-ink mt-1">Profile Settings</h1>
            <p className="muted">Keep your personal data up to date; everything syncs with the backend.</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="card border-l-4 border-red-400 bg-red-50">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}
      {success && (
        <div className="card border-l-4 border-green-400 bg-green-50">
          <p className="text-green-700 text-sm">{success}</p>
        </div>
      )}

      {/* Profile Form */}
      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Info */}
          <div>
            <h2 className="text-lg font-bold text-ink mb-4">Basic Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-ink/80 mb-2">
                  <User className="inline w-4 h-4 mr-1" />
                  Full Name
                </label>
                <input
                  type="text"
                  value={profile.name}
                  disabled
                  className="input-field bg-gray-100 cursor-not-allowed"
                />
                <p className="mt-1 text-xs text-ink/60">Name cannot be changed</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-ink/80 mb-2">
                  <Mail className="inline w-4 h-4 mr-1" />
                  Email Address
                </label>
                <input
                  type="email"
                  value={profile.email}
                  disabled
                  className="input-field bg-gray-100 cursor-not-allowed"
                />
                <p className="mt-1 text-xs text-ink/60">Email cannot be changed</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-ink/80 mb-2">
                  Gender
                </label>
                <select
                  value={profile.gender}
                  onChange={(e) => setProfile({ ...profile, gender: e.target.value })}
                  className="input-field"
                >
                  <option value="">Select</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                  <option value="prefer-not-to-say">Prefer not to say</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-ink/80 mb-2">
                  <MapPin className="inline w-4 h-4 mr-1" />
                  City
                </label>
                <input
                  type="text"
                  value={profile.city}
                  onChange={(e) => setProfile({ ...profile, city: e.target.value })}
                  className="input-field"
                  placeholder="e.g., Mumbai"
                />
              </div>
            </div>
          </div>

          {/* Financial Info */}
          <div className="border-t border-ink/10 pt-6">
            <h2 className="text-lg font-bold text-ink mb-4">Financial Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-ink/80 mb-2">
                  <DollarSign className="inline w-4 h-4 mr-1" />
                  Annual Income (₹)
                </label>
                <input
                  type="number"
                  value={profile.annual_income}
                  onChange={(e) => setProfile({ ...profile, annual_income: e.target.value })}
                  className="input-field"
                  placeholder="500000"
                  min="0"
                  step="1000"
                />
                <p className="mt-1 text-xs text-ink/60">Used for financial insights and tips</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-ink/80 mb-2">
                  <Building className="inline w-4 h-4 mr-1" />
                  Company
                </label>
                <input
                  type="text"
                  value={profile.company}
                  onChange={(e) => setProfile({ ...profile, company: e.target.value })}
                  className="input-field"
                  placeholder="e.g., Tech Corp"
                />
              </div>
            </div>
          </div>

          {/* Personal Info */}
          <div className="border-t border-ink/10 pt-6">
            <h2 className="text-lg font-bold text-ink mb-4">Personal Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-ink/80 mb-2">
                  <Users className="inline w-4 h-4 mr-1" />
                  Family Members
                </label>
                <input
                  type="number"
                  value={profile.family_members}
                  onChange={(e) => setProfile({ ...profile, family_members: parseInt(e.target.value) || 1 })}
                  className="input-field"
                  min="1"
                />
              </div>

              <div>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={profile.has_pets}
                    onChange={(e) => setProfile({ ...profile, has_pets: e.target.checked })}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <div>
                    <span className="text-sm font-semibold text-ink">
                      <Heart className="inline w-4 h-4 mr-1" />
                      Has Pets
                    </span>
                    <p className="text-xs text-ink/60">This helps us provide better insights</p>
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <div className="border-t border-ink/10 pt-6">
            <button
              type="submit"
              disabled={saving}
              className="btn-primary inline-flex items-center"
            >
              {saving ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Saving...
                </>
              ) : (
                <>
                  <Save className="mr-2 w-4 h-4" />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Profile;

