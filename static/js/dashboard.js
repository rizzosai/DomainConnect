const urlParams = new URLSearchParams(window.location.search);
const verified = urlParams.get('verified');
const savedUsername = localStorage.getItem('rizzosai_username');

if (verified === 'true') {
    const notice = document.getElementById('verification-notice');
    notice.style.display = 'block';
    setTimeout(() => {
        notice.style.display = 'none';
    }, 5000);
}

function copyAffiliateLink() {
    const linkInput = document.getElementById('affiliateLink');
    linkInput.select();
    document.execCommand('copy');
    alert('Affiliate link copied to clipboard!');
}

async function loadDashboard() {
    let username = document.getElementById('loginUsername')?.value.trim();
    
    if (!username && savedUsername) {
        username = savedUsername;
    }
    
    if (!username) {
        document.getElementById('login-prompt').style.display = 'block';
        document.getElementById('dashboard-content').style.display = 'none';
        return;
    }
    
    try {
        const res = await fetch(`/api/user/${username}`);
        const data = await res.json();
        
        if (res.ok && data.success) {
            localStorage.setItem('rizzosai_username', username);
            
            document.getElementById('login-prompt').style.display = 'none';
            document.getElementById('dashboard-content').style.display = 'block';
            
            document.getElementById('stat-username').textContent = data.user.username;
            document.getElementById('stat-tier').textContent = data.user.tier.toUpperCase();
            document.getElementById('stat-rate').textContent = `$${data.user.daily_rate}`;
            document.getElementById('stat-referrals').textContent = data.user.total_referrals;
            document.getElementById('stat-earnings').textContent = `$${data.user.total_earnings}`;
            
            document.getElementById('affiliateLink').value = data.user.affiliate_link;
            
            const referralsList = document.getElementById('referrals-list');
            if (data.user.referrals && data.user.referrals.length > 0) {
                referralsList.innerHTML = '';
                data.user.referrals.forEach(ref => {
                    const refDiv = document.createElement('div');
                    refDiv.className = 'referral-item';
                    const joinDate = new Date(ref.joined).toLocaleDateString();
                    refDiv.innerHTML = `
                        <strong>${ref.name}</strong> (@${ref.username})
                        <br>
                        <small>Joined: ${joinDate} | Tier: ${ref.tier.toUpperCase()}</small>
                    `;
                    referralsList.appendChild(refDiv);
                });
            } else {
                referralsList.innerHTML = '<p style="color: #666;">No referrals yet. Share your affiliate link to start earning!</p>';
            }
        } else {
            alert(data.error || 'Failed to load dashboard. Please check your username.');
            document.getElementById('login-prompt').style.display = 'block';
            document.getElementById('dashboard-content').style.display = 'none';
        }
    } catch (error) {
        alert('Network error. Please try again.');
        console.error('Dashboard error:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (savedUsername) {
        loadDashboard();
    } else {
        document.getElementById('login-prompt').style.display = 'block';
    }
});
