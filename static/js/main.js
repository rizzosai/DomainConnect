async function loadLeaderboard() {
    const list = document.querySelector('.leaderboard-list');
    const loading = document.getElementById('leaderboard-loading');
    
    try {
        const res = await fetch('/api/leaderboard');
        if (!res.ok) throw new Error('Network error');
        
        const data = await res.json();
        list.innerHTML = '';
        
        if (data.leaderboard && data.leaderboard.length > 0) {
            data.leaderboard.forEach((entry, i) => {
                const crown = i === 0 ? '<span style="font-size:1.2em;">👑</span> ' : '';
                const li = document.createElement('li');
                li.innerHTML = `
                    <div>
                        ${crown}<strong>${entry.name}</strong> (@${entry.username})
                    </div>
                    <div>
                        <span style="color: #d9001f; font-weight: bold;">$${entry.earnings}/day</span>
                        <span style="color: #666; margin-left: 10px;">${entry.referrals} referrals</span>
                    </div>
                `;
                list.appendChild(li);
            });
        } else {
            list.innerHTML = '<li style="text-align: center; color: #666;">No leaderboard data yet. Be the first!</li>';
        }
        
        loading.style.display = 'none';
    } catch (e) {
        loading.textContent = 'Failed to load leaderboard.';
        console.error('Leaderboard error:', e);
    }
}

async function loadPackages() {
    const container = document.getElementById('packages-container');
    
    try {
        const res = await fetch('/api/packages');
        const data = await res.json();
        
        container.innerHTML = '';
        
        const urlParams = new URLSearchParams(window.location.search);
        const referrer = urlParams.get('ref');
        
        data.packages.forEach(pkg => {
            const card = document.createElement('div');
            card.className = 'package-card';
            card.innerHTML = `
                <h3>${pkg.name} ($${pkg.price}/day)</h3>
                <ul>
                    <li>Premium domain space rental</li>
                    <li>Subdomain access on RizzosAI.com</li>
                    <li>Affiliate link & commission system</li>
                    <li>Dashboard access</li>
                    <li>Leaderboard tracking</li>
                    <li>Email support</li>
                </ul>
                <button onclick="selectPackage('${pkg.id}', '${referrer || ''}')">
                    Select ${pkg.name}
                </button>
            `;
            container.appendChild(card);
        });
    } catch (e) {
        container.innerHTML = '<p style="color: red;">Failed to load packages. Please refresh the page.</p>';
        console.error('Packages error:', e);
    }
}

async function selectPackage(packageId, referrer) {
    try {
        const res = await fetch('/api/create-checkout-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                package_id: packageId,
                referrer: referrer
            })
        });
        
        const data = await res.json();
        
        if (data.checkout_url) {
            window.location.href = data.checkout_url;
        } else {
            alert('Error creating checkout session. Please try again.');
        }
    } catch (e) {
        alert('Error: ' + e.message);
        console.error('Checkout error:', e);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadLeaderboard();
    loadPackages();
    
    setInterval(loadLeaderboard, 60000);
});
